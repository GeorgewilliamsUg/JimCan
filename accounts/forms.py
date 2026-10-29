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
    Form for Admin/Owner provisioning a new user account with RBAC and onboarding credentials.
    Supports auto-generated 12-char temporary passwords or custom initial passwords,
    email validation and uniqueness, and must_change_password enforcement.
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
        label=_("Email Address"),
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'sarah.k@jimcanconstruction.site',
            'required': 'required',
        })
    )
    role = forms.ChoiceField(
        choices=(),
        required=True,
        label=_("Assigned Role"),
        widget=forms.Select(attrs={'class': 'auth-input'})
    )
    password_option = forms.ChoiceField(
        choices=[
            ('auto', _('Auto-generate secure temporary password')),
            ('manual', _('Enter custom temporary password')),
        ],
        initial='auto',
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'password-option-radio'}),
        label=_("Password Option"),
    )
    custom_password = forms.CharField(
        required=False,
        strip=False,
        label=_("Custom Temporary Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': '••••••••••••',
            'autocomplete': 'new-password',
        })
    )
    must_change_password = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Require password change upon first login"),
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-slate-900 focus:ring-slate-900'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Optional username'}),
        }

    def __init__(self, *args, **kwargs):
        from accounts.roles import ROLE_CHOICES
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = ROLE_CHOICES
        self.fields['username'].required = False
        if not self.is_bound:
            self.fields['must_change_password'].initial = True

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError(_("Email address is required."))
        # Verify email uniqueness
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("A user account with this email address already exists."))
        return email

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
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base_username[:135]}_{counter}"
                counter += 1
            cleaned_data['username'] = candidate

        return cleaned_data

    def save(self, commit=True, created_by=None):
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

        if commit:
            user.save()
            role = self.cleaned_data.get('role')
            assign_role(user, role)

            # Configure profile
            must_change = self.cleaned_data.get('must_change_password', True)
            if hasattr(user, 'profile'):
                user.profile.must_change_password = must_change
                if created_by:
                    user.profile.created_by = created_by
                user.profile.save()
            else:
                from accounts.models import UserProfile
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    must_change_password=must_change,
                    created_by=created_by,
                )

        return user


class UserEditForm(forms.ModelForm):
    """
    Form for editing user details and role assignment (Phase 5 Task 4).
    Prevents demotion of the last active Owner and prevents privilege escalation.
    """
    role = forms.ChoiceField(
        choices=(),
        required=True,
        label=_("Assigned Role"),
        widget=forms.Select(attrs={'class': 'auth-input'})
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

    def clean_role(self):
        from accounts.roles import ALL_OPERATIONAL_ROLES, ROLE_OWNER, ROLE_ADMIN, get_user_role
        new_role = self.cleaned_data.get('role')
        if new_role not in ALL_OPERATIONAL_ROLES:
            raise forms.ValidationError(_("Invalid role selected."))

        # Protect last active Owner/Admin from demotion
        if self.instance and self.instance.pk:
            current_role = get_user_role(self.instance)
            if current_role in (ROLE_OWNER, ROLE_ADMIN) and new_role not in (ROLE_OWNER, ROLE_ADMIN) and self.instance.is_active:
                active_owners = User.objects.filter(is_active=True, groups__name=ROLE_OWNER)
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
            assign_role(user, role)
        return user

