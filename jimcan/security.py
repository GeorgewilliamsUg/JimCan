"""
Core Security Utilities & Audit Hook for Jimcan Operations Dashboard.
Connects the lightweight security_event hook directly to Phase 3's immutable
AuditEvent and SecurityNoise tables via record_event().
"""

import logging
from django.utils import timezone

logger = logging.getLogger('django.security')


def security_event(event_type: str, user=None, username: str = None, request=None, ip_address: str = None, is_data_change: bool = False, **details):
    """
    Emits a structured security event to the log file and directly persists
    to the AuditEvent / SecurityNoise database tables via record_event().
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

    # Persist directly into the Phase 3 Audit Core
    try:
        from audit.services import record_event
        record_event(
            event_type=event_type,
            actor=user,
            actor_username=actor_username if actor_username != "anonymous" else None,
            client_ip=client_ip if client_ip != "unknown" else None,
            request=request,
            changes=details,
            is_data_change=is_data_change,
            attempted_username=username
        )
    except Exception as e:
        if is_data_change:
            raise
        logger.error(f"[SECURITY_EVENT_AUDIT_ERROR] Could not record event to audit table: {e}")
