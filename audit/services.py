"""
Audit Core Services (Phase 3).
Implements:
- HMAC-SHA256 keyed cryptographic chain calculation.
- Canonical JSON serialization of audit events.
- Atomic, non-forking sequence generation with threading and database locks.
- Denylist filtering for sensitive fields in change diffs.
- Noise table deduplication and rate limiting.
- Re-entrant, fail-safe record_event() function.
- notify_owners() alert dispatcher.
- verify_chain() integrity verification engine.
"""

import hashlib
import hmac
import json
import logging
import threading
from datetime import timedelta
from typing import Dict, Any, Optional, Tuple, List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db import transaction, connection
from django.utils import timezone

from audit.context import get_audit_context
from audit.models import AuditEvent, AuditChainHead, SecurityNoise

logger = logging.getLogger('django.security')

# Process-level concurrency lock to prevent sequence race conditions inside the same process
_chain_lock = threading.Lock()

# Explicit field-name denylist applied to every changes diff
DENYLIST_FIELDS = {
    'password', 'password1', 'password2', 'old_password', 'new_password',
    'new_password1', 'new_password2', 'secret', 'otp_secret', 'token',
    'reset_token', 'session_key', 'backup_code', 'backup_codes', 'key',
    'hmac_key', 'salt', 'hash', 'entry_hash', 'prev_hash'
}

# Events that automatically trigger an Owner notification and alert=True
ALERT_EVENTS = {
    'account_locked',
    'authenticator_registered',
    'backup_code_used',
    'backup_codes_regenerated',
    'authenticator_removed',
    'two_factor_reset',
    'role_changed',
    'user_created',
    'user_deactivated',
    'chain_verification_failure',
    'burst_failed_logins',
}

# High-volume events routed to the SecurityNoise table
NOISE_EVENTS = {
    'login_failure',
    'permission_denied_403',
}

# Hourly noise threshold beyond which noise rows are suppressed
HOURLY_NOISE_CAP = 1000


def get_audit_hmac_key() -> str:
    """Retrieves the active HMAC key from settings, raising an error if missing in production."""
    key = getattr(settings, 'AUDIT_HMAC_KEY', None)
    if not key:
        if getattr(settings, 'DEBUG', False) or getattr(settings, 'IS_RUNNING_TESTS', False):
            return 'jimcan-dev-test-audit-hmac-key-only'
        raise ValueError("AUDIT_HMAC_KEY must be configured in settings.")
    return key


def sanitize_changes(changes: Any) -> Any:
    """
    Recursively scrubs denylisted fields from a dictionary, list, or primitive.
    Replaces matched sensitive keys with '[REDACTED]'.
    """
    if isinstance(changes, dict):
        cleaned = {}
        for k, v in changes.items():
            if str(k).lower().strip() in DENYLIST_FIELDS:
                cleaned[k] = '[REDACTED]'
            else:
                cleaned[k] = sanitize_changes(v)
        return cleaned
    elif isinstance(changes, (list, tuple)):
        return [sanitize_changes(item) for item in changes]
    return changes


def canonical_serialize(
    sequence: int,
    timestamp_iso: str,
    actor_username: str,
    client_ip: Optional[str],
    user_agent: str,
    event_type: str,
    target_model: str,
    target_object_id: str,
    target_label: str,
    changes: Dict[str, Any],
    request_id: str,
    alert: bool,
    prev_hash: str
) -> bytes:
    """
    Produces a deterministic canonical JSON byte string for HMAC computation.
    """
    payload = {
        'alert': bool(alert),
        'actor_username': str(actor_username or 'system'),
        'changes': sanitize_changes(changes or {}),
        'client_ip': str(client_ip or ''),
        'event_type': str(event_type),
        'prev_hash': str(prev_hash),
        'request_id': str(request_id or ''),
        'sequence': int(sequence),
        'target_label': str(target_label or ''),
        'target_model': str(target_model or ''),
        'target_object_id': str(target_object_id or ''),
        'timestamp': str(timestamp_iso),
        'user_agent': str(user_agent or ''),
    }
    return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')


def compute_entry_hash(prev_hash: str, canonical_bytes: bytes, hmac_key: str = None) -> str:
    """Computes HMAC-SHA256 hex digest over canonical serialization using AUDIT_HMAC_KEY."""
    key = (hmac_key or get_audit_hmac_key()).encode('utf-8')
    return hmac.new(key, canonical_bytes, hashlib.sha256).hexdigest()


def _record_noise_event(
    event_type: str,
    client_ip: Optional[str],
    path: str,
    username: Optional[str]
) -> Optional[SecurityNoise]:
    """
    Records or deduplicates noisy security events (failed logins, 403s).
    Deduplicates events with identical (event_type, client_ip, path) within a 60-second window.
    Applies an hourly insertion cap to protect database resources.
    """
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    # 1. Check hourly insertion cap
    recent_noise_count = SecurityNoise.objects.filter(last_seen__gte=one_hour_ago).count()
    if recent_noise_count >= HOURLY_NOISE_CAP:
        logger.warning(
            f"[SECURITY_NOISE_CAP] Hourly noise threshold reached ({HOURLY_NOISE_CAP}). "
            f"Suppressing database insertion for {event_type} from {client_ip} on {path}."
        )
        return None

    # 2. For login failures: only store username if account exists, otherwise [unknown account]
    cleaned_username = ""
    if username:
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            cleaned_username = username
        else:
            cleaned_username = "[unknown account]"

    # 3. Deduplicate within 60-second window
    one_minute_ago = now - timedelta(seconds=60)
    existing = SecurityNoise.objects.filter(
        event_type=event_type,
        client_ip=client_ip,
        path=path[:255],
        last_seen__gte=one_minute_ago
    ).first()

    if existing:
        existing.count += 1
        existing.last_seen = now
        if cleaned_username and not existing.username_attempted:
            existing.username_attempted = cleaned_username
        existing.save(update_fields=['count', 'last_seen', 'username_attempted'])
        return existing

    # 4. Create new noise entry
    return SecurityNoise.objects.create(
        event_type=event_type,
        client_ip=client_ip,
        path=(path or "")[:255],
        count=1,
        first_seen=now,
        last_seen=now,
        username_attempted=cleaned_username
    )


def record_event(
    event_type: str,
    actor=None,
    actor_username: Optional[str] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    target_model: str = "",
    target_object_id: str = "",
    target_label: str = "",
    changes: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    alert: bool = False,
    request=None,
    is_data_change: bool = False,
    attempted_username: Optional[str] = None,
    target_user=None,
    description: Optional[str] = None,
    context_override: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Optional[AuditEvent]:
    """
    Central, tamper-evident recording entry point for all system security events.
    Guarantees monotonic sequence ordering and cryptographic chaining.
    """
    # Resolve target_user convenience parameter if provided
    if target_user is not None:
        if not target_model:
            target_model = target_user.__class__.__name__
        if not target_object_id:
            target_object_id = str(getattr(target_user, 'pk', target_user))
        if not target_label:
            target_label = getattr(target_user, 'username', str(target_user))

    # Resolve description and context overrides into changes dict
    if description or context_override or kwargs:
        changes = dict(changes) if changes else {}
        if description:
            changes.setdefault('description', description)
        if context_override:
            changes.update(context_override)
        if kwargs:
            changes.update(kwargs)

    # 1. Fall back to ambient context from contextvars if not explicitly supplied
    ctx = get_audit_context()
    resolved_actor = actor if actor is not None else ctx['actor']
    resolved_username = actor_username or ctx['actor_username'] or "system"
    resolved_ip = client_ip or ctx['client_ip']
    resolved_ua = user_agent or ctx['user_agent'] or ""
    resolved_req_id = request_id or ctx['request_id'] or ""

    if request:
        if not resolved_ip:
            resolved_ip = request.META.get('REMOTE_ADDR')
        if not resolved_ua:
            resolved_ua = (request.META.get('HTTP_USER_AGENT') or "")[:255]
        if not resolved_req_id:
            resolved_req_id = getattr(request, 'request_id', "")

    # 2. Check if this is a high-volume noise event
    if event_type in NOISE_EVENTS:
        path = request.path if request else ""
        try:
            _record_noise_event(
                event_type=event_type,
                client_ip=resolved_ip,
                path=path,
                username=attempted_username or resolved_username
            )
        except Exception as e:
            logger.error(f"[AUDIT_NOISE_ERROR] Failed to record security noise: {e}")
        return None

    # 3. Determine if alert flag is active
    is_alert = alert or (event_type in ALERT_EVENTS)
    sanitized_changes_dict = sanitize_changes(changes or {})

    try:
        with _chain_lock:
            with transaction.atomic():
                # Acquire single-row head lock
                head, _ = AuditChainHead.objects.select_for_update().get_or_create(id=1)

                sequence = head.latest_sequence + 1
                prev_hash = head.latest_hash if head.latest_sequence > 0 else ('0' * 64)
                now = timezone.now()
                now_iso = now.isoformat()

                canonical_bytes = canonical_serialize(
                    sequence=sequence,
                    timestamp_iso=now_iso,
                    actor_username=resolved_username,
                    client_ip=resolved_ip,
                    user_agent=resolved_ua,
                    event_type=event_type,
                    target_model=target_model,
                    target_object_id=str(target_object_id),
                    target_label=target_label,
                    changes=sanitized_changes_dict,
                    request_id=resolved_req_id,
                    alert=is_alert,
                    prev_hash=prev_hash
                )

                entry_hash = compute_entry_hash(prev_hash, canonical_bytes)

                event = AuditEvent.objects.create(
                    sequence=sequence,
                    timestamp=now,
                    actor=resolved_actor if getattr(resolved_actor, 'is_authenticated', False) else None,
                    actor_username=resolved_username,
                    client_ip=resolved_ip,
                    user_agent=resolved_ua,
                    event_type=event_type,
                    target_model=target_model,
                    target_object_id=str(target_object_id),
                    target_label=target_label,
                    changes=sanitized_changes_dict,
                    request_id=resolved_req_id,
                    alert=is_alert,
                    prev_hash=prev_hash,
                    entry_hash=entry_hash
                )

                # Update chain head
                head.latest_sequence = sequence
                head.latest_hash = entry_hash
                head.save()

        # Emit log message
        logger.info(
            f"[AUDIT_EVENT] seq={event.sequence} event={event.event_type} "
            f"user={event.actor_username} ip={event.client_ip} alert={event.alert}"
        )

        # Dispatch Owner Alert if designated
        if is_alert:
            notify_owners(
                subject=f"Security Notice: {event.event_type.replace('_', ' ').title()}",
                event=event
            )

        return event

    except Exception as e:
        logger.error(f"[AUDIT_FAILURE] Failed to record audit event '{event_type}': {e}", exc_info=True)
        if is_data_change:
            # Data change audit write failure MUST rollback the transaction
            raise
        # For non-data-change events, log failure and do not turn logging into an outage
        return None


def notify_owners(subject: str, event: Any):
    """
    Emails all active users in the 'Owner' group.
    Never raises an exception or blocks the caller.
    Does not include any secret, token, or credential links.
    """
    try:
        User = get_user_model()
        owner_emails = list(
            User.objects.filter(groups__name='Owner', is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )

        if not owner_emails:
            logger.warning("[AUDIT_ALERT] No active Owner email addresses found to receive security alert.")
            return

        event_type = getattr(event, 'event_type', str(event))
        actor = getattr(event, 'actor_username', 'Unknown')
        ip = getattr(event, 'client_ip', 'Unknown')
        timestamp = getattr(event, 'timestamp', timezone.now())
        seq = getattr(event, 'sequence', 'N/A')

        body = (
            f"Security Notification from Jimcan Operations Dashboard\n"
            f"----------------------------------------------------\n\n"
            f"Event Type:  {event_type}\n"
            f"Sequence:    {seq}\n"
            f"Actor:       {actor}\n"
            f"Client IP:   {ip}\n"
            f"Timestamp:   {timestamp.isoformat()}\n\n"
            f"Please confirm this security or authentication change was expected.\n"
            f"If unexpected, sign in to the Operations Dashboard immediately to review user management and audit logs.\n"
        )

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@jimcanconstruction.site')

        send_mail(
            subject=f"[Jimcan Alert] {subject}",
            message=body,
            from_email=from_email,
            recipient_list=owner_emails,
            fail_silently=False
        )

    except Exception as exc:
        logger.error(f"[AUDIT_ALERT_FAILED] Failed to send owner security alert: {exc}", exc_info=True)


def verify_chain() -> Tuple[bool, str, Optional[int]]:
    """
    Recomputes the cryptographic chain across all AuditEvent rows.
    Returns:
        (is_valid, message, failure_sequence)
    """
    events = AuditEvent.objects.all().order_by('sequence')
    count = events.count()

    if count == 0:
        return True, "Audit log is empty; chain is intact.", None

    expected_sequence = 1
    previous_hash = '0' * 64
    hmac_key = get_audit_hmac_key()

    for event in events.iterator():
        # 1. Check sequence number continuity (no gaps)
        if event.sequence != expected_sequence:
            msg = (
                f"Audit sequence gap detected! Expected sequence {expected_sequence}, "
                f"found {event.sequence} (missing sequence {expected_sequence})."
            )
            return False, msg, expected_sequence

        # 2. Check prev_hash linkage
        if event.prev_hash != previous_hash:
            msg = (
                f"Prev-hash mismatch at sequence {event.sequence}. "
                f"Stored prev_hash does not match previous entry_hash."
            )
            return False, msg, event.sequence

        # 3. Recompute canonical serialization and HMAC
        canonical_bytes = canonical_serialize(
            sequence=event.sequence,
            timestamp_iso=event.timestamp.isoformat(),
            actor_username=event.actor_username,
            client_ip=event.client_ip,
            user_agent=event.user_agent,
            event_type=event.event_type,
            target_model=event.target_model,
            target_object_id=event.target_object_id,
            target_label=event.target_label,
            changes=event.changes,
            request_id=event.request_id,
            alert=event.alert,
            prev_hash=event.prev_hash
        )

        expected_entry_hash = compute_entry_hash(event.prev_hash, canonical_bytes, hmac_key)

        if event.entry_hash != expected_entry_hash:
            msg = (
                f"Tampering detected at sequence {event.sequence}! "
                f"Computed entry_hash does not match stored entry_hash."
            )
            return False, msg, event.sequence

        previous_hash = event.entry_hash
        expected_sequence += 1

    return True, f"Audit chain verified successfully ({count} events verified, 0 gaps, 0 mismatches).", None
