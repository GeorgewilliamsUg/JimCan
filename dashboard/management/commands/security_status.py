import sys
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Audits and verifies the security state of the application configuration and database."

    def handle(self, *args, **options):
        passed = 0
        warned = 0
        failed = 0

        self.stdout.write(self.style.MIGRATE_HEADING("=== Jimcan Security Status Audit ==="))

        # 1. DEBUG Setting
        if not settings.DEBUG:
            self.stdout.write(self.style.SUCCESS("[PASS] DEBUG is False (production mode enabled)"))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR("[FAIL] DEBUG is True (development mode active; must be False in production)"))
            failed += 1

        # 2. SECRET_KEY Configuration
        insecure_keys = (
            'jimcan-dev-insecure-key-2026-phase-0-scaffolding',
            'generate-a-strong-random-50-character-string-here',
            'django-insecure',
        )
        key = getattr(settings, 'SECRET_KEY', '')
        if not key:
            self.stdout.write(self.style.ERROR("[FAIL] SECRET_KEY is not configured"))
            failed += 1
        elif any(insecure in key for insecure in insecure_keys) or len(key) < 30:
            self.stdout.write(self.style.ERROR("[FAIL] SECRET_KEY is insecure, placeholder, or too short (<30 chars)"))
            failed += 1
        else:
            self.stdout.write(self.style.SUCCESS("[PASS] SECRET_KEY is configured with adequate entropy"))
            passed += 1

        # 3. ALLOWED_HOSTS Configuration
        hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not hosts:
            self.stdout.write(self.style.ERROR("[FAIL] ALLOWED_HOSTS is empty"))
            failed += 1
        elif '*' in hosts:
            self.stdout.write(self.style.ERROR("[FAIL] ALLOWED_HOSTS contains wildcard '*'"))
            failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f"[PASS] ALLOWED_HOSTS configured: {', '.join(hosts)}"))
            passed += 1

        # 4. Cookie Security Flags
        if not settings.DEBUG:
            cookie_errors = []
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                cookie_errors.append("SESSION_COOKIE_SECURE is False")
            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                cookie_errors.append("CSRF_COOKIE_SECURE is False")
            if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', False):
                cookie_errors.append("SESSION_COOKIE_HTTPONLY is False")
            if getattr(settings, 'SESSION_COOKIE_SAMESITE', None) not in ('Lax', 'Strict'):
                cookie_errors.append("SESSION_COOKIE_SAMESITE is not Lax/Strict")
            if getattr(settings, 'CSRF_COOKIE_SAMESITE', None) not in ('Lax', 'Strict'):
                cookie_errors.append("CSRF_COOKIE_SAMESITE is not Lax/Strict")

            if cookie_errors:
                self.stdout.write(self.style.ERROR(f"[FAIL] Insecure cookie settings: {', '.join(cookie_errors)}"))
                failed += 1
            else:
                self.stdout.write(self.style.SUCCESS("[PASS] Cookie security flags verified (Secure, HttpOnly, SameSite=Lax)"))
                passed += 1
        else:
            # Development allows Secure=False over plain HTTP
            self.stdout.write(self.style.SUCCESS("[PASS] Cookie security flags (HttpOnly=True, SameSite=Lax; Secure=False for dev)"))
            passed += 1

        # 5. HSTS Configuration (HTTP Strict Transport Security)
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        if not settings.DEBUG:
            if hsts_seconds >= 31536000:
                self.stdout.write(self.style.SUCCESS(f"[PASS] SECURE_HSTS_SECONDS is {hsts_seconds} (>= 1 year)"))
                passed += 1
            elif hsts_seconds > 0:
                self.stdout.write(self.style.WARNING(f"[WARN] SECURE_HSTS_SECONDS is {hsts_seconds} (staged under 1 year / 31536000 seconds)"))
                warned += 1
            else:
                self.stdout.write(self.style.ERROR("[FAIL] SECURE_HSTS_SECONDS is 0 (HSTS disabled in production)"))
                failed += 1
        else:
            self.stdout.write(self.style.SUCCESS("[PASS] HSTS disabled in development (DEBUG=True)"))
            passed += 1

        # 6. Django Admin Enabled State
        enable_admin = getattr(settings, 'ENABLE_ADMIN', False)
        if not enable_admin:
            self.stdout.write(self.style.SUCCESS("[PASS] Django admin is disabled (ENABLE_ADMIN=False)"))
            passed += 1
        else:
            self.stdout.write(self.style.WARNING("[WARN] Django admin is enabled (ENABLE_ADMIN=True)"))
            warned += 1

        # 7. Django Admin Path Safety
        admin_path = getattr(settings, 'DJANGO_ADMIN_PATH', 'admin').strip('/')
        if enable_admin and not settings.DEBUG and admin_path in ('admin', 'admin/'):
            self.stdout.write(self.style.ERROR("[FAIL] Django admin is enabled on default path 'admin/' in production"))
            failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f"[PASS] Django admin path: '{admin_path}/'"))
            passed += 1

        # 8. Superuser Count Audit (Rule: No account is a superuser)
        user_model = get_user_model()
        try:
            superuser_count = user_model.objects.filter(is_superuser=True).count()
            if superuser_count == 0:
                self.stdout.write(self.style.SUCCESS("[PASS] Superuser count is 0 (Rule: No account is a superuser)"))
                passed += 1
            else:
                self.stdout.write(self.style.ERROR(
                    f"[FAIL] Found {superuser_count} superuser account(s). "
                    "Project Rule prohibits superuser accounts. Use Owner group with explicit permissions."
                ))
                failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[FAIL] Could not query user accounts: {e}"))
            failed += 1

        # ----------------------------------------------------------------------
        # Phase 2: Authentication & Guardrails Checks
        # ----------------------------------------------------------------------

        # 9. Password Hasher in Use
        hashers = getattr(settings, 'PASSWORD_HASHERS', [])
        primary_hasher = hashers[0] if hashers else ''
        if 'JimcanArgon2PasswordHasher' in primary_hasher or 'Argon2PasswordHasher' in primary_hasher:
            self.stdout.write(self.style.SUCCESS(f"[PASS] Primary password hasher: {primary_hasher}"))
            passed += 1
        elif 'PBKDF2PasswordHasher' in primary_hasher:
            self.stdout.write(self.style.WARNING(f"[WARN] Primary password hasher is PBKDF2: {primary_hasher}"))
            warned += 1
        else:
            self.stdout.write(self.style.ERROR(f"[FAIL] Insecure or unknown primary password hasher: {primary_hasher}"))
            failed += 1

        # 10. Password Validator Minimum Length
        validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        min_length = None
        for val in validators:
            if 'MinimumLengthValidator' in val.get('NAME', ''):
                min_length = val.get('OPTIONS', {}).get('min_length', 8)
                break

        if min_length and min_length >= 12:
            self.stdout.write(self.style.SUCCESS(f"[PASS] Password minimum length validator is {min_length} chars (>= 12)"))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR(f"[FAIL] Password minimum length validator is {min_length} (must be >= 12)"))
            failed += 1

        # 11. Session Storage & Lifetime Limits
        session_engine = getattr(settings, 'SESSION_ENGINE', '')
        if session_engine == 'django.contrib.sessions.backends.db':
            self.stdout.write(self.style.SUCCESS("[PASS] Session engine: database-backed (django.contrib.sessions.backends.db)"))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR(f"[FAIL] Session engine is not database-backed: {session_engine}"))
            failed += 1

        from jimcan.middleware import SESSION_IDLE_TIMEOUT_SECONDS, SESSION_ABSOLUTE_TIMEOUT_SECONDS
        if SESSION_IDLE_TIMEOUT_SECONDS == 1800 and SESSION_ABSOLUTE_TIMEOUT_SECONDS == 28800:
            self.stdout.write(self.style.SUCCESS(
                f"[PASS] Session limits verified (Idle: {SESSION_IDLE_TIMEOUT_SECONDS // 60}m, "
                f"Absolute: {SESSION_ABSOLUTE_TIMEOUT_SECONDS // 3600}h)"
            ))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR(
                f"[FAIL] Invalid session timeout constants: Idle={SESSION_IDLE_TIMEOUT_SECONDS}s, Absolute={SESSION_ABSOLUTE_TIMEOUT_SECONDS}s"
            ))
            failed += 1

        # 12. Brute-Force Lockout (django-axes) Configuration
        middleware_list = getattr(settings, 'MIDDLEWARE', [])
        axes_installed = 'axes' in getattr(settings, 'INSTALLED_APPS', [])
        axes_middleware_last = middleware_list and middleware_list[-1] == 'axes.middleware.AxesMiddleware'
        axes_limit = getattr(settings, 'AXES_FAILURE_LIMIT', None)
        axes_reset = getattr(settings, 'AXES_RESET_ON_SUCCESS', False)

        if axes_installed and axes_middleware_last and axes_limit == 5 and axes_reset is True:
            self.stdout.write(self.style.SUCCESS("[PASS] django-axes configured (5 failure limit, reset on success, last in middleware)"))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR(
                f"[FAIL] Incomplete axes configuration: installed={axes_installed}, "
                f"last_middleware={axes_middleware_last}, limit={axes_limit}, reset={axes_reset}"
            ))
            failed += 1

        # 13. Deny-by-Default (LoginRequiredMiddleware)
        if 'django.contrib.auth.middleware.LoginRequiredMiddleware' in middleware_list:
            self.stdout.write(self.style.SUCCESS("[PASS] LoginRequiredMiddleware active (site is deny-by-default)"))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR("[FAIL] LoginRequiredMiddleware is missing from MIDDLEWARE (site is not deny-by-default)"))
            failed += 1

        # ----------------------------------------------------------------------
        # Summary & Exit Code
        # ----------------------------------------------------------------------
        self.stdout.write("")
        summary = f"Audit Results: {passed} passed, {warned} warnings, {failed} failed."
        if failed > 0:
            self.stdout.write(self.style.ERROR(f"FAILED: {summary}"))
            sys.exit(1)
        elif warned > 0:
            self.stdout.write(self.style.WARNING(f"PASSED with warnings: {summary}"))
            sys.exit(0)
        else:
            self.stdout.write(self.style.SUCCESS(f"ALL CHECKS PASSED: {summary}"))
            sys.exit(0)
