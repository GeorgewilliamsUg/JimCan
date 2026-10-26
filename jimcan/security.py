"""
Core Security Utilities & Audit Hook for Jimcan Operations Dashboard.
Implements Phase 2: Lightweight security_event hook writing structured events to the security logger.
(Phase 3 will connect this hook to the persistent immutable AuditLog database model).
"""

import logging
from django.utils import timezone

logger = logging.getLogger('django.security')


def security_event(event_type: str, user=None, username: str = None, request=None, ip_address: str = None, **details):
    """
    Emits a structured security event.
    In Phase 2, writes to the rotating security log file.
    In Phase 3, this will also persist to the immutable audit database table.
    """
    actor_username = username
    if not actor_username and user and hasattr(user, 'get_username'):
        actor_username = user.get_username()
    elif not actor_username and request and hasattr(request, 'user') and request.user.is_authenticated:
        actor_username = request.user.get_username()
    elif not actor_username:
        actor_username = "anonymous"

    client_ip = ip_address
    if not client_ip and request:
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    elif not client_ip:
        client_ip = "unknown"

    timestamp = timezone.now().isoformat()
    extra_str = " ".join(f"{k}={v}" for k, v in details.items())

    log_entry = f"[SECURITY_EVENT] timestamp={timestamp} event={event_type} user={actor_username} ip={client_ip} {extra_str}".strip()
    logger.warning(log_entry)
