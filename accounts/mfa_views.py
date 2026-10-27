"""
Two-Factor Authentication & Recovery Views (Phase 4).
Implements:
- JimcanTwoFactorLoginView (password + 6-digit TOTP / single-use backup code wizard).
- JimcanSetupView (authenticator registration protected by step-up re-auth).
- JimcanSetupCompleteView (presents 10 backup codes once with explicit warning).
- JimcanBackupTokensView (backup codes regeneration protected by step-up re-auth).
- JimcanProfileView (displays active device & remaining backup codes count).
- JimcanDisableView (device removal with audit logging & owner alerting).
- ResetUserMFAView (Owner-initiated reset of another user's 2FA).
"""

from urllib.parse import quote
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from django_otp import devices_for_user, user_has_device
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from two_factor.views import (
    LoginView,
    SetupView,
    SetupCompleteView,
    BackupTokensView,
    ProfileView,
    DisableView,
    QRGeneratorView,
)

from accounts.decorators import require_recent_auth
from accounts.forms import JimcanAuthenticationForm
from accounts.services import sign_out_everywhere
from audit.services import record_event
from jimcan.security import security_event

User = get_user_model()


@method_decorator(login_not_required, name='dispatch')
class JimcanTwoFactorLoginView(LoginView):
    """
    Two-step login flow: password followed by 6-digit TOTP code or static backup token.
    Normalizes standard login POST data to support both automated tests and interactive forms.
    """
    form_list = (
        (LoginView.AUTH_STEP, JimcanAuthenticationForm),
        (LoginView.TOKEN_STEP, LoginView.form_list[1][1]),
        (LoginView.BACKUP_STEP, LoginView.form_list[2][1]),
    )
    template_name = 'two_factor/core/login.html'
    redirect_authenticated_user = False

    def post(self, request, *args, **kwargs):
        prefix = self.get_prefix(request)
        current_step_key = f"{prefix}-current_step"

        # Normalize plain username/password submissions if current_step is not present
        if 'username' in request.POST and current_step_key not in request.POST:
            post_data = request.POST.copy()
            post_data[current_step_key] = self.AUTH_STEP
            post_data[f"{self.AUTH_STEP}-username"] = request.POST['username']
            post_data[f"{self.AUTH_STEP}-password"] = request.POST['password']
            request.POST = post_data

        return super().post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        response = super().done(form_list, **kwargs)
        user = self.get_user()

        # Mark recent authentication for step-up actions
        self.request.session['reauth_at'] = timezone.now().timestamp()

        # Check if login verified using a static backup code
        device = getattr(user, 'otp_device', None)
        if isinstance(device, StaticDevice):
            record_event(
                event_type="backup_code_used",
                actor=user,
                target_user=user,
                alert=True,
                request=self.request,
                description=f"User '{user.username}' signed in using a static backup code."
            )

        security_event("login_success", user=user, request=self.request)
        return response

    def render(self, form=None, **kwargs):
        # Capture login failure on invalid auth step
        if self.steps.current == self.AUTH_STEP and form and form.is_bound and not form.is_valid():
            username = form.data.get(f"{self.AUTH_STEP}-username") or form.data.get('username')
            security_event("login_failure", username=username, request=self.request)
        return super().render(form, **kwargs)


class JimcanSetupView(SetupView):
    """
    Enrolls a new TOTP authenticator device.
    Requires recent password verification (step-up) for existing enrolled users.
    Upon completion, automatically generates 10 single-use static backup codes and alerts Owners.
    """
    template_name = 'two_factor/core/setup.html'
    success_url = 'two_factor:setup_complete'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('two_factor:login')

        has_device = user_has_device(request.user)
        reauth_at = request.session.get('reauth_at')
        now_ts = timezone.now().timestamp()

        # If user already has an authenticator, re-enrolling requires step-up reauth within 10 min
        if has_device and (not reauth_at or (now_ts - float(reauth_at) > 600)):
            next_url = quote(request.get_full_path())
            return redirect(f"{reverse('accounts:reauth')}?next={next_url}")

        return super().dispatch(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        response = super().done(form_list, **kwargs)
        user = self.request.user

        # Generate 10 single-use static backup codes
        static_device, _ = user.staticdevice_set.get_or_create(name='backup')
        static_device.token_set.all().delete()
        raw_tokens = []
        for _ in range(10):
            token_val = StaticToken.random_token()
            static_device.token_set.create(token=token_val)
            raw_tokens.append(token_val)

        # Store in session to display ONCE on setup complete
        self.request.session['backup_codes_show_once'] = raw_tokens

        # Record audit event and alert all Owners
        record_event(
            event_type="authenticator_registered",
            actor=user,
            target_user=user,
            alert=True,
            request=self.request,
            description=f"User '{user.username}' enrolled a new TOTP authenticator app and generated 10 backup codes."
        )

        return response


class JimcanSetupCompleteView(SetupCompleteView):
    """
    Renders confirmation that 2FA enrollment succeeded.
    Retrieves and displays the 10 static backup codes ONCE, then clears them from session.
    """
    template_name = 'two_factor/core/setup_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pull tokens from session and delete them so they cannot be viewed again
        context['backup_codes'] = self.request.session.pop('backup_codes_show_once', None)
        context['backup_warning'] = (
            "Save them in a password manager or print them; they are the only way in if the phone is lost."
        )
        return context


class JimcanBackupTokensView(BackupTokensView):
    """
    Regenerates static backup recovery codes.
    Protected by step-up re-authentication within 10 minutes.
    Emits an audit event and alerts Owners.
    """
    template_name = 'two_factor/core/backup_tokens.html'
    success_url = 'two_factor:backup_tokens'

    @method_decorator(require_recent_auth(minutes=10))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        device = self.get_device()
        device.token_set.all().delete()
        raw_tokens = []
        for _ in range(self.number_of_tokens):
            tok = StaticToken.random_token()
            device.token_set.create(token=tok)
            raw_tokens.append(tok)

        self.request.session['backup_codes_show_once'] = raw_tokens

        # Record audit event and alert all Owners
        record_event(
            event_type="backup_codes_regenerated",
            actor=self.request.user,
            target_user=self.request.user,
            alert=True,
            request=self.request,
            description=f"User '{self.request.user.username}' regenerated static backup recovery codes."
        )

        messages.success(self.request, "10 new backup recovery codes generated. Store them safely.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['new_backup_codes'] = self.request.session.pop('backup_codes_show_once', None)
        context['backup_warning'] = (
            "Save them in a password manager or print them; they are the only way in if the phone is lost."
        )
        return context


class JimcanProfileView(ProfileView):
    """
    Displays the user's Two-Factor Authentication status and remaining backup codes count.
    """
    template_name = 'two_factor/profile/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Remaining backup tokens count
        try:
            static_dev = self.request.user.staticdevice_set.first()
            context['backup_tokens_remaining'] = static_dev.token_set.count() if static_dev else 0
        except Exception:
            context['backup_tokens_remaining'] = 0
        return context


class JimcanDisableView(DisableView):
    """
    Disables two-factor authentication for the current user.
    Protected by step-up re-authentication.
    Logs an audit event and alerts Owners.
    """
    template_name = 'two_factor/profile/disable.html'
    success_url = reverse_lazy('two_factor:profile')

    @method_decorator(require_recent_auth(minutes=10))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        for device in devices_for_user(self.request.user):
            device.delete()

        record_event(
            event_type="authenticator_removed",
            actor=self.request.user,
            target_user=self.request.user,
            alert=True,
            request=self.request,
            description=f"User '{self.request.user.username}' removed all two-factor authentication devices."
        )

        messages.warning(self.request, "Two-factor authentication has been disabled.")
        return redirect(self.success_url)


class ResetUserMFAView(View):
    """
    Allows an Owner to reset another user's two-factor device (Phase 4 Task 6).
    Enforces:
    1. Caller must belong to the 'Owner' group.
    2. Caller must have recent step-up authentication (@require_recent_auth).
    3. Caller cannot reset their own MFA through this page.
    4. Terminates all active sessions for target user (sign_out_everywhere).
    5. Writes an audit event and alerts all Owners.
    """
    @method_decorator(require_recent_auth(minutes=10))
    def post(self, request, user_id):
        if not request.user.has_perm('accounts.manage_users'):
            raise PermissionDenied("Permission 'accounts.manage_users' required to reset two-factor devices.")

        target_user = get_object_or_404(User, pk=user_id)

        # An Owner cannot reset their own two-factor through the page
        if request.user.pk == target_user.pk:
            return HttpResponseForbidden(
                "An Owner cannot reset their own two-factor device through the page. "
                "Use backup codes, ask another Owner, or run 'python manage.py reset_mfa'."
            )

        # Delete all devices for target user
        deleted_count = 0
        for device in devices_for_user(target_user):
            device.delete()
            deleted_count += 1

        # Invalidate all active sessions for target user
        sign_out_everywhere(target_user)

        # Write audit event and alert all Owners
        record_event(
            event_type="two_factor_reset",
            actor=request.user,
            target_user=target_user,
            alert=True,
            request=request,
            description=(
                f"Owner '{request.user.username}' reset two-factor authentication for user '{target_user.username}'. "
                f"Removed {deleted_count} device(s) and terminated all active sessions."
            )
        )

        messages.success(
            request,
            f"Two-factor authentication has been reset for '{target_user.username}'. "
            f"All active sessions were terminated, and the user must re-enroll upon next sign-in."
        )

        next_url = request.POST.get('next') or request.GET.get('next') or reverse('dashboard:settings')
        return redirect(next_url)
