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
from django.http import HttpResponseNotAllowed
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
    assign_role,
    get_user_role,
)
from accounts.services import send_setup_link, sign_out_everywhere
from audit.services import record_event

User = get_user_model()


def _is_recent_auth(request, minutes: int = 10) -> bool:
    """Helper to check if request has a recent step-up re-authentication timestamp."""
    reauth_at = request.session.get('reauth_at')
    if not reauth_at:
        return False
    threshold = minutes * 60
    return (timezone.now().timestamp() - float(reauth_at)) <= threshold


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
class UserListView(View):
    """
    Renders the central user and role management roster (/settings/users/).
    Accessible exclusively to users holding the 'accounts.manage_users' permission.
    """
    template_name = 'accounts/user_list.html'

    def get(self, request):
        users = User.objects.all().order_by('username')
        user_list = []
        active_owners = 0

        for u in users:
            role = get_user_role(u) or 'No Role'
            has_mfa = user_has_device(u)
            if role == ROLE_OWNER and u.is_active:
                active_owners += 1
            user_list.append({
                'id': u.pk,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'role': role,
                'is_active': u.is_active,
                'has_mfa': has_mfa,
                'date_joined': u.date_joined,
                'last_login': u.last_login,
                'is_current_user': (u.pk == request.user.pk),
            })

        context = {
            'page_title': 'User Management & Roles',
            'users': user_list,
            'total_users': len(user_list),
            'active_owners_count': active_owners,
        }
        return render(request, self.template_name, context)


@method_decorator(permission_required('accounts.manage_users', raise_exception=True), name='dispatch')
@method_decorator(require_recent_auth(minutes=10), name='dispatch')
class UserCreateView(View):
    """
    Owner provisions a new staff account.
    Requires step-up re-authentication. Creates account with unusable password,
    assigns exactly one of the three roles, and emails a one-time activation link.
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
            user = form.save()
            role = form.cleaned_data['role']

            # Dispatch one-time setup activation link
            send_setup_link(user, request=request)

            # Record tamper-evident audit event
            record_event(
                event_type="user_created",
                actor=request.user,
                target_user=user,
                alert=False,
                request=request,
                description=(
                    f"Owner '{request.user.username}' provisioned user account '{user.username}' "
                    f"with assigned role '{role}'. One-time activation link dispatched."
                )
            )

            messages.success(
                request,
                f"User account '{user.username}' provisioned successfully with role '{role}'. "
                f"A one-time activation link has been sent to {user.email}."
            )
            return redirect('accounts:user_list')

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
        return render(request, self.template_name, {
            'form': form,
            'target_user': target_user,
            'page_title': f"Edit Account · {target_user.username}",
            'action': 'edit',
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
