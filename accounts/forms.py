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
    Form for Owner provisioning a new user account (Phase 5 Task 4).
    Enforces server-side constraints: unusable password, exactly one of the
    three approved roles, zero staff / superuser privilege.
    """
    role = forms.ChoiceField(
        choices=(),
        required=True,
        label=_("Assigned Role"),
        widget=forms.Select(attrs={'class': 'auth-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'e.g. jnamukasa'}),
            'first_name': forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'e.g. Jane'}),
            'last_name': forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'e.g. Namukasa'}),
            'email': forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'jane@jimcanconstruction.site'}),
        }

    def __init__(self, *args, **kwargs):
        from accounts.roles import ROLE_CHOICES
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = ROLE_CHOICES

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError(_("Email address is required."))
        return email

    def save(self, commit=True):
        from accounts.roles import assign_role
        user = super().save(commit=False)
        user.set_unusable_password()
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            role = self.cleaned_data.get('role')
            assign_role(user, role)
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
        from accounts.roles import ALL_ROLES, ROLE_OWNER, get_user_role
        new_role = self.cleaned_data.get('role')
        if new_role not in ALL_ROLES:
            raise forms.ValidationError(_("Invalid role selected."))

        # Protect last active Owner from demotion
        if self.instance and self.instance.pk:
            current_role = get_user_role(self.instance)
            if current_role == ROLE_OWNER and new_role != ROLE_OWNER and self.instance.is_active:
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

