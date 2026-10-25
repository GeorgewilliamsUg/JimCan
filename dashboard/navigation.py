"""
Centralized Navigation Registry for Jimcan Operations Dashboard.
Enforces role-based visibility and section prefix matching per
pp.md Phase 1 §1-2 and docs/design/roles-permissions.md.
"""

from typing import List, Dict, Any

NAVIGATION_ITEMS = [
    {
        "id": "overview",
        "name": "Dashboard",
        "url_name": "dashboard:overview",
        "url_prefix": "/overview",
        "exact_match": True,
        "icon": "layout-dashboard",
        "allowed_roles": ["admin", "manager"],
        "category": "operational",
    },
    {
        "id": "leads",
        "name": "Leads",
        "url_name": "dashboard:leads",
        "url_prefix": "/leads",
        "icon": "contact-round",
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
        "allowed_roles": ["admin", "manager", "accountant"],
        "category": "operational",
    },
    {
        "id": "invoices",
        "name": "Invoices",
        "url_name": "dashboard:invoices",
        "url_prefix": "/invoices",
        "icon": "receipt",
        "allowed_roles": ["admin", "manager", "accountant"],
        "category": "operational",
    },
    {
        "id": "expenses",
        "name": "Expenses",
        "url_name": "dashboard:expenses",
        "url_prefix": "/expenses",
        "icon": "wallet-cards",
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "operational",
    },
    {
        "id": "tax",
        "name": "Tax & Reports",
        "url_name": "dashboard:tax",
        "url_prefix": "/tax",
        "icon": "chart-no-axes-combined",
        "allowed_roles": ["admin", "accountant"],
        "category": "operational",
    },
    {
        "id": "files",
        "name": "Site Uploads",
        "url_name": "dashboard:files",
        "url_prefix": "/files",
        "icon": "upload-cloud",
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
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "admin",
        "badge": "P0",
    },
    {
        "id": "shell_demo",
        "name": "Shell & Feedback",
        "url_name": "dashboard:shell_demo",
        "url_prefix": "/shell-demo",
        "icon": "sliders",
        "allowed_roles": ["admin", "manager", "engineer", "accountant"],
        "category": "admin",
        "badge": "P1",
    },
    {
        "id": "settings",
        "name": "Settings",
        "url_name": "dashboard:settings",
        "url_prefix": "/settings",
        "icon": "settings",
        "allowed_roles": ["admin"],
        "category": "admin",
    },
    {
        "id": "audit",
        "name": "Audit Log",
        "url_name": "dashboard:audit",
        "url_prefix": "/audit",
        "icon": "shield-alert",
        "allowed_roles": ["admin"],
        "category": "admin",
    },
]

def get_navigation_items(role: str, current_path: str) -> List[Dict[str, Any]]:
    """
    Returns filtered navigation items permitted for the given role,
    with active section state determined by URL prefix matching.
    """
    role = role.lower() if role else "admin"
    permitted = []

    for item in NAVIGATION_ITEMS:
        if role in item["allowed_roles"]:
            item_copy = item.copy()
            # Active matching logic: exact match for root '/' or prefix match for subpaths
            if item.get("exact_match"):
                item_copy["is_active"] = (current_path == item["url_prefix"]) or (item["id"] == "overview" and current_path in ("/", "/overview", "/overview/", "/dashboard", "/dashboard/"))
            else:
                item_copy["is_active"] = current_path.startswith(item["url_prefix"])
            permitted.append(item_copy)

    return permitted
