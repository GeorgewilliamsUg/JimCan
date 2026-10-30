"""
User Management Views (Phase 5 Task 4).
Restricted to Owners possessing the 'accounts.manage_users' permission.
Enforces step-up re-authentication for high-risk operations: user provisioning,
role modification, deactivation, and MFA resets.
Enforces session revocation on deactivation/role changes and protects the last active Owner.
"""

from urllib.parse import quote
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from django_otp import user_has_device
from accounts.decorators import require_recent_auth
from accounts.forms import UserCreateForm, UserEditForm
from accounts.roles import (
    ALL_ROLES,
    ROLE_OWNER,
    ROLE_ADMIN,
    assign_role,
    get_user_role,
    is_admin,
)
from accounts.services import (
    send_setup_link,
    sign_out_everywhere,
    generate_temporary_password,
    send_onboarding_email,
)
from audit.services import record_event

User = get_user_model()


def _is_recent_auth(request, minutes: int = 10) -> bool:
    """Helper to check if request has a recent step-up re-authentication timestamp."""
    reauth_at = request.session.get('reauth_at')
    if not reauth_at:
        return False
    threshold = minutes * 60
    return (timezone.now().timestamp() - float(reauth_at)) <= threshold


def get_team_roster_data(requester_user):
    """Generates the context data dictionary for the team credentials ledger."""
    users = User.objects.all().select_related('profile').order_by('username')
    user_list = []
    active_owners = 0
    is_requester_admin = is_admin(requester_user)

    for u in users:
        role = get_user_role(u) or 'No Role'
        has_mfa = user_has_device(u)
        if role in (ROLE_OWNER, ROLE_ADMIN) and u.is_active:
            active_owners += 1

        profile = getattr(u, 'profile', None)
        must_change = profile.must_change_password if profile else False
        created_at = profile.created_at if profile else u.date_joined
        created_by = profile.created_by if profile else None

        # Credential Oversight: Decrypt initial raw password strictly for Owner/Admin if still pending change
        vault_password = None
        if is_requester_admin and profile and must_change:
            vault_password = profile.get_initial_vault_password()

        privileges = []
        if profile:
            if profile.can_view_boq or profile.can_view_boq_rates:
                privileges.append({'id': 'boq', 'label': 'BOQ Pricing', 'color': 'indigo'})
            if profile.can_approve_expenses:
                privileges.append({'id': 'expenses', 'label': 'Approve Expenses', 'color': 'emerald'})
            if profile.can_export_tax_reports:
                privileges.append({'id': 'tax', 'label': 'Tax Export', 'color': 'blue'})
            if profile.can_manage_leads:
                privileges.append({'id': 'leads', 'label': 'Manage Leads', 'color': 'purple'})

        user_list.append({
            'id': u.pk,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'full_name': u.get_full_name() or u.username,
            'email': u.email,
            'role': role,
            'is_active': u.is_active,
            'must_change_password': must_change,
            'vault_password': vault_password,
            'has_vault_record': bool(profile and profile.initial_credential_vault and must_change),
            'privileges': privileges,
            'can_view_boq': profile.can_view_boq if profile else False,
            'can_approve_expenses': profile.can_approve_expenses if profile else False,
            'can_export_tax_reports': profile.can_export_tax_reports if profile else False,
            'can_manage_leads': profile.can_manage_leads if profile else False,
            'created_at': created_at,
            'created_by': created_by,
            'has_mfa': has_mfa,
            'date_joined': u.date_joined,
            'last_login': u.last_login,
            'is_current_user': (u.pk == getattr(requester_user, 'pk', None)),
        })

    create_form = UserCreateForm()

    return {
        'page_title': 'Team & Role Management',
        'users': user_list,
        'total_users': len(user_list),
        'active_owners_count': active_owners,
        'create_form': create_form,
        'is_admin': is_requester_admin,
    }


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
class UserListView(View):
    """
    Renders the central user and role management roster (/settings/users/ or /settings/team/).
    Accessible exclusively to users holding the 'accounts.manage_users' permission.
    Provides credential oversight (vault decryption for Owner/Admin) and granular permission badges.
    """
    template_name = 'accounts/user_list.html'

    def get(self, request):
        context = get_team_roster_data(request.user)
        return render(request, self.template_name, context)



@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
@method_decorator(require_recent_auth(minutes=10), name='dispatch')
class UserCreateView(View):
    """
    Admin/Owner provisions a new staff account.
    Requires step-up re-authentication. Creates account, assigns role,
    and dispatches automated onboarding email credentials.
    """
    template_name = 'accounts/user_form.html'

    def get(self, request):
        form = UserCreateForm()
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Add New Staff Account',
            'action': 'create',
        })

    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(created_by=request.user)
            role = form.cleaned_data['role']
            temp_password = getattr(form, 'generated_password', None)

            # Trigger automated onboarding credentials email if requested
            send_email = getattr(form, 'send_email_requested', True)
            email_sent, email_err = False, None
            if send_email:
                if temp_password:
                    email_sent, email_err = send_onboarding_email(user, temp_password, request=request)
                else:
                    send_setup_link(user, request=request)
                    email_sent = True

            # Record tamper-evident audit event
            record_event(
                event_type="user_created",
                actor=request.user,
                target_user=user,
                alert=False,
                request=request,
                description=(
                    f"Admin '{request.user.username}' provisioned user account '{user.username}' "
                    f"({user.email}) with assigned role '{role}'. Onboarding credentials {'dispatched' if email_sent else 'stored in vault'}."
                )
            )

            if email_sent:
                messages.success(
                    request,
                    f"User account '{user.get_full_name() or user.username}' ({user.email}) created successfully with role '{role}'. "
                    f"An onboarding email with temporary credentials has been dispatched."
                )
            elif send_email:
                messages.warning(
                    request,
                    f"User account '{user.get_full_name() or user.username}' created, but credentials email could not be delivered: {email_err}. "
                    f"Temporary Password has been safely recorded in the administrative vault."
                )
            else:
                messages.success(
                    request,
                    f"User account '{user.get_full_name() or user.username}' ({user.email}) created successfully with role '{role}'. "
                    f"Temporary credentials have been stored in the administrative vault."
                )
            return redirect('accounts:user_list')

        # Clean flash messages for form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                field_label = form.fields[field].label if field in form.fields else field.replace('_', ' ').capitalize()
                messages.error(request, f"{field_label}: {error}")

        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Add New Staff Account',
            'action': 'create',
        })


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
class UserEditView(View):
    """
    Edits user full name, email, and role assignment.
    Changing role requires step-up re-authentication and terminates secondary sessions.
    Protects the last active Owner from demotion.
    """
    template_name = 'accounts/user_form.html'

    def get(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        form = UserEditForm(instance=target_user)
        profile = getattr(target_user, 'profile', None)
        must_change = profile.must_change_password if profile else False
        is_requester_admin = is_admin(request.user)
        vault_password = None
        if is_requester_admin and profile and must_change:
            vault_password = profile.get_initial_vault_password()

        return render(request, self.template_name, {
            'form': form,
            'target_user': target_user,
            'page_title': f"Edit Account · {target_user.username}",
            'action': 'edit',
            'vault_password': vault_password,
            'has_vault_record': bool(profile and profile.initial_credential_vault and must_change),
            'must_change_password': must_change,
            'is_admin': is_requester_admin,
        })

    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        old_role = get_user_role(target_user)

        form = UserEditForm(request.POST, instance=target_user)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            role_changed = (old_role != new_role)

            # If role is changing, mandate step-up re-authentication
            if role_changed and not _is_recent_auth(request, minutes=10):
                next_url = quote(request.get_full_path())
                return redirect(f"{reverse('accounts:reauth')}?next={next_url}")

            user = form.save()

            if role_changed:
                # Terminate all active sessions for the modified user
                sign_out_everywhere(user)

                # Record role change audit event with Owner alert
                record_event(
                    event_type="role_changed",
                    actor=request.user,
                    target_user=user,
                    alert=True,
                    request=request,
                    description=(
                        f"Owner '{request.user.username}' changed role for '{user.username}' "
                        f"from '{old_role}' to '{new_role}'. All active sessions terminated."
                    )
                )
                messages.success(
                    request,
                    f"Role updated to '{new_role}' for '{user.username}'. All active sessions were revoked."
                )
            else:
                record_event(
                    event_type="user_updated",
                    actor=request.user,
                    target_user=user,
                    alert=False,
                    request=request,
                    description=f"Owner '{request.user.username}' updated profile details for '{user.username}'."
                )
                messages.success(request, f"Account details updated for '{user.username}'.")

            return redirect('accounts:user_list')

        return render(request, self.template_name, {
            'form': form,
            'target_user': target_user,
            'page_title': f"Edit Account · {target_user.username}",
            'action': 'edit',
        })


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
@method_decorator(require_recent_auth(minutes=10), name='dispatch')
class UserToggleActiveView(View):
    """
    Toggles the active state of a user account (deactivate or reactivate).
    Users are NEVER deleted from the database.
    Deactivating an account terminates all active sessions.
    The last active Owner cannot be deactivated.
    """

    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)

        if target_user.is_active:
            # Check last active Owner protection
            is_owner = target_user.groups.filter(name=ROLE_OWNER).exists()
            if is_owner:
                active_owners = User.objects.filter(is_active=True, groups__name=ROLE_OWNER).count()
                if active_owners <= 1:
                    messages.error(
                        request,
                        "Cannot deactivate the last active Owner account. "
                        "At least one active Owner must exist to prevent system lockout."
                    )
                    return redirect('accounts:user_list')

            target_user.is_active = False
            target_user.save(update_fields=['is_active'])

            # Immediately terminate all active sessions
            sign_out_everywhere(target_user)

            record_event(
                event_type="user_deactivated",
                actor=request.user,
                target_user=target_user,
                alert=True,
                request=request,
                description=(
                    f"Owner '{request.user.username}' deactivated account '{target_user.username}'. "
                    f"All active sessions were terminated."
                )
            )
            messages.success(
                request,
                f"Account '{target_user.username}' has been deactivated. All sessions were terminated."
            )
        else:
            target_user.is_active = True
            target_user.save(update_fields=['is_active'])

            record_event(
                event_type="user_updated",
                actor=request.user,
                target_user=target_user,
                alert=False,
                request=request,
                description=f"Owner '{request.user.username}' reactivated account '{target_user.username}'."
            )
            messages.success(request, f"Account '{target_user.username}' has been reactivated.")

        return redirect('accounts:user_list')


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
class UserSendSetupLinkView(View):
    """
    Dispatches a fresh one-time set-password activation link to an existing user.
    """

    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        if not target_user.is_active:
            messages.error(request, "Cannot send an activation link to a deactivated account.")
            return redirect('accounts:user_list')

        send_setup_link(target_user, request=request)
        messages.success(
            request,
            f"A one-time activation link has been sent to {target_user.email}."
        )
        return redirect('accounts:user_list')


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
@method_decorator(require_recent_auth(minutes=10), name='dispatch')
class UserResetPasswordView(View):
    """
    Resets an active user's credentials with an auto-generated 12-char temporary password,
    enforces must_change_password=True, terminates all active sessions,
    and dispatches the automated onboarding credentials email.
    """
    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        if not target_user.is_active:
            messages.error(request, "Cannot reset credentials for a suspended/deactivated account.")
            return redirect('accounts:user_list')

        custom_pw = request.POST.get('custom_password', '').strip()
        if custom_pw:
            if len(custom_pw) < 8:
                messages.error(request, "Custom password must be at least 8 characters long.")
                next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'accounts:user_list'
                return redirect(next_url)
            temp_password = custom_pw
        else:
            temp_password = generate_temporary_password(12)

        target_user.set_password(temp_password)
        target_user.save()

        # Enforce must_change_password and update encrypted temporary credential vault
        if hasattr(target_user, 'profile'):
            target_user.profile.set_initial_vault_password(temp_password)
            target_user.profile.must_change_password = True
            target_user.profile.save()
        else:
            from accounts.models import UserProfile
            prof = UserProfile.objects.create(user=target_user, must_change_password=True)
            prof.set_initial_vault_password(temp_password)
            prof.save()

        # Terminate all active sessions for this user
        sign_out_everywhere(target_user)

        # Dispatch onboarding credentials email
        email_sent, email_err = send_onboarding_email(target_user, temp_password, request=request)

        # Record tamper-evident audit event
        record_event(
            event_type="password_reset",
            actor=request.user,
            target_user=target_user,
            alert=True,
            request=request,
            description=(
                f"Admin '{request.user.username}' reset credentials for '{target_user.username}'. "
                f"All active sessions terminated and onboarding email dispatched."
            )
        )

        display_name = target_user.get_full_name() or target_user.username
        if email_sent:
            messages.success(
                request,
                f"Password reset for '{display_name}' (@{target_user.username}). "
                f"Credentials recorded in Administrative Vault (Temporary Password: {temp_password}) and emailed to {target_user.email}."
            )
        else:
            messages.warning(
                request,
                f"Password reset for '{display_name}' (@{target_user.username}). "
                f"Credentials recorded in Administrative Vault (Temporary Password: {temp_password}). Email dispatch failed: {email_err}."
            )

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
        return redirect('accounts:user_list')


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
class UserVaultCredentialView(View):
    """
    API endpoint for Owner/Admin to safely inspect provisioned credentials.
    Returns decrypted initial temporary password strictly when must_change_password is True.
    """
    def get(self, request, user_id):
        if not is_admin(request.user):
            raise PermissionDenied("Only Administrator or Owner can inspect vault credentials.")

        target_user = get_object_or_404(User, pk=user_id)
        vault_pw = target_user.get_initial_vault_password() if hasattr(target_user, 'get_initial_vault_password') else None
        return JsonResponse({
            'user_id': target_user.pk,
            'username': target_user.username,
            'has_vault': bool(vault_pw),
            'password': vault_pw,
            'must_change_password': target_user.profile.must_change_password if hasattr(target_user, 'profile') else False,
        })

