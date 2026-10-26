"""
Django Admin configuration for Audit Core (Phase 3).
Enforces strictly read-only views with zero add/change/delete capabilities.
"""

from django.contrib import admin
from audit.models import AuditEvent, SecurityNoise, AuditAnchorRecord


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'timestamp', 'event_type', 'actor_username', 'client_ip', 'alert')
    list_filter = ('alert', 'event_type', 'timestamp')
    search_fields = ('actor_username', 'client_ip', 'target_label', 'request_id')
    readonly_fields = [f.name for f in AuditEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SecurityNoise)
class SecurityNoiseAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'client_ip', 'path', 'count', 'first_seen', 'last_seen', 'username_attempted')
    list_filter = ('event_type', 'last_seen')
    search_fields = ('client_ip', 'path', 'username_attempted')
    readonly_fields = [f.name for f in SecurityNoise._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditAnchorRecord)
class AuditAnchorRecordAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'head_hash', 'created_at')
    readonly_fields = [f.name for f in AuditAnchorRecord._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
