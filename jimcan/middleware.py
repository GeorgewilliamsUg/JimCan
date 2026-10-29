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
    """
    Enforces 'Cache-Control: no-store, private' on:
    - Every response to an authenticated request.
    - All login, logout, password change/reset, and two-factor pages.
    - All rendered HTML responses to prevent browser back-button caching of sensitive data.
    Static files and media assets are never modified.
    """
    SENSITIVE_PREFIXES = (
        '/login',
        '/logout',
        '/password_change',
        '/password_reset',
        '/reset',
        '/two-factor',
        '/account',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Do not modify static files or media assets
        path = request.path_info
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        if (static_url and static_url != '/' and path.startswith(static_url)) or \
           (media_url and media_url != '/' and path.startswith(media_url)):
            return response

        # Check authentication state
        is_authenticated = hasattr(request, 'user') and request.user.is_authenticated

        # Check sensitive authentication/credential endpoints (even unauthenticated)
        is_sensitive = any(path.startswith(prefix) for prefix in self.SENSITIVE_PREFIXES)
        if path in ('/', ''):
            is_sensitive = True

        # Check HTML response
        content_type = response.headers.get('Content-Type', '')
        is_html = 'text/html' in content_type

        if is_authenticated or is_sensitive or is_html:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response


# Session Lifetimes (Phase 2 Task 6)
SESSION_IDLE_TIMEOUT_SECONDS = 1800       # 30 minutes
SESSION_ABSOLUTE_TIMEOUT_SECONDS = 28800  # 8 hours


class SessionTimeoutMiddleware:
    """
    Enforces session timeout guardrails:
    - Idle timeout: 30 minutes of inactivity.
    - Absolute timeout: 8 hours maximum session lifetime.
    Updates last_activity at most once per 60 seconds to prevent unnecessary DB writes.
    When a limit is reached, logs the user out and redirects to login with 'Your session expired.'
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            import time
            from django.contrib.auth import logout
            from django.contrib import messages
            from django.shortcuts import redirect

            now = int(time.time())
            started_at = request.session.get('session_started_at')
            last_activity = request.session.get('last_activity')

            # 1. Initialize session start time if not recorded
            if not started_at:
                request.session['session_started_at'] = now
                request.session['last_activity'] = now
            else:
                # 2. Check Absolute Timeout (8 hours)
                if now - started_at > SESSION_ABSOLUTE_TIMEOUT_SECONDS:
                    logout(request)
                    if hasattr(request, '_messages'):
                        messages.warning(request, "Your session expired.")
                    return redirect('login')

                # 3. Check Idle Timeout (30 minutes)
                if last_activity and (now - last_activity > SESSION_IDLE_TIMEOUT_SECONDS):
                    logout(request)
                    if hasattr(request, '_messages'):
                        messages.warning(request, "Your session expired.")
                    return redirect('login')

                # 4. Throttle activity updates to once per 60 seconds
                if last_activity and (now - last_activity >= 60):
                    request.session['last_activity'] = now

        return self.get_response(request)


class MFAEnforcementMiddleware:
    """
    Enforces two-factor authentication (Phase 4 Task 3).
    If a request is authenticated but the user is not verified (request.user.is_verified() is False),
    redirects to the setup page (if unenrolled) or verify page (if enrolled).
    Allowlists only:
    - The two-factor pages (/account/two_factor/*, /two_factor/*, /account/login/, /login/)
    - Logout (/logout/)
    - Static and media files
    - Central public URLs
    Controlled by settings.MFA_ENFORCEMENT ('off', 'owners', 'all').
    """
    EXEMPT_PREFIXES = (
        '/account/two_factor/',
        '/two_factor/',
        '/account/login',
        '/login',
        '/logout',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # 1. Static and media assets are always exempt
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        if (static_url and static_url != '/' and path.startswith(static_url)) or \
           (media_url and media_url != '/' and path.startswith(media_url)):
            return self.get_response(request)

        # 2. Unauthenticated requests are handled by LoginRequiredMiddleware
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        # Force Password Change requirement check for first login / temporary passwords
        if hasattr(user, 'profile') and user.profile.must_change_password:
            force_pwd = ForcePasswordChangeMiddleware(lambda req: None)
            pwd_resp = force_pwd(request)
            if pwd_resp is not None:
                return pwd_resp

        # 3. If user is already verified via 2FA, pass through
        if hasattr(user, 'is_verified') and user.is_verified():
            return self.get_response(request)

        # 4. Check MFA_ENFORCEMENT mode ('off', 'owners', 'all')
        mode = getattr(settings, 'MFA_ENFORCEMENT', 'all' if not settings.DEBUG else 'off').lower()
        if mode == 'off':
            return self.get_response(request)
        elif mode == 'owners':
            is_owner = user.groups.filter(name='Owner').exists()
            if not is_owner:
                return self.get_response(request)
        elif mode == 'all':
            pass
        else:
            # Safe fail-closed default
            pass

        # 5. Check exempt path prefixes
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return self.get_response(request)

        # Check public URL allowlist
        try:
            from django.urls import resolve
            from accounts.public_urls import PUBLIC_URL_NAMES
            match = resolve(path)
            if match.url_name in PUBLIC_URL_NAMES or match.view_name in PUBLIC_URL_NAMES:
                return self.get_response(request)
        except Exception:
            pass

        # 6. User is authenticated, required to have MFA, but not verified
        from django_otp import user_has_device
        from django.http import HttpResponse
        from django.shortcuts import redirect
        from django.urls import reverse

        has_device = user_has_device(user)
        target_url = reverse('two_factor:login') if has_device else reverse('two_factor:setup')

        # HTMX intercept
        is_htmx = request.headers.get('HX-Request') == 'true' or getattr(request, 'htmx', False)
        if is_htmx:
            resp = HttpResponse(status=204)
            resp['HX-Redirect'] = target_url
            return resp

        return redirect(target_url)


class ForcePasswordChangeMiddleware:
    """
    Forces newly provisioned or reset users with must_change_password=True
    to update their password before accessing any dashboard or operational routes.
    """
    EXEMPT_URL_NAMES = (
        'password_change',
        'password_change_done',
        'logout',
        'accounts:logout',
        'two_factor:setup',
        'two_factor:setup_complete',
        'two_factor:qr',
        'two_factor:backup_tokens',
    )
    EXEMPT_PREFIXES = (
        '/password_change',
        '/logout',
        '/account/two_factor',
        '/two-factor',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        if (static_url and static_url != '/' and path.startswith(static_url)) or \
           (media_url and media_url != '/' and path.startswith(media_url)):
            return self.get_response(request)

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        # Check if user must change password
        must_change = False
        if hasattr(user, 'profile') and user.profile.must_change_password:
            must_change = True

        if not must_change:
            return self.get_response(request)

        # Allow exempt routes
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return self.get_response(request)

        from django.urls import resolve
        try:
            match = resolve(path)
            if match.url_name in self.EXEMPT_URL_NAMES or match.view_name in self.EXEMPT_URL_NAMES:
                return self.get_response(request)
        except Exception:
            pass

        # User must change password -> redirect directly to password change view
        from django.http import HttpResponse
        from django.shortcuts import redirect
        from django.urls import reverse

        target_url = reverse('password_change')

        is_htmx = request.headers.get('HX-Request') == 'true' or getattr(request, 'htmx', False)
        if is_htmx:
            resp = HttpResponse(status=204)
            resp['HX-Redirect'] = target_url
            return resp

        return redirect(target_url)

