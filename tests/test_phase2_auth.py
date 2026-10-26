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
        self.admin_user = User.objects.create_superuser(
            username='admin_boss',
            email='admin@jimcan.co.ug',
            password='AdminPassword123!'
        )

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
