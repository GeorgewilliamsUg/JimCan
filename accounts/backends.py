"""
Custom Authentication Backends for Jimcan Operations Dashboard.
Implements Phase 2: Axes integration with graceful fallback when request is None (CLI / test client).
"""

from axes.backends import AxesStandaloneBackend


class JimcanAxesBackend(AxesStandaloneBackend):
    """
    Subclass of AxesStandaloneBackend that gracefully falls through
    when request is None (e.g., in unit tests using client.login() or CLI commands),
    allowing ModelBackend to authenticate while strictly enforcing Axes lockout
    on all real HTTP requests where request is present.
    """
    def authenticate(self, request=None, username=None, password=None, **kwargs):
        if request is None:
            return None
        return super().authenticate(request, username=username, password=password, **kwargs)
