"""
Authentication & Session Services for Jimcan Operations Dashboard.
Implements Phase 2:
- sign_out_everywhere helper
- send_setup_link & generate_setup_link token helpers
"""

import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger('django.security')


def sign_out_everywhere(user, keep_session_key: str = None) -> int:
    """
    Invalidates all active database sessions for the given user.
    If keep_session_key is passed, preserves that single session (used during password change).
    Returns the count of deleted sessions.
    """
    deleted_count = 0
    user_id_str = str(user.pk)

    # Filter active/unexpired sessions
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        if keep_session_key and session.session_key == keep_session_key:
            continue
        try:
            data = session.get_decoded()
            if data.get('_auth_user_id') == user_id_str:
                session.delete()
                deleted_count += 1
        except Exception:
            # Corrupted or un-decodable session; purge it safely
            session.delete()
            deleted_count += 1

    return deleted_count


def generate_setup_link(user, request=None) -> str:
    """
    Generates a one-time set-password link valid for 1 hour (PASSWORD_RESET_TIMEOUT).
    Does not print or leak any credentials.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse('accounts:set_password', kwargs={'uidb64': uidb64, 'token': token})

    if request:
        return request.build_absolute_uri(path)

    # Fallback to configured host or staging host
    base_domain = getattr(settings, 'ALLOWED_HOSTS', ['localhost'])[0]
    if base_domain.startswith('.'):
        base_domain = base_domain[1:]
    scheme = 'https' if not settings.DEBUG else 'http'
    port = ':8000' if settings.DEBUG else ''
    return f"{scheme}://{base_domain}{port}{path}"


def send_setup_link(user, request=None) -> bool:
    """
    Sends the one-time set-password link to the user's registered email address.
    Returns True on success.
    """
    link = generate_setup_link(user, request=request)
    subject = "Activate Your Account · Jimcan Operations Portal"
    message = (
        f"Hello {user.get_full_name() or user.username},\n\n"
        "An account has been created for you on the Jimcan Operations Portal.\n"
        "Please use the link below to set your password. This link is valid for 1 hour:\n\n"
        f"{link}\n\n"
        "If you did not expect this invitation, please contact your Managing Director.\n\n"
        "— Jimcan Construction Ltd."
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jimcanconstruction.site')

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return True
