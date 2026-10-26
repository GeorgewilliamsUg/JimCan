"""
Public URL Allowlist for Jimcan Operations Dashboard.
Implements Phase 2 Task 8: Explicit central registry of unauthenticated / public URL names.
Any URL not listed in PUBLIC_URL_NAMES or wrapped in login_not_required will deny access by default.
"""

PUBLIC_URL_NAMES = (
    'welcome',
    'login',
    'logout',
    'password_reset',
    'password_reset_done',
    'password_reset_confirm',
    'password_reset_complete',
    'account_setup',
)
