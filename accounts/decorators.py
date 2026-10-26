"""
Re-authentication ("step-up") Decorators & Mixins.
Implements Phase 2 Task 9: Requires recent authentication (within 10 minutes)
before sensitive operations (user editing, tax exports, voiding, role change).
"""

from functools import wraps
from urllib.parse import quote
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


def require_recent_auth(minutes: int = 10):
    """
    View decorator that verifies the current user has authenticated within `minutes`.
    If `reauth_at` in the session is missing or older than the threshold, redirects
    to `accounts:reauth?next=<current_path>`.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                next_url = quote(request.get_full_path())
                return redirect(f"{reverse('login')}?next={next_url}")

            reauth_at = request.session.get('reauth_at')
            now_ts = timezone.now().timestamp()
            threshold_seconds = minutes * 60

            from django_otp import user_has_device
            has_mfa = user_has_device(request.user)
            is_verified = request.user.is_verified() if hasattr(request.user, 'is_verified') else False

            if not reauth_at or (now_ts - float(reauth_at) > threshold_seconds) or (has_mfa and not is_verified):
                next_url = quote(request.get_full_path())
                return redirect(f"{reverse('accounts:reauth')}?next={next_url}")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RecentAuthRequiredMixin(AccessMixin):
    """
    Class-based view mixin enforcing recent authentication within `reauth_minutes` (default: 10).
    """
    reauth_minutes = 10

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        reauth_at = request.session.get('reauth_at')
        now_ts = timezone.now().timestamp()
        threshold_seconds = self.reauth_minutes * 60

        from django_otp import user_has_device
        has_mfa = user_has_device(request.user)
        is_verified = request.user.is_verified() if hasattr(request.user, 'is_verified') else False

        if not reauth_at or (now_ts - float(reauth_at) > threshold_seconds) or (has_mfa and not is_verified):
            next_url = quote(request.get_full_path())
            return redirect(f"{reverse('accounts:reauth')}?next={next_url}")

        return super().dispatch(request, *args, **kwargs)
