from .navigation import get_navigation_items
from accounts.roles import get_user_role, ROLE_OWNER, ROLE_FINANCE, ROLE_SITE_STAFF

def navigation_context(request):
    """
    Context processor providing role-aware navigation and current section state.
    Uses request.user permissions as the single source of truth.
    """
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        items = get_navigation_items(user, request.path)
        current_role = get_user_role(user) or 'Site staff'
    else:
        items = get_navigation_items(None, request.path)
        current_role = None

    operational_items = [i for i in items if i.get('category') == 'operational']
    admin_items = [i for i in items if i.get('category') == 'admin']

    return {
        'current_role': current_role,
        'current_role_display': current_role or 'Guest',
        'operational_nav': operational_items,
        'admin_nav': admin_items,
        'all_roles': [
            (ROLE_OWNER, 'Owner (Full Access)'),
            (ROLE_FINANCE, 'Finance (Financials & Reporting)'),
            (ROLE_SITE_STAFF, 'Site staff (Field & Projects View)'),
        ],
    }

