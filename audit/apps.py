import sys
from django.apps import AppConfig


_mfa_mode_recorded = False


def record_mfa_mode_on_start(sender=None, **kwargs):
    """
    Records the MFA_ENFORCEMENT mode audit event once when the application starts serving requests.
    """
    global _mfa_mode_recorded
    if _mfa_mode_recorded:
        return
    _mfa_mode_recorded = True

    from django.conf import settings
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            if 'audit_auditevent' in tables and 'audit_chain_head' in tables:
                from audit.services import record_event
                mode = getattr(settings, 'MFA_ENFORCEMENT', 'all' if not settings.DEBUG else 'off')
                record_event(
                    event_type="mfa_enforcement_mode",
                    actor=None,
                    actor_username="system",
                    description=f"Application initialized with MFA_ENFORCEMENT={mode}",
                    context_override={'mfa_enforcement': mode}
                )
    except Exception:
        pass


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Security & Audit Core'

    def ready(self):
        from django.core.signals import request_started
        request_started.connect(record_mfa_mode_on_start, dispatch_uid='audit_mfa_enforcement_mode_startup')

