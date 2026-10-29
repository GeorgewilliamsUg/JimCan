"""
One Source of Truth for Roles and Permissions (Phase 1 & Phase 5).
Defines operational roles:
- Admin / Owner: Full access to company settings, team management, audit logs, financials, delete operations.
- Project Manager: Read/write access to projects, BOQ, and site uploads; read-only access to client financial summaries.
- Site Engineer / Site staff: Access limited to site logs, expense submissions, and milestone tracking.
- Auditor / Accountant / Finance: Read/write access to Invoices, Expenses, Tax ledgers, and BOQ rates; no access to system administration or user provisioning.
"""

from typing import Dict, List, Optional
from django.contrib.auth.models import Group, User, Permission

ROLE_ADMIN = 'Admin'
ROLE_OWNER = 'Owner'
ROLE_PROJECT_MANAGER = 'Project Manager'
ROLE_SITE_ENGINEER = 'Site Engineer'
ROLE_SITE_STAFF = 'Site staff'
ROLE_ACCOUNTANT = 'Accountant'
ROLE_AUDITOR = 'Auditor'
ROLE_FINANCE = 'Finance'

# Canonical groups managed in Django Auth Groups
ALL_ROLES = (
    ROLE_OWNER,
    ROLE_FINANCE,
    ROLE_SITE_STAFF,
)

# All operational roles for RBAC and UI selection
ALL_OPERATIONAL_ROLES = (
    ROLE_ADMIN,
    ROLE_OWNER,
    ROLE_PROJECT_MANAGER,
    ROLE_SITE_ENGINEER,
    ROLE_SITE_STAFF,
    ROLE_ACCOUNTANT,
    ROLE_AUDITOR,
    ROLE_FINANCE,
)

# Canonical UI presentation choices
ROLE_CHOICES = [
    (ROLE_ADMIN, 'Admin / Owner (Full System & Financial Access)'),
    (ROLE_PROJECT_MANAGER, 'Project Manager (Projects, BOQ, Site Uploads, Financial Summaries)'),
    (ROLE_SITE_ENGINEER, 'Site Engineer (Site Logs, Expense Submissions, Progress)'),
    (ROLE_ACCOUNTANT, 'Auditor / Accountant (Invoices, Expenses, Tax, BOQ Rates)'),
    # Backwards-compatible choices for legacy forms and tests
    (ROLE_OWNER, 'Owner (Full System & Financial Access)'),
    (ROLE_FINANCE, 'Finance (Invoices, Expenses, Tax, BOQ Rates)'),
    (ROLE_SITE_STAFF, 'Site staff (Site Logs, Expense Submissions, Progress)'),
    (ROLE_AUDITOR, 'Auditor (Read-only Invoices, Expenses, Tax, BOQ Rates)'),
]

# Explicit permission codenames granted to each role
_ADMIN_PERMISSIONS = [
    # System & Governance
    'accounts.view_financials',
    'accounts.view_tax_reports',
    'accounts.export_reports',
    'accounts.manage_users',
    'accounts.view_audit_log',
    'accounts.edit_settings',

    # Operational Sections
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

    # Built-in Model Permissions
    'auth.view_user',
    'auth.add_user',
    'auth.change_user',
    'auth.view_group',
    'audit.view_auditevent',
]

_PROJECT_MANAGER_PERMISSIONS = [
    'accounts.view_overview',
    'accounts.view_projects',
    'accounts.add_projects',
    'accounts.change_projects',
    'accounts.view_rates',
    'accounts.add_rates',
    'accounts.change_rates',
    'accounts.view_files',
    'accounts.add_files',
    'accounts.change_files',
    'accounts.view_financials',  # Read-only access to client financial summaries
]

_SITE_ENGINEER_PERMISSIONS = [
    'accounts.view_overview',
    'accounts.view_projects',
    'accounts.view_rates',
    'accounts.view_expenses',
    'accounts.add_expenses',     # Expense submission
    'accounts.view_files',
    'accounts.add_files',        # Site documentation uploads
]

_ACCOUNTANT_PERMISSIONS = [
    # System & Governance
    'accounts.view_financials',
    'accounts.view_tax_reports',
    'accounts.export_reports',

    # Operational Sections
    'accounts.view_overview',
    'accounts.view_leads',
    'accounts.view_projects',
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
]

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    ROLE_ADMIN: _ADMIN_PERMISSIONS,
    ROLE_OWNER: _ADMIN_PERMISSIONS,
    ROLE_PROJECT_MANAGER: _PROJECT_MANAGER_PERMISSIONS,
    ROLE_SITE_ENGINEER: _SITE_ENGINEER_PERMISSIONS,
    ROLE_SITE_STAFF: _SITE_ENGINEER_PERMISSIONS,
    ROLE_ACCOUNTANT: _ACCOUNTANT_PERMISSIONS,
    ROLE_AUDITOR: _ACCOUNTANT_PERMISSIONS,
    ROLE_FINANCE: _ACCOUNTANT_PERMISSIONS,
}


def get_role_permissions(role_name: str) -> List[str]:
    """Returns the explicit permission strings for the specified role."""
    return ROLE_PERMISSIONS.get(role_name, [])


def get_user_role(user: User) -> Optional[str]:
    """
    Returns the single active role assigned to the user, or None.
    Checks profile first, then falls back to user groups.
    """
    if not user or not user.is_authenticated:
        return None

    if hasattr(user, 'profile') and user.profile.role:
        return user.profile.role

    for role in (ROLE_OWNER, ROLE_FINANCE, ROLE_SITE_STAFF):
        if user.groups.filter(name=role).exists():
            return role
    return None


def is_admin(user: User) -> bool:
    """Returns True if the user has Admin or Owner privileges."""
    if not user or not user.is_authenticated:
        return False
    role = get_user_role(user)
    return role in (ROLE_ADMIN, ROLE_OWNER) or user.groups.filter(name__in=[ROLE_ADMIN, ROLE_OWNER]).exists()


def assign_role(user: User, role_name: str) -> None:
    """
    Safely assigns exactly one canonical role to the given user.
    Enforces server-side guardrails:
    - Verifies role_name is valid.
    - Synchronizes Django Group and UserProfile.
    - Removes all other role groups.
    - Enforces is_superuser=False and is_staff=False.
    - Clears individual user_permissions.
    """
    if role_name not in ALL_OPERATIONAL_ROLES:
        raise ValueError(f"Invalid role '{role_name}'. Must be one of {ALL_OPERATIONAL_ROLES}.")

    # Canonical group assignment (maps aliases to standard group permissions)
    canonical_group_name = role_name
    if role_name in (ROLE_ADMIN, ROLE_OWNER):
        canonical_group_name = ROLE_OWNER
    elif role_name in (ROLE_ACCOUNTANT, ROLE_AUDITOR, ROLE_FINANCE):
        canonical_group_name = ROLE_FINANCE
    elif role_name in (ROLE_SITE_ENGINEER, ROLE_SITE_STAFF, ROLE_PROJECT_MANAGER):
        canonical_group_name = ROLE_SITE_STAFF

    group, _ = Group.objects.get_or_create(name=canonical_group_name)
    user.groups.set([group])
    user.is_superuser = False
    user.is_staff = False
    user.user_permissions.clear()

    # If role has specific permissions not in canonical group, add them
    if role_name == ROLE_PROJECT_MANAGER:
        for perm_str in _PROJECT_MANAGER_PERMISSIONS:
            if '.' in perm_str:
                app_label, codename = perm_str.split('.', 1)
                perm = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
                if perm:
                    user.user_permissions.add(perm)

    user.save(update_fields=['is_superuser', 'is_staff'])

    # Sync UserProfile role
    if hasattr(user, 'profile'):
        user.profile.role = role_name
        user.profile.save(update_fields=['role'])
    else:
        from accounts.models import UserProfile
        UserProfile.objects.create(user=user, role=role_name)
