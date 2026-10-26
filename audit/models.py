"""
Audit Core Models (Phase 3).
Defines:
- AuditEvent: Immutable, append-only, cryptographically chained security event log.
- AuditChainHead: Single-row table used for locking and tracking chain sequence.
- SecurityNoise: High-volume noisy security records (failed logins, 403s), deduplicated and prunable.
- AuditAnchorRecord: Historical audit anchor snapshots for off-site verification.
"""

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone


class AuditEventQuerySet(models.QuerySet):
    """QuerySet that strictly prevents bulk updates and deletions."""

    def update(self, **kwargs):
        raise PermissionDenied("AuditEvent records are immutable and cannot be updated.")

    def delete(self):
        raise PermissionDenied("AuditEvent records are append-only and cannot be deleted.")


class AuditEventManager(models.Manager.from_queryset(AuditEventQuerySet)):
    """Manager for AuditEvent enforcing append-only semantics."""
    pass


class AuditEvent(models.Model):
    """
    Append-only, tamper-evident security audit event.
    Chained with HMAC-SHA256 over canonical serialization + prev_hash.
    """
    sequence = models.PositiveBigIntegerField(unique=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events'
    )
    actor_username = models.CharField(max_length=150, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    event_type = models.CharField(max_length=64, db_index=True)
    target_model = models.CharField(max_length=100, blank=True)
    target_object_id = models.CharField(max_length=100, blank=True)
    target_label = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=36, blank=True, db_index=True)
    alert = models.BooleanField(default=False, db_index=True)
    prev_hash = models.CharField(max_length=64)
    entry_hash = models.CharField(max_length=64, db_index=True)

    objects = AuditEventManager()

    class Meta:
        ordering = ['sequence']
        verbose_name = 'Audit Event'
        verbose_name_plural = 'Audit Events'
        indexes = [
            models.Index(fields=['timestamp', 'event_type']),
            models.Index(fields=['alert', 'timestamp']),
        ]

    def __str__(self):
        return f"AuditEvent #{self.sequence} [{self.event_type}] by {self.actor_username or 'system'}"

    def save(self, *args, **kwargs):
        # Disallow updates on existing records
        if self.pk is not None and not kwargs.get('force_insert', False):
            if AuditEvent.objects.filter(pk=self.pk).exists():
                raise PermissionDenied("AuditEvent records are immutable and cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("AuditEvent records are append-only and cannot be deleted.")


class AuditChainHead(models.Model):
    """
    Single-row table that anchors the chain head and sequence counter.
    Locked using select_for_update() during record_event to prevent sequence forks.
    """
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    latest_sequence = models.PositiveBigIntegerField(default=0)
    latest_hash = models.CharField(max_length=64, default='0' * 64)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Audit Chain Head'
        verbose_name_plural = 'Audit Chain Head'

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"AuditChainHead seq={self.latest_sequence} hash={self.latest_hash[:8]}..."


class SecurityNoise(models.Model):
    """
    High-volume noisy security records (failed logins, 403 permission denied).
    Deduplicated per minute and prunable after 90 days. Not chained.
    """
    event_type = models.CharField(max_length=64, db_index=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)
    username_attempted = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Security Noise'
        verbose_name_plural = 'Security Noise Records'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['event_type', 'client_ip', 'path']),
            models.Index(fields=['last_seen']),
        ]

    def __str__(self):
        return f"SecurityNoise [{self.event_type}] {self.client_ip} ({self.count}x) last: {self.last_seen}"


class AuditAnchorRecord(models.Model):
    """
    Audit anchor snapshots created for off-site weekly verification.
    """
    sequence = models.PositiveBigIntegerField()
    head_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Anchor Record'
        verbose_name_plural = 'Audit Anchor Records'

    def __str__(self):
        return f"Anchor seq={self.sequence} hash={self.head_hash[:8]} at {self.created_at}"
