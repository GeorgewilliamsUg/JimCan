"""
Accounts & Authentication Views for Jimcan Operations Dashboard.
Implements Phase 2:
- ReauthView (Step-up authentication)
- AccountSetupView (One-time token set-password setup)
- JimcanPasswordChangeView (Current password requirement + other session termination)
- JimcanLogoutView (POST-only logout enforcement)
"""

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import get_user_model
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views import View

from accounts.forms import ReauthForm
from accounts.services import sign_out_everywhere
from jimcan.security import security_event

User = get_user_model()


class ReauthView(LoginRequiredMixin, View):
    """
    Step-up re-authentication view (Phase 2 Task 9).
    Prompts the user to re-enter their current password before continuing to a sensitive action.
    """
    template_name = 'registration/reauth.html'

    def get(self, request):
        next_url = request.GET.get('next', '/')
        # If user already re-authenticated within 10 minutes, proceed immediately
        reauth_at = request.session.get('reauth_at')
        if reauth_at and (timezone.now().timestamp() - float(reauth_at) <= 600):
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard:overview')

        form = ReauthForm(user=request.user)
        return render(request, self.template_name, {'form': form, 'next': next_url})

    def post(self, request):
        next_url = request.POST.get('next') or request.GET.get('next') or '/'
        form = ReauthForm(request.user, data=request.POST)

        if form.is_valid():
            request.session['reauth_at'] = timezone.now().timestamp()
            security_event("reauthentication_success", user=request.user, request=request)
            
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard:overview')

        security_event("reauthentication_failure", user=request.user, request=request)
        return render(request, self.template_name, {'form': form, 'next': next_url})


@method_decorator(login_not_required, name='dispatch')
class AccountSetupView(View):
    """
    Handles one-time set-password link activation for new user accounts (Phase 2 Task 4).
    Validates token, ensures user is active, sets password, and signs out all stale sessions.
    """
    template_name = 'registration/account_setup.html'

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if not user or not user.is_active or not default_token_generator.check_token(user, token):
            return render(request, 'registration/setup_link_invalid.html', status=400)

        form = SetPasswordForm(user=user)
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if not user or not user.is_active or not default_token_generator.check_token(user, token):
            return render(request, 'registration/setup_link_invalid.html', status=400)

        form = SetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            sign_out_everywhere(user)
            security_event("account_setup_completed", username=user.username, request=request)
            messages.success(request, "Your password has been set successfully. You can now sign in.")
            return redirect('login')

        return render(request, self.template_name, {'form': form, 'user': user})


class JimcanPasswordChangeView(PasswordChangeView):
    """
    Password change view (Phase 2 Task 2).
    Requires current password, invalidates all other active sessions for this user,
    and logs a security event.
    """
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('dashboard:overview')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Keep current session authenticated
        update_session_auth_hash(self.request, form.user)
        # Terminate all other sessions for this user
        terminated_count = sign_out_everywhere(form.user, keep_session_key=self.request.session.session_key)
        security_event("password_changed", user=form.user, terminated_sessions=terminated_count, request=self.request)
        messages.success(self.request, "Password updated successfully. All other active sessions have been signed out.")
        return response


@method_decorator(login_not_required, name='dispatch')
class JimcanLogoutView(View):
    """
    Enforces POST-only logout (Phase 2 Task 5).
    Rejects GET requests with 405 Method Not Allowed.
    """
    def get(self, request):
        return HttpResponseNotAllowed(['POST'], "Logout must be requested via HTTP POST.")

    def post(self, request):
        if request.user.is_authenticated:
            security_event("logout", user=request.user, request=request)
            logout(request)
        messages.info(request, "You have been signed out.")
        return redirect('login')
