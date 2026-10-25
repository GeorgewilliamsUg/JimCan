"""
Security, caching, and HTMX guardrail middleware for Jimcan Operations Dashboard.
Mitigates Risk #5: Stale private data exposed via browser history after sign-out.
Mitigates Phase 2 Risk: HTMX requests timing out and rendering raw login HTML inside partial dashboard widgets.
"""

from urllib.parse import quote
from django.conf import settings
from django.urls import reverse

class HtmxAuthRedirectMiddleware:
    """
    Guards against HTMX partial requests rendering login HTML into inner components.
    When an HTMX request encounters a 401, 403, or a redirect to the login page
    (e.g., expired session or unauthenticated request), this middleware injects
    an 'HX-Redirect' header to instruct HTMX to perform a full-window browser redirect.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Detect HTMX request
        is_htmx = request.headers.get('HX-Request') == 'true' or getattr(request, 'htmx', False)
        if not is_htmx:
            return response

        # Resolve login url path
        login_url = getattr(settings, 'LOGIN_URL', '/login/')
        if not login_url.startswith('/'):
            try:
                login_url = reverse(login_url)
            except Exception:
                login_url = '/login/'

        # 1. Intercept 401 Unauthorized or 403 Forbidden
        if response.status_code in (401, 403):
            next_param = quote(request.get_full_path())
            response['HX-Redirect'] = f"{login_url}?next={next_param}"
            return response

        # 2. Intercept 301/302 redirects targeting the login page
        if response.status_code in (301, 302):
            location = response.get('Location', '')
            if login_url in location or location.startswith('/login'):
                response['HX-Redirect'] = location
                return response

        return response


class PrivateCacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply strict private no-cache headers to all HTML responses
        # Static files and media are handled separately by WhiteNoise/Apache
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response

