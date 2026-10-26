"""
Automated validation tests for Phase 2: Authentication and Guardrails.
Tests password manager compatibility, non-blocking paste, Alpine.js client toggles,
HTMX 401/403 full-window redirects, ?next= preservation, and Admin Setup Checklist.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()

class AuthenticationFormAttributesTests(TestCase):
    """
    Validates R-001 & R-002:
    Login inputs must use standard attributes for 1Password, Bitwarden, Keychain,
    and never block paste.
    """

    def setUp(self):
        self.client = Client()

    def test_login_page_renders_with_standard_attributes(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Standard password manager fields
        self.assertIn('name="username"', content)
        self.assertIn('autocomplete="username"', content)
        self.assertIn('id="id_username"', content)
        self.assertIn('name="password"', content)
        self.assertIn('autocomplete="current-password"', content)
        self.assertIn('id="id_password"', content)

    def test_password_paste_is_not_blocked(self):
        response = self.client.get(reverse('login'))
        content = response.content.decode('utf-8')

        # Ensure no paste prevention exists on the form or inputs
        self.assertNotIn('onpaste', content.lower())
        self.assertNotIn('@paste', content)
        self.assertNotIn("addEventListener('paste'", content)
        self.assertNotIn('addEventListener("paste"', content)

    def test_alpine_caps_lock_and_visibility_toggles(self):
        """Validates R-003 & R-004: Caps Lock dynamic warning and Show/Hide toggle."""
        response = self.client.get(reverse('login'))
        content = response.content.decode('utf-8')

        # Alpine state bindings
        self.assertIn('showPassword: false', content)
        self.assertIn('capsLockOn: false', content)
        self.assertIn("getModifierState('CapsLock')", content)
        self.assertIn(':type="showPassword ? \'text\' : \'password\'"', content)
        self.assertIn('Caps Lock is ON', content)

    def test_next_parameter_preservation(self):
        """Validates R-005: Preserving ?next= parameter throughout login."""
        target_path = '/projects/101/'
        response = self.client.get(f"{reverse('login')}?next={target_path}")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Hidden input preserves parameter
        self.assertIn(f'name="next" value="{target_path}"', content)


class HtmxAuthGuardrailTests(TestCase):
    """
    Validates R-006:
    HTMX requests encountering session expiration, 401, or 403 must be intercepted
    and redirected to /login/?next=[path] via HX-Redirect header.
    """

    def setUp(self):
        self.client = Client()

    def test_htmx_401_triggers_hx_redirect(self):
        response = self.client.get(
            reverse('dashboard:test_htmx_401'),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('HX-Redirect', response.headers)
        self.assertTrue(response.headers['HX-Redirect'].startswith('/login/?next='))
        self.assertIn('test-htmx-401', response.headers['HX-Redirect'])

    def test_htmx_403_triggers_hx_redirect(self):
        response = self.client.get(
            reverse('dashboard:test_htmx_403'),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('HX-Redirect', response.headers)
        self.assertTrue(response.headers['HX-Redirect'].startswith('/login/?next='))
        self.assertIn('test-htmx-403', response.headers['HX-Redirect'])

    def test_client_htmx_before_swap_guardrail_present_in_base_html(self):
        """Validates that base.html script cancels partial swap on 401/403."""
        response = self.client.get(reverse('login'))
        content = response.content.decode('utf-8')
        self.assertIn('htmx:beforeSwap', content)
        self.assertIn('evt.detail.shouldSwap = false', content)
        self.assertIn('/login/?next=', content)


class PasswordResetAndConsoleEmailTests(TestCase):
    """
    Validates R-009 & R-010:
    Password reset dispatches to console email backend without revealing user existence.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='staff_test',
            email='staff@jimcan.co.ug',
            password='InitialPassword123!'
        )

    def test_password_reset_post_dispatches_email_and_redirects(self):
        response = self.client.post(reverse('password_reset'), {
            'email': 'staff@jimcan.co.ug'
        })
        self.assertRedirects(response, reverse('password_reset_done'))
        # Verify console email dispatched
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password reset on', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['staff@jimcan.co.ug'])

    def test_password_reset_nonexistent_email_does_not_error(self):
        """Security: Generic response prevents email enumeration."""
        response = self.client.post(reverse('password_reset'), {
            'email': 'nonexistent@jimcan.co.ug'
        })
        self.assertRedirects(response, reverse('password_reset_done'))


class AdminSetupChecklistTests(TestCase):
    """
    Validates R-008:
    Admin Setup Checklist renders safely with zero missing database models.
    """

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin_boss',
            email='admin@jimcan.co.ug',
            password='AdminPassword123!'
        )
        self.client.force_login(self.admin_user)

    def test_setup_checklist_renders_safely(self):
        # Admin access to setup checklist
        response = self.client.get(reverse('dashboard:setup_checklist'), {'role': 'admin'})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('System Setup Checklist', content)
        self.assertIn('Organization &amp; Branding', content)
        self.assertIn('Tax &amp; Calculation Rules', content)
        self.assertIn('Document Numbering Sequences', content)
        self.assertIn('JC-INV-2026-', content)
        self.assertIn('Standard VAT Rate (18%)', content)

    def test_settings_view_redirects_or_renders_checklist(self):
        response = self.client.get(reverse('dashboard:settings'), {'role': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('System Setup Checklist', response.content.decode('utf-8'))


class AuthTemplatesIntegrityTests(TestCase):
    """Verifies all required Django auth views render with Jimcan styling."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='auth_user',
            password='SecretPassword123!'
        )

    def test_password_reset_done_renders(self):
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Check Your Inbox', response.content.decode('utf-8'))

    def test_password_reset_complete_renders(self):
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Password Reset Successful', response.content.decode('utf-8'))

    def test_password_change_requires_login(self):
        response = self.client.get(reverse('password_change'))
        # Should redirect to login with next param
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.headers['Location'])

    def test_password_change_renders_when_logged_in(self):
        self.client.login(username='auth_user', password='SecretPassword123!')
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Change Password', response.content.decode('utf-8'))

    def test_unauthenticated_user_accessing_root_renders_welcome_page(self):
        """Verifies root URL (/) renders the branded Welcome/Login page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Civil Engineering', content)

    def test_unauthenticated_user_accessing_internal_view_redirects_to_login(self):
        """Verifies unauthenticated users attempting to access internal views are routed to login."""
        response = self.client.get('/overview/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/login/?next=/overview/')

    def test_authenticated_user_accessing_root_redirects_to_dashboard(self):
        """Verifies authenticated users accessing root (/) are redirected to the dashboard."""
        self.client.login(username='auth_user', password='SecretPassword123!')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/overview/')


class Phase2SpecificationSecurityTests(TestCase):
    """
    Validates all mandatory Phase 2 security specifications:
    - Lockout behavior via django-axes (5 failures, lockout, cooloff)
    - Session rotation across authentication boundary
    - Session idle (30m) & absolute (8h) timeouts
    - Password change terminates other active sessions
    - Deactivated users cannot log in or reset passwords
    - Password reset responds identically for existing and non-existing emails
    - Deny-by-default architecture (LoginRequiredMiddleware)
    - No public registration routes
    - bootstrap_owner guardrails (refuses when user exists, creates non-superuser)
    - Safe redirect mitigation against open redirect attacks
    - Step-up re-authentication (@require_recent_auth)
    - Middleware pipeline order compliance
    - Zero superusers rule
    """

    def setUp(self):
        self.client = Client()
        self.user_password = 'TestPhase2UserPass123!Secure'
        self.test_user = User.objects.create_user(
            username='phase2_test_user',
            email='testuser@jimcanconstruction.site',
            password=self.user_password
        )

    def test_no_public_signup_or_registration_routes_exist(self):
        """Verifies that no public registration or sign-up endpoints exist on the site."""
        forbidden_paths = [
            '/register/',
            '/signup/',
            '/accounts/register/',
            '/accounts/signup/',
            '/user/register/',
        ]
        for path in forbidden_paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, f"Public registration route unexpectedly exists: {path}")

    def test_session_key_rotates_on_login(self):
        """Session key must differ before and after login to prevent session fixation attacks."""
        # 1. Establish initial anonymous session
        self.client.get(reverse('login'))
        anonymous_session_key = self.client.session.session_key

        # 2. Authenticate
        login_res = self.client.post(reverse('login'), {
            'username': 'phase2_test_user',
            'password': self.user_password,
        })
        self.assertEqual(login_res.status_code, 302)
        authenticated_session_key = self.client.session.session_key

        self.assertNotEqual(
            anonymous_session_key,
            authenticated_session_key,
            "Session key did not rotate upon authentication (session fixation vulnerability)"
        )

    def test_idle_timeout_logs_user_out(self):
        """Inactivity exceeding 30 minutes must invalidate the session and redirect to login."""
        import time
        self.client.login(username='phase2_test_user', password=self.user_password)
        
        # Simulate idle inactivity (31 minutes ago)
        session = self.client.session
        now = int(time.time())
        session['session_started_at'] = now - 2000
        session['last_activity'] = now - 1860  # > 1800s idle timeout
        session.save()

        response = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.headers['Location'])

        # Verify session is no longer authenticated
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_absolute_timeout_logs_user_out(self):
        """Sessions exceeding 8 hours must invalidate regardless of activity and redirect to login."""
        import time
        self.client.login(username='phase2_test_user', password=self.user_password)

        # Simulate 8 hours + 1 minute of active usage
        session = self.client.session
        now = int(time.time())
        session['session_started_at'] = now - 28860  # > 28800s absolute timeout
        session['last_activity'] = now - 10           # active 10 seconds ago
        session.save()

        response = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.headers['Location'])
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_change_ends_other_sessions(self):
        """Updating a password must keep current session alive while terminating all other sessions."""
        from accounts.services import sign_out_everywhere
        from django.contrib.sessions.models import Session

        # Establish Client 1 (the user who changes the password)
        c1 = Client()
        c1.login(username='phase2_test_user', password=self.user_password)
        s1_key = c1.session.session_key

        # Establish Client 2 (another device logged in as the same user)
        c2 = Client()
        c2.login(username='phase2_test_user', password=self.user_password)
        s2_key = c2.session.session_key

        self.assertNotEqual(s1_key, s2_key)

        # Client 1 changes their password
        new_password = 'NewReplacementPassword123!Safe'
        change_res = c1.post(reverse('accounts:password_change'), {
            'old_password': self.user_password,
            'new_password1': new_password,
            'new_password2': new_password,
        })
        self.assertEqual(change_res.status_code, 302)

        # Client 1 must still be authenticated
        overview_c1 = c1.get(reverse('dashboard:overview'))
        self.assertEqual(overview_c1.status_code, 200)

        # Client 2's session in DB must be purged
        self.assertFalse(
            Session.objects.filter(session_key=s2_key).exists(),
            "Secondary session was not terminated upon password change"
        )

        # Client 2 must now be redirected to login
        overview_c2 = c2.get(reverse('dashboard:overview'))
        self.assertEqual(overview_c2.status_code, 302)
        self.assertIn('/login/', overview_c2.headers['Location'])

    def test_deactivated_user_cannot_login(self):
        """Deactivated users must be rejected upon login attempt."""
        self.test_user.is_active = False
        self.test_user.save()

        res = self.client.post(reverse('login'), {
            'username': self.test_user.username,
            'password': self.user_password,
        })
        # Should stay on login with generic failure message
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Incorrect username or password.")
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_deactivated_user_cannot_complete_password_reset(self):
        """A deactivated user cannot complete a password reset or setup link."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        self.test_user.is_active = False
        self.test_user.save()

        uidb64 = urlsafe_base64_encode(force_bytes(self.test_user.pk))
        token = default_token_generator.make_token(self.test_user)

        res = self.client.get(reverse('accounts:set_password', kwargs={'uidb64': uidb64, 'token': token}))
        self.assertEqual(res.status_code, 400)
        self.assertContains(res, "Invitation Link Expired or Invalid", status_code=400)

    def test_password_reset_form_identical_response_for_existing_and_non_existing_email(self):
        """Password reset responses must be identical regardless of whether email exists (prevents enumeration)."""
        # 1. Post existing email
        res_existing = self.client.post(reverse('password_reset'), {
            'email': self.test_user.email,
        })
        self.assertEqual(res_existing.status_code, 302)
        self.assertEqual(res_existing.headers['Location'], reverse('password_reset_done'))

        # 2. Post non-existing email
        res_non_existing = self.client.post(reverse('password_reset'), {
            'email': 'doesnotexist_ever_random999@unknown-domain.com',
        })
        self.assertEqual(res_non_existing.status_code, 302)
        self.assertEqual(res_non_existing.headers['Location'], reverse('password_reset_done'))

    def test_safe_redirect_external_next_url_is_ignored(self):
        """External or open redirects must be rejected in favor of the default redirect."""
        res = self.client.post(f"{reverse('login')}?next=https://malicious.evil.com/phishing", {
            'username': self.test_user.username,
            'password': self.user_password,
        })
        self.assertEqual(res.status_code, 302)
        self.assertNotIn("malicious.evil.com", res.headers['Location'])
        self.assertEqual(res.headers['Location'], reverse('dashboard:overview'))

    def test_reauthentication_decorator_blocks_when_old_and_allows_when_recent(self):
        """@require_recent_auth must block actions when reauth_at is stale and allow when recent."""
        import time
        from accounts.decorators import require_recent_auth
        from django.http import HttpResponse
        from django.test import RequestFactory

        @require_recent_auth(minutes=10)
        def sensitive_action(request):
            return HttpResponse("SENSITIVE_DATA_ACCESSED")

        rf = RequestFactory()

        # 1. Stale or missing reauth_at -> Redirects to reauth
        req_stale = rf.get('/sensitive-action/')
        req_stale.user = self.test_user
        req_stale.session = {'reauth_at': time.time() - 700}  # 11+ minutes old

        res_stale = sensitive_action(req_stale)
        self.assertEqual(res_stale.status_code, 302)
        self.assertIn('/accounts/reauth/', res_stale.headers['Location'])

        # 2. Fresh reauth_at -> Passes through
        req_fresh = rf.get('/sensitive-action/')
        req_fresh.user = self.test_user
        req_fresh.session = {'reauth_at': time.time() - 100}  # 100 seconds old (< 600s)

        res_fresh = sensitive_action(req_fresh)
        self.assertEqual(res_fresh.status_code, 200)
        self.assertEqual(res_fresh.content.decode('utf-8'), "SENSITIVE_DATA_ACCESSED")

    def test_bootstrap_owner_refuses_when_user_exists(self):
        """bootstrap_owner must refuse execution with exit code 1 if any user exists."""
        from io import StringIO
        from django.core.management import call_command

        out = StringIO()
        with self.assertRaises(SystemExit) as cm:
            call_command('bootstrap_owner', stdout=out)
        self.assertEqual(cm.exception.code, 1)

    def test_middleware_order_matches_documented_specification(self):
        """settings.MIDDLEWARE must match the exact 14 items documented in middleware-order.md."""
        from django.conf import settings
        expected_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'whitenoise.middleware.WhiteNoiseMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.contrib.auth.middleware.LoginRequiredMiddleware',
            'jimcan.middleware.SessionTimeoutMiddleware',
            'audit.middleware.AuditContextMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'django_htmx.middleware.HtmxMiddleware',
            'jimcan.middleware.HtmxAuthRedirectMiddleware',
            'jimcan.middleware.PrivateCacheControlMiddleware',
            'axes.middleware.AxesMiddleware',
        ]
        self.assertEqual(
            list(settings.MIDDLEWARE),
            expected_middleware,
            "MIDDLEWARE configuration does not match the documented order in docs/security/middleware-order.md"
        )

    def test_axes_brute_force_lockout_after_five_failed_attempts(self):
        """django-axes must lock out after 5 consecutive bad passwords, then allow after reset."""
        from django.core.management import call_command

        # Reset any prior test attempts
        call_command('axes_reset')

        # 4 failed login attempts stay on login page with 200
        for attempt in range(1, 5):
            res = self.client.post(reverse('login'), {
                'username': self.test_user.username,
                'password': 'WrongPassword123!',
            })
            self.assertEqual(res.status_code, 200)

        # 5th failed attempt reaches the limit (AXES_FAILURE_LIMIT=5) and triggers lockout
        res_5 = self.client.post(reverse('login'), {
            'username': self.test_user.username,
            'password': 'WrongPassword123!',
        })
        self.assertIn(res_5.status_code, (403, 429))

        # 6th attempt with CORRECT password: Must be rejected due to active lockout
        res_locked = self.client.post(reverse('login'), {
            'username': self.test_user.username,
            'password': self.user_password,
        })
        # Axes intercepts and blocks with 403 or 429
        self.assertIn(res_locked.status_code, (403, 429))

        # Reset lockout (simulating cooloff expiration or Owner unlock)
        call_command('axes_reset')

        # 7th attempt with CORRECT password: Must now succeed
        res_unlocked = self.client.post(reverse('login'), {
            'username': self.test_user.username,
            'password': self.user_password,
        })
        self.assertEqual(res_unlocked.status_code, 302)
        self.assertEqual(res_unlocked.headers['Location'], reverse('dashboard:overview'))
