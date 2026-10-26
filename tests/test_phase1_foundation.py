"""
Tests for Phase 1: Foundation and Hardening.
Verifies production settings, missing SECRET_KEY rejection, no-store cache headers,
admin disabling, and the security_status management command.
"""

import os
import subprocess
import sys
from io import StringIO
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import TestCase, Client, override_settings
from django.urls import reverse

User = get_user_model()


class ProductionSettingsTests(TestCase):
    """Verifies that production security settings match required values when DEBUG=False."""

    def test_production_settings_values_when_debug_false(self):
        """Simulates production environment settings to verify all security headers and flags."""
        env = os.environ.copy()
        env['DEBUG'] = 'False'
        env['SECRET_KEY'] = 'test-prod-key-with-sufficient-entropy-1234567890-test'
        env['ALLOWED_HOSTS'] = 'jimcanconstruction.site'
        env['ENABLE_ADMIN'] = 'False'

        code = (
            "import django, os; os.environ['DJANGO_SETTINGS_MODULE']='jimcan.settings'; "
            "django.setup(); from django.conf import settings; "
            "assert settings.SESSION_COOKIE_SECURE is True, 'SESSION_COOKIE_SECURE must be True'; "
            "assert settings.CSRF_COOKIE_SECURE is True, 'CSRF_COOKIE_SECURE must be True'; "
            "assert settings.SESSION_COOKIE_HTTPONLY is True, 'SESSION_COOKIE_HTTPONLY must be True'; "
            "assert settings.SESSION_COOKIE_SAMESITE == 'Lax', 'SESSION_COOKIE_SAMESITE must be Lax'; "
            "assert settings.CSRF_COOKIE_SAMESITE == 'Lax', 'CSRF_COOKIE_SAMESITE must be Lax'; "
            "assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True, 'SECURE_CONTENT_TYPE_NOSNIFF must be True'; "
            "assert settings.SECURE_REFERRER_POLICY == 'same-origin', 'SECURE_REFERRER_POLICY must be same-origin'; "
            "assert settings.X_FRAME_OPTIONS == 'DENY', 'X_FRAME_OPTIONS must be DENY'; "
            "assert settings.SECURE_HSTS_SECONDS == 300, 'SECURE_HSTS_SECONDS must be 300'; "
            "assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is False, 'SECURE_HSTS_INCLUDE_SUBDOMAINS must be False'; "
            "assert settings.SECURE_HSTS_PRELOAD is False, 'SECURE_HSTS_PRELOAD must be False'; "
            "print('PROD_SETTINGS_OK')"
        )

        res = subprocess.run([sys.executable, "-c", code], env=env, cwd=str(settings.BASE_DIR), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Production settings verification failed:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        self.assertIn("PROD_SETTINGS_OK", res.stdout)

    def test_secret_key_missing_refuses_to_start(self):
        """Verifies that missing SECRET_KEY raises ImproperlyConfigured and stops startup."""
        env = os.environ.copy()
        env.pop('SECRET_KEY', None)
        # Ensure .env does not override by running in an isolated sub-process with empty SECRET_KEY
        env['SECRET_KEY'] = ''

        code = (
            "import os, django\n"
            "os.environ['DJANGO_SETTINGS_MODULE'] = 'jimcan.settings'\n"
            "from django.core.exceptions import ImproperlyConfigured\n"
            "try:\n"
            "    django.setup()\n"
            "    print('UNEXPECTED_START')\n"
            "except ImproperlyConfigured:\n"
            "    print('CAUGHT_IMPROPERLY_CONFIGURED')\n"
        )
        res = subprocess.run([sys.executable, "-c", code], env=env, cwd=str(settings.BASE_DIR), capture_output=True, text=True)
        self.assertIn("CAUGHT_IMPROPERLY_CONFIGURED", res.stdout, f"Failed.\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        self.assertNotIn("UNEXPECTED_START", res.stdout)


class CacheControlMiddlewareSecurityTests(TestCase):
    """Verifies Cache-Control: no-store, private behavior."""

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='cache_test_user',
            password='TestPassword123!Secure'
        )

    def tearDown(self):
        self.test_user.delete()

    def test_no_store_header_present_on_login_page_unauthenticated(self):
        """Login page must send no-store, private even to anonymous visitors."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        cache_control = response.headers.get('Cache-Control', '')
        self.assertIn('no-store', cache_control)
        self.assertIn('private', cache_control)

    def test_no_store_header_present_on_authenticated_response(self):
        """Any response to an authenticated user must include no-store, private."""
        self.client.login(username='cache_test_user', password='TestPassword123!Secure')
        response = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(response.status_code, 200)
        cache_control = response.headers.get('Cache-Control', '')
        self.assertIn('no-store', cache_control)
        self.assertIn('private', cache_control)

    def test_no_store_header_absent_on_static_files(self):
        """Static asset requests must not have no-store injected by the middleware."""
        # Test directly requesting a static URL
        response = self.client.get('/static/css/tokens.css')
        cache_control = response.headers.get('Cache-Control', '')
        self.assertNotIn('no-store', cache_control)


class AdminUrlDisablingTests(TestCase):
    """Verifies admin URL conditional registration."""

    def test_admin_returns_404_when_enable_admin_is_off(self):
        """When ENABLE_ADMIN is False, /admin/ route does not exist and returns 404."""
        client = Client()
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 404)


class SecurityStatusCommandTests(TestCase):
    """Verifies python manage.py security_status functionality."""

    def test_security_status_fails_when_superuser_exists(self):
        """security_status must exit non-zero when a superuser account exists."""
        # Create a throwaway superuser for this test
        su = User.objects.create_superuser(
            username='temp_phase1_superuser',
            password='TemporarySuperUserPass123!',
            email='su@test.local'
        )
        try:
            out = StringIO()
            with self.assertRaises(SystemExit) as cm:
                call_command('security_status', stdout=out)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Found", out.getvalue())
            self.assertIn("superuser account(s)", out.getvalue())
        finally:
            su.delete()
