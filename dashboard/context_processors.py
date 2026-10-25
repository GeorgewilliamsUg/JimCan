from .navigation import get_navigation_items

def navigation_context(request):
    """
    Context processor providing role-aware navigation and current section state.
    Allows dynamic role preview via ?role= parameter or request.user.
    """
    # Check if a role override is active in session or query param (for testing/demo)
    role = request.GET.get('role')
    if role:
        request.session['active_role'] = role.lower()
    
    current_role = request.session.get('active_role')
    if not current_role:
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_role = getattr(request.user, 'role', 'admin')
        else:
            current_role = 'admin'

    items = get_navigation_items(current_role, request.path)
    operational_items = [i for i in items if i.get('category') == 'operational']
    admin_items = [i for i in items if i.get('category') == 'admin']

    return {
        'current_role': current_role,
        'current_role_display': {
            'admin': 'Admin',
            'manager': 'Manager',
            'engineer': 'Site Engineer',
            'accountant': 'Accountant',
        }.get(current_role, 'Admin'),
        'operational_nav': operational_items,
        'admin_nav': admin_items,
        'all_roles': [
            ('admin', 'Admin (Full Company View)'),
            ('manager', 'Manager (Assigned Builds)'),
            ('engineer', 'Site Engineer (Field View)'),
            ('accountant', 'Accountant (Read-Only & Tax)'),
        ],
    }
