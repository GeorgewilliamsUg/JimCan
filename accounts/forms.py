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
    Step-up re-authentication form asking only for the user's current password.
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

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Incorrect password."))
        return password
