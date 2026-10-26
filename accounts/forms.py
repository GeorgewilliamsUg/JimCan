from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm
)
from django.utils.translation import gettext_lazy as _


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
