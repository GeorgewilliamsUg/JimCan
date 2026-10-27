"""
One Source of Truth for Roles and Permissions (Phase 5 Task 1).
Defines the three canonical system roles: Owner, Finance, Site staff,
and exactly which permission codenames each holds, matching the approved
docs/security/permission-matrix.md adjusted by Gate 1 decisions.

Hard Rules:
1. Owners are normal accounts whose group holds explicit permissions. There are no superusers.
2. Standard Django permissions (view, add, change) cover model access. No role gets delete on a financial model.
3. Code never checks a role name or is_superuser to grant access. It checks permissions only.
"""

from typing import Dict, List, Optional
from django.contrib.auth.models import Group, User, Permission

ROLE_OWNER = 'Owner'
ROLE_FINANCE = 'Finance'
ROLE_SITE_STAFF = 'Site staff'

ALL_ROLES = (
    ROLE_OWNER,
    ROLE_FINANCE,
    ROLE_SITE_STAFF,
)

ROLE_CHOICES = [
    (ROLE_OWNER, 'Owner (Managing Director / Principal Partners)'),
    (ROLE_FINANCE, 'Finance (Accountant / Commercial Controller)'),
    (ROLE_SITE_STAFF, 'Site staff (Site Engineers / Field Supervisors)'),
]

# Explicit permission codenames granted to each role
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    ROLE_OWNER: [
        # System & Governance
        'accounts.view_financials',
        'accounts.view_tax_reports',
        'accounts.export_reports',
        'accounts.manage_users',
        'accounts.view_audit_log',
        'accounts.edit_settings',

        # Operational Sections (Full View / Add / Change, Zero Hard Delete)
        'accounts.view_overview',
        'accounts.view_leads',
        'accounts.add_leads',
        'accounts.change_leads',
        'accounts.view_projects',
        'accounts.add_projects',
        'accounts.change_projects',
        'accounts.view_rates',
        'accounts.add_rates',
        'accounts.change_rates',
        'accounts.view_invoices',
        'accounts.add_invoices',
        'accounts.change_invoices',
        'accounts.view_expenses',
        'accounts.add_expenses',
        'accounts.change_expenses',
        'accounts.view_files',
        'accounts.add_files',
        'accounts.change_files',

        # Built-in Model Permissions (Zero Delete)
        'auth.view_user',
        'auth.add_user',
        'auth.change_user',
        'auth.view_group',
        'audit.view_auditevent',
    ],

    ROLE_FINANCE: [
        # System & Governance
        'accounts.view_financials',
        'accounts.view_tax_reports',
        'accounts.export_reports',

        # Operational Sections
        'accounts.view_overview',
        'accounts.view_leads',          # Gate 1 Q2: Finance sees leads View-only
        'accounts.view_projects',       # Gate 1 Q3: Scoped viewing
        'accounts.view_rates',
        'accounts.add_rates',
        'accounts.change_rates',
        'accounts.view_invoices',
        'accounts.add_invoices',
        'accounts.change_invoices',     # Draft invoices only; issued invoices immutable
        'accounts.view_expenses',
        'accounts.add_expenses',
        'accounts.change_expenses',
        'accounts.view_files',          # View-only on field files
    ],

    ROLE_SITE_STAFF: [
        # Operational Sections (Strictly Non-Financial & Scoped)
        'accounts.view_overview',       # Non-financial dashboard feed
        'accounts.view_projects',       # Assigned builds only
        'accounts.view_rates',          # Standard rates only (no commercial margins)
        'accounts.view_expenses',       # Own expenses only
        'accounts.add_expenses',        # Submit expense vouchers (cannot edit after submit)
        'accounts.view_files',
        'accounts.add_files',           # Upload site progress photos
    ],
}


def get_role_permissions(role_name: str) -> List[str]:
    """Returns the explicit permission strings for the specified role."""
    return ROLE_PERMISSIONS.get(role_name, [])


def get_user_role(user: User) -> Optional[str]:
    """
    Returns the single active role assigned to the user, or None.
    If a user has multiple role groups (which is invalid), returns the first matching role.
    """
    if not user or not user.is_authenticated:
        return None
    for role in ALL_ROLES:
        if user.groups.filter(name=role).exists():
            return role
    return None


def assign_role(user: User, role_name: str) -> None:
    """
    Safely assigns exactly one canonical role to the given user.
    Enforces server-side guardrails:
    - Verifies role_name is valid.
    - Removes all other role groups.
    - Enforces is_superuser=False and is_staff=False.
    - Clears individual user_permissions.
    """
    if role_name not in ALL_ROLES:
        raise ValueError(f"Invalid role '{role_name}'. Must be one of {ALL_ROLES}.")

    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.set([group])
    user.is_superuser = False
    user.is_staff = False
    user.user_permissions.clear()
    user.save(update_fields=['is_superuser', 'is_staff'])
