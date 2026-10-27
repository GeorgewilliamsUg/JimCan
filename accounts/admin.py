"""
Django Admin configuration for Accounts & Users (Phase 5 Task 4).
Enforces zero user deletion in Django admin: users are never deleted.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

User = get_user_model()

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class JimcanUserAdmin(DjangoUserAdmin):
    """
    Custom UserAdmin enforcing safety guardrails:
    - Zero delete permission: users are never deleted from database.
    - Removes delete_selected bulk action.
    """
    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
