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
from django.core.mail import send_mail, EmailMultiAlternatives
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


def generate_temporary_password(length: int = 12) -> str:
    """
    Generates a secure, cryptographically random temporary password.
    Guarantees at least 1 uppercase, 1 lowercase, 1 digit, and 1 special character.
    Total length defaults to 12.
    """
    import secrets
    import string

    if length < 8:
        length = 12

    uppercase_chars = string.ascii_uppercase
    lowercase_chars = string.ascii_lowercase
    digit_chars = string.digits
    special_chars = "!@#$%^&*()-_=+"
    all_chars = uppercase_chars + lowercase_chars + digit_chars + special_chars

    # Guarantee at least one character from each required category
    password = [
        secrets.choice(uppercase_chars),
        secrets.choice(lowercase_chars),
        secrets.choice(digit_chars),
        secrets.choice(special_chars),
    ]

    # Fill remaining characters
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Cryptographically secure shuffle
    rng = secrets.SystemRandom()
    rng.shuffle(password)
    return "".join(password)


def send_onboarding_email(user, temporary_password: str, request=None) -> tuple[bool, str | None]:
    """
    Triggers an automated HTML onboarding email containing initial temporary credentials.
    Sender address: settings.DEFAULT_FROM_EMAIL (defaults to sgeorge.ug@gmail.com).
    Subject: Your Jimcan Operations Account Credentials
    Handles SMTP failures and timeouts gracefully without crashing the transaction.
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    subject = "Your Jimcan Operations Account Credentials"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sgeorge.ug@gmail.com')
    recipient_list = [user.email]

    if not user.email:
        logger.warning(f"Onboarding email skipped: User '{user.username}' has no email address.")
        return False, "User has no email address."

    # Determine login portal URL
    if request:
        try:
            portal_url = request.build_absolute_uri(reverse('two_factor:login'))
        except Exception:
            portal_url = request.build_absolute_uri('/login/')
    else:
        domain = getattr(settings, 'ALLOWED_HOSTS', ['jimcanconstruction.site'])[0]
        if domain.startswith('.'):
            domain = domain[1:]
        scheme = 'http' if settings.DEBUG else 'https'
        portal_url = f"{scheme}://{domain}/login/"

    first_name = user.first_name or user.username
    context = {
        'first_name': first_name,
        'user_email': user.email,
        'temporary_password': temporary_password,
        'portal_url': portal_url,
    }

    try:
        html_content = render_to_string('emails/new_user_credentials.html', context)
        text_content = render_to_string('emails/new_user_credentials.txt', context)
    except Exception as exc:
        logger.error(f"Failed to render onboarding email template: {exc}")
        html_content = None
        text_content = (
            f"Hello {first_name},\n\n"
            "An administrator has provisioned your account for the Jimcan Operations Platform.\n\n"
            f"Portal URL: {portal_url}\n"
            f"Username / Email: {user.email}\n"
            f"Temporary Password: {temporary_password}\n\n"
            "You are required to change your temporary password immediately upon first login.\n\n"
            "Never share your password with anyone."
        )

    try:
        if html_content:
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
        else:
            send_mail(subject, text_content, from_email, recipient_list, fail_silently=False)
        logger.info(f"Onboarding credentials email dispatched successfully to {user.email}")
        return True, None
    except Exception as exc:
        logger.error(f"Failed to dispatch onboarding credentials email to {user.email}: {exc}")
        return False, str(exc)
