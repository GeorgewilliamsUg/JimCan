from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm
)
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class JimcanAuthenticationForm(AuthenticationForm):
    """
    Authentication form enforcing a single, uniform failure message
    to prevent username enumeration (Phase 2 Task 5).
    """
    error_messages = {
        'invalid_login': _("Incorrect username or password."),
        'inactive': _("Incorrect username or password."),
    }


class ReauthForm(forms.Form):
    """
    Step-up re-authentication form asking for current password plus
    fresh 6-digit authenticator code (or backup recovery code) if 2FA is enrolled.
    """
    password = forms.CharField(
        label=_("Current Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'autofocus': True,
            'class': 'auth-input',
            'placeholder': '••••••••••••'
        }),
    )
    otp_token = forms.CharField(
        label=_("6-Digit Code or Backup Code"),
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'one-time-code',
            'class': 'auth-input',
            'placeholder': '123456',
        }),
    )

    def __init__(self, user, request=None, *args, **kwargs):
        self.user = user
        self.request = request
        super().__init__(*args, **kwargs)
        from django_otp import user_has_device
        self.has_mfa = user_has_device(user)
        if self.has_mfa:
            self.fields['otp_token'].required = True

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Incorrect password."))
        return password

    def clean(self):
        cleaned_data = super().clean()
        if not self.has_mfa:
            return cleaned_data

        otp_token = cleaned_data.get('otp_token', '').strip()
        # If user is verified and reauth is recent, pass; otherwise require valid code
        if not otp_token:
            if not (self.request and hasattr(self.request.user, 'is_verified') and self.request.user.is_verified()):
                self.add_error('otp_token', _("Authentication code is required."))
                return cleaned_data

        if otp_token:
            from django_otp import devices_for_user
            import django_otp
            verified = False
            for device in devices_for_user(self.user):
                if device.verify_token(otp_token):
                    verified = True
                    if self.request:
                        django_otp.login(self.request, device)
                    break

            if not verified:
                self.add_error('otp_token', _("Invalid authentication code."))

        return cleaned_data


class UserCreateForm(forms.ModelForm):
    """
    Form for Admin/Owner provisioning a new user account with RBAC, granular permission
    overrides, administrative credential vault encryption, and onboarding credentials.
    Enforces username and email uniqueness across active and inactive accounts.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label=_("First Name"),
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'e.g. Sarah',
            'required': 'required',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label=_("Last Name"),
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'e.g. Kigozi',
            'required': 'required',
        })
    )
    email = forms.EmailField(
        required=True,
        label=_("Work Email Address"),
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'sarah.k@jimcanconstruction.site',
            'required': 'required',
        })
    )
    username = forms.CharField(
        max_length=150,
        required=False,
        label=_("Username"),
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'e.g. sarah_k',
        })
    )
    role = forms.ChoiceField(
        choices=(),
        required=True,
        label=_("System Role"),
        widget=forms.Select(attrs={'class': 'auth-input'})
    )
    password_option = forms.ChoiceField(
        choices=[
            ('auto', _('Auto-generate strong credentials')),
            ('manual', _('Manual Entry (Set explicit password)')),
        ],
        initial='auto',
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'password-option-radio'}),
        label=_("Password Configuration"),
    )
    custom_password = forms.CharField(
        required=False,
        strip=False,
        label=_("Custom Initial Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
        })
    )

    # Granular Feature Toggles
    can_view_boq = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Access BOQ Master Pricing (can_view_boq_rates)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    can_approve_expenses = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Permission to sign off on vouchers (can_approve_expenses)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    can_export_tax_reports = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Permission to download URA schedules (can_export_tax_reports)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    can_manage_leads = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Edit and reassign pipeline items (can_manage_leads)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )

    # Action Checkboxes
    must_change_password = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Require password change on first sign-in"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    send_onboarding_email = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Dispatch onboarding email with credentials"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')

    def __init__(self, *args, **kwargs):
        from accounts.roles import ROLE_CHOICES
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = ROLE_CHOICES
        if not self.is_bound:
            self.fields['must_change_password'].initial = True
            self.fields['send_onboarding_email'].initial = True

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError(_("Email address is required."))
        # Verify email uniqueness across all active and inactive accounts
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("A user account with this email address already exists."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username:
            # Verify username uniqueness across all active and inactive accounts
            qs = User.objects.filter(username__iexact=username)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_("A user account with this username already exists."))
        return username

    def clean_role(self):
        from accounts.roles import ALL_OPERATIONAL_ROLES
        role = self.cleaned_data.get('role')
        if role not in ALL_OPERATIONAL_ROLES:
            raise forms.ValidationError(_("Select a valid operational role."))
        return role

    def clean(self):
        cleaned_data = super().clean()
        password_option = cleaned_data.get('password_option', 'auto')
        custom_password = cleaned_data.get('custom_password')

        if password_option == 'manual':
            if not custom_password:
                self.add_error('custom_password', _("Please enter a custom temporary password."))
            elif len(custom_password) < 8:
                self.add_error('custom_password', _("Custom temporary password must be at least 8 characters long."))

        # Autogenerate username if not provided
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        if not username and email:
            base_username = email.split('@')[0].replace('+', '').replace('.', '_')
            candidate = base_username[:140]
            counter = 1
            while User.objects.filter(username__iexact=candidate).exists():
                candidate = f"{base_username[:135]}_{counter}"
                counter += 1
            cleaned_data['username'] = candidate

        return cleaned_data

    def _sync_user_permissions(self, user):
        from django.contrib.auth.models import Permission
        if not hasattr(user, 'profile'):
            return

        flag_perm_map = {
            'can_view_boq': ['view_rates'],
            'can_approve_expenses': ['change_expenses'],
            'can_export_tax_reports': ['view_tax_reports', 'export_reports'],
            'can_manage_leads': ['view_leads', 'add_leads', 'change_leads'],
        }

        for flag, codenames in flag_perm_map.items():
            if getattr(user.profile, flag, False):
                perms = Permission.objects.filter(codename__in=codenames)
                user.user_permissions.add(*perms)

    def save(self, commit=True, created_by=None):
        from accounts.models import UserProfile
        from accounts.roles import assign_role
        from accounts.services import generate_temporary_password

        user = super().save(commit=False)
        password_option = self.cleaned_data.get('password_option', 'auto')
        custom_password = self.cleaned_data.get('custom_password')

        if password_option == 'manual' and custom_password:
            temp_password = custom_password
        else:
            temp_password = generate_temporary_password(12)

        user.set_password(temp_password)
        user.is_staff = False
        user.is_superuser = False
        self.generated_password = temp_password
        self.send_email_requested = self.cleaned_data.get('send_onboarding_email', True)

        if commit:
            user.save()
            role = self.cleaned_data.get('role')

            # Configure profile
            must_change = self.cleaned_data.get('must_change_password', True)
            can_view_boq = self.cleaned_data.get('can_view_boq', False)
            can_approve_expenses = self.cleaned_data.get('can_approve_expenses', False)
            can_export_tax_reports = self.cleaned_data.get('can_export_tax_reports', False)
            can_manage_leads = self.cleaned_data.get('can_manage_leads', False)

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.must_change_password = must_change
            profile.can_view_boq = can_view_boq
            profile.can_view_boq_rates = can_view_boq
            profile.can_approve_expenses = can_approve_expenses
            profile.can_export_tax_reports = can_export_tax_reports
            profile.can_manage_leads = can_manage_leads
            if created_by:
                profile.created_by = created_by

            # Store encrypted password in administrative vault
            profile.set_initial_vault_password(temp_password)
            profile.save()

            # Attach updated profile to in-memory user instance
            user.profile = profile

            # Assign role and sync permissions
            assign_role(user, role)
            self._sync_user_permissions(user)

        return user


class UserEditForm(forms.ModelForm):
    """
    Form for editing user details, role assignment, and granular permission overrides.
    Prevents demotion of the last active Owner and prevents privilege escalation.
    """
    role = forms.ChoiceField(
        choices=(),
        required=True,
        label=_("Assigned Role"),
        widget=forms.Select(attrs={'class': 'auth-input'})
    )

    can_view_boq = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Access BOQ Master Pricing (can_view_boq_rates)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    can_approve_expenses = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Permission to sign off on vouchers (can_approve_expenses)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    can_export_tax_reports = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Permission to download URA schedules (can_export_tax_reports)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )
    can_manage_leads = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Edit and reassign pipeline items (can_manage_leads)"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'auth-input'}),
            'last_name': forms.TextInput(attrs={'class': 'auth-input'}),
            'email': forms.EmailInput(attrs={'class': 'auth-input'}),
        }

    def __init__(self, *args, **kwargs):
        from accounts.roles import ROLE_CHOICES, get_user_role
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = ROLE_CHOICES
        if self.instance and self.instance.pk:
            current_role = get_user_role(self.instance)
            if current_role:
                self.fields['role'].initial = current_role
            if hasattr(self.instance, 'profile'):
                self.fields['can_view_boq'].initial = self.instance.profile.can_view_boq
                self.fields['can_approve_expenses'].initial = self.instance.profile.can_approve_expenses
                self.fields['can_export_tax_reports'].initial = self.instance.profile.can_export_tax_reports
                self.fields['can_manage_leads'].initial = self.instance.profile.can_manage_leads

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError(_("Email address is required."))
        # Verify email uniqueness across all accounts
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("A user account with this email address already exists."))
        return email

    def clean_role(self):
        from accounts.roles import ALL_OPERATIONAL_ROLES, ROLE_OWNER, ROLE_ADMIN, get_user_role
        new_role = self.cleaned_data.get('role')
        if new_role not in ALL_OPERATIONAL_ROLES:
            raise forms.ValidationError(_("Invalid role selected."))

        # Protect last active Owner/Admin from demotion
        if self.instance and self.instance.pk:
            current_role = get_user_role(self.instance)
            if current_role in (ROLE_OWNER, ROLE_ADMIN) and new_role not in (ROLE_OWNER, ROLE_ADMIN) and self.instance.is_active:
                active_owners = User.objects.filter(is_active=True, groups__name__in=[ROLE_OWNER, ROLE_ADMIN])
                if active_owners.count() <= 1:
                    raise forms.ValidationError(_("Cannot demote the last active Owner account."))
        return new_role

    def save(self, commit=True):
        from accounts.roles import assign_role
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            role = self.cleaned_data.get('role')

            if hasattr(user, 'profile'):
                can_view_boq = self.cleaned_data.get('can_view_boq', False)
                user.profile.can_view_boq = can_view_boq
                user.profile.can_view_boq_rates = can_view_boq
                user.profile.can_approve_expenses = self.cleaned_data.get('can_approve_expenses', False)
                user.profile.can_export_tax_reports = self.cleaned_data.get('can_export_tax_reports', False)
                user.profile.can_manage_leads = self.cleaned_data.get('can_manage_leads', False)
                user.profile.save()

            assign_role(user, role)

            # Sync permissions
            from django.contrib.auth.models import Permission
            flag_perm_map = {
                'can_view_boq': ['view_rates'],
                'can_approve_expenses': ['change_expenses'],
                'can_export_tax_reports': ['view_tax_reports', 'export_reports'],
                'can_manage_leads': ['view_leads', 'add_leads', 'change_leads'],
            }
            for flag, codenames in flag_perm_map.items():
                perms = Permission.objects.filter(codename__in=codenames)
                if getattr(user.profile, flag, False):
                    user.user_permissions.add(*perms)
                else:
                    user.user_permissions.remove(*perms)

        return user

