"""
Centralized Navigation Registry for Jimcan Operations Dashboard.
Enforces role-based visibility and section prefix matching per
pp.md Phase 1 §1-2 and docs/design/roles-permissions.md.
"""

from typing import List, Dict, Any, Union
from django.conf import settings
from django.contrib.auth.models import User

NAVIGATION_ITEMS = [
    {
        "id": "overview",
        "name": "Dashboard",
        "url_name": "dashboard:overview",
        "url_prefix": "/overview",
        "exact_match": True,
        "icon": "layout-dashboard",
        "required_permission": "accounts.view_overview",
        "allowed_roles": ["admin", "manager"],
        "category": "operational",
    },
    {
        "id": "leads",
        "name": "Leads",
        "url_name": "dashboard:leads",
        "url_prefix": "/leads",
        "icon": "contact-round",
        "required_permission": "accounts.view_leads",
        "allowed_roles": ["admin", "manager"],
        "category": "operational",
        "badge": "3",
    },
    {
        "id": "projects",
        "name": "Projects",
        "url_name": "dashboard:projects",
        "url_prefix": "/projects",
        "icon": "hard-hat",
        "required_permission": "accounts.view_projects",
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "operational",
        "badge": "4",
    },
    {
        "id": "boq",
        "name": "BOQ & Rates",
        "url_name": "dashboard:rates",
        "url_prefix": "/rates",
        "icon": "notebook-tabs",
        "required_permission": "accounts.view_rates",
        "allowed_roles": ["admin", "manager", "accountant"],
        "category": "operational",
    },
    {
        "id": "invoices",
        "name": "Invoices",
        "url_name": "dashboard:invoices",
        "url_prefix": "/invoices",
        "icon": "receipt",
        "required_permission": "accounts.view_invoices",
        "allowed_roles": ["admin", "manager", "accountant"],
        "category": "operational",
    },
    {
        "id": "expenses",
        "name": "Expenses",
        "url_name": "dashboard:expenses",
        "url_prefix": "/expenses",
        "icon": "wallet-cards",
        "required_permission": "accounts.view_expenses",
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "operational",
    },
    {
        "id": "tax",
        "name": "Tax & Reports",
        "url_name": "dashboard:tax",
        "url_prefix": "/tax",
        "icon": "chart-no-axes-combined",
        "required_permission": "accounts.view_tax_reports",
        "allowed_roles": ["admin", "accountant"],
        "category": "operational",
    },
    {
        "id": "files",
        "name": "Site Uploads",
        "url_name": "dashboard:files",
        "url_prefix": "/files",
        "icon": "upload-cloud",
        "required_permission": "accounts.view_files",
        "allowed_roles": ["admin", "manager", "engineer"],
        "category": "operational",
    },
    # Secondary / Administration Items
    {
        "id": "styleguide",
        "name": "Style Guide",
        "url_name": "dashboard:styleguide",
        "url_prefix": "/styleguide",
        "icon": "palette",
        "required_permission": "accounts.view_overview",
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "admin",
        "badge": "P0",
        "is_debug_only": True,
    },
    {
        "id": "shell_demo",
        "name": "Shell & Feedback",
        "url_name": "dashboard:shell_demo",
        "url_prefix": "/shell-demo",
        "icon": "sliders",
        "required_permission": "accounts.view_overview",
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "admin",
        "badge": "P1",
        "is_debug_only": True,
    },
    {
        "id": "settings",
        "name": "Settings",
        "url_name": "dashboard:settings",
        "url_prefix": "/settings",
        "icon": "settings",
        "required_permission": "accounts.edit_settings",
        "allowed_roles": ["admin"],
        "category": "admin",
    },
    {
        "id": "users",
        "name": "Team & Roles",
        "url_name": "dashboard:settings_users",
        "url_prefix": "/settings/users",
        "icon": "users",
        "required_permission": "accounts.manage_users",
        "allowed_roles": ["admin"],
        "category": "admin",
    },
    {
        "id": "audit",
        "name": "Audit Log",
        "url_name": "dashboard:audit",
        "url_prefix": "/audit",
        "icon": "shield-alert",
        "required_permission": "accounts.view_audit_log",
        "allowed_roles": ["admin"],
        "category": "admin",
    },
]


def get_navigation_items(
    user_or_role: Union[User, str, None] = None,
    current_path: str = '/',
    role: Optional[str] = None,
    user: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Returns filtered navigation items permitted for the given user or role,
    with active section state determined by URL prefix matching.
    Hides 'Style guide' and 'Shell and feedback' pages when settings.DEBUG is False (Phase 5 Task 5).
    """
    target = user if user is not None else (role if role is not None else user_or_role)
    permitted = []
    is_user_obj = hasattr(target, 'has_perm')

    for item in NAVIGATION_ITEMS:
        # Phase 5 Task 5: Style guide & Shell demo exist only when DEBUG is true
        if item.get("is_debug_only") and not getattr(settings, 'DEBUG', False):
            continue

        is_allowed = False
        if is_user_obj:
            is_allowed = target.has_perm(item.get("required_permission"))
        elif isinstance(target, str):
            role_clean = target.lower()
            if role_clean == 'owner':
                role_clean = 'admin'
            elif role_clean == 'finance':
                role_clean = 'accountant'
            elif role_clean in ('site staff', 'staff'):
                role_clean = 'engineer'
            is_allowed = role_clean in item.get("allowed_roles", [])
        elif target is None:
            is_allowed = False

        if is_allowed:
            item_copy = item.copy()
            # Active matching logic: exact match for root '/' or prefix match for subpaths
            if item.get("exact_match"):
                item_copy["is_active"] = (current_path == item["url_prefix"]) or (
                    item["id"] == "overview" and current_path in ("/", "/overview", "/overview/", "/dashboard", "/dashboard/")
                )
            else:
                item_copy["is_active"] = current_path.startswith(item["url_prefix"])
            permitted.append(item_copy)

    return permitted
