"""
Signals for Accounts & Authentication Security.
Listens for Axes lockout events and emits structured security_event calls.
"""

from django.dispatch import receiver
from axes.signals import user_locked_out
from jimcan.security import security_event


@receiver(user_locked_out)
def on_user_locked_out(sender, request, username, ip_address, **kwargs):
    """
    Called whenever django-axes triggers an account lockout.
    Logs structured event to security log.
    """
    security_event(
        "account_locked",
        username=username,
        ip_address=ip_address,
        request=request,
        reason="Exceeded maximum failed login attempts"
    )
