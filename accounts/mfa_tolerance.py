"""
MFA TOTP Clock Drift Tolerance Configuration.
Tolerates clock drift between server and client authenticator devices (e.g. on shared hosting like Namecheap).
Sets TOTPDeviceForm and TOTPDevice verification tolerance to settings.OTP_TOTP_TOLERANCE (default 2, +/- 60s).
"""

from django.conf import settings


def patch_totp_tolerance():
    """
    Patches django-two-factor-auth and django-otp to honor settings.OTP_TOTP_TOLERANCE.
    1. Patches TOTPDeviceForm so enrollment accepts tokens with relaxed tolerance and saves it.
    2. Patches TOTPDevice.verify_token so all token validations (login, reauth, admin) use at least target tolerance.
    """
    try:
        from two_factor.forms import TOTPDeviceForm
        from django_otp.plugins.otp_totp.models import TOTPDevice

        # 1. Patch TOTPDeviceForm
        if not getattr(TOTPDeviceForm, '_tolerance_patched', False):
            orig_init = TOTPDeviceForm.__init__

            def tolerant_init(self, key, user, metadata=None, **kwargs):
                orig_init(self, key, user, metadata=metadata, **kwargs)
                self.tolerance = getattr(settings, 'OTP_TOTP_TOLERANCE', 2)
                # Enhance token input widget attributes for styling and mobile keyboards
                self.fields['token'].widget.attrs.update({
                    'class': 'w-full text-center text-2xl font-mono tracking-widest py-3 px-4 rounded-lg border border-line bg-white focus:outline-none focus:ring-2 focus:ring-safety',
                    'placeholder': '000000',
                    'inputmode': 'numeric',
                    'pattern': '[0-9]*',
                    'autocomplete': 'one-time-code',
                })

            TOTPDeviceForm.__init__ = tolerant_init
            TOTPDeviceForm._tolerance_patched = True

        # 2. Patch TOTPDevice.verify_token
        if not getattr(TOTPDevice, '_tolerance_patched', False):
            orig_verify = TOTPDevice.verify_token

            def tolerant_verify(self, token):
                target_tolerance = getattr(settings, 'OTP_TOTP_TOLERANCE', 2)
                if self.tolerance < target_tolerance:
                    self.tolerance = target_tolerance
                return orig_verify(self, token)

            TOTPDevice.verify_token = tolerant_verify
            TOTPDevice._tolerance_patched = True

    except ImportError:
        pass
