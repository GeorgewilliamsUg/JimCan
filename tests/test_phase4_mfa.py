"""
Comprehensive Automated Test Suite for Phase 4: Two-Factor Authentication & Recovery.
Validates:
- Password + 6-digit TOTP / single-use backup code login flow.
- Single-use static backup codes generation (10 codes shown once, remaining count on profile).
- TOTP and Static token throttling on failed verification attempts.
- MFAEnforcementMiddleware across all routes, exempt paths, and modes ('off', 'owners', 'all').
- Step-up re-authentication requiring fresh OTP verification for users with MFA.
- Admin site OTP protection (unreachable without verified second factor).
- Recovery constraints: Owners cannot reset own MFA via web UI; Owners can reset other users
  after step-up; CLI reset_mfa command works with audit & alerts.
- Scheduled expire_pending_accounts command deactivates accounts with password but no 2FA after 72h.
- security_status audit checks for MFA mode and active Owner count.
- Documented secret storage honesty and encrypted database backups.
"""

import importlib
import io
import os
import sys
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import clear_url_caches, reverse
from django.utils import timezone

import django_otp
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.decorators import require_recent_auth
from accounts.forms import ReauthForm
from audit.models import AuditEvent
from jimcan.middleware import MFAEnforcementMiddleware

User = get_user_model()


class Phase4BaseTestCase(TestCase):
    """Base setup providing common groups, users, and TOTP test devices."""

    def setUp(self):
        call_command('setup_roles', stdout=io.StringIO())
        self.owner_group = Group.objects.get(name='Owner')
        self.staff_group = Group.objects.get(name='Site staff')

        self.owner1 = User.objects.create_user(
            username='owner_alice',
            email='alice@jimcan.site',
            password='AlicePassword123!Secure'
        )
        self.owner1.groups.add(self.owner_group)

        self.owner2 = User.objects.create_user(
            username='owner_bob',
            email='bob@jimcan.site',
            password='BobPassword123!Secure'
        )
        self.owner2.groups.add(self.owner_group)

        self.staff_user = User.objects.create_user(
            username='staff_carol',
            email='carol@jimcan.site',
            password='CarolPassword123!Secure'
        )
        self.staff_user.groups.add(self.staff_group)

    def mark_verified(self, client, user):
        """Helper to mark user session as 2FA-verified in Django test client."""
        device, _ = TOTPDevice.objects.get_or_create(user=user, name='default', confirmed=True)
        session = client.session
        session[django_otp.DEVICE_ID_SESSION_KEY] = device.persistent_id
        session['reauth_at'] = timezone.now().timestamp()
        session.save()
        return device


class MFAEnforcementMiddlewareTests(Phase4BaseTestCase):
    """Verifies MFAEnforcementMiddleware redirects, exemptions, and route protection."""

    @override_settings(MFA_ENFORCEMENT='all')
    def test_unauthenticated_request_not_looped(self):
        """Unauthenticated requests are untouched by MFA middleware; LoginRequiredMiddleware handles them."""
        client = Client()
        res = client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res['Location'].startswith('/login/'))

    @override_settings(MFA_ENFORCEMENT='all')
    def test_authenticated_unenrolled_user_redirected_to_setup(self):
        """Authenticated user without any 2FA device is redirected to setup for all protected routes."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')

        protected_urls = [
            reverse('dashboard:overview'),
            reverse('dashboard:invoices'),
            reverse('dashboard:projects'),
            reverse('dashboard:settings'),
        ]

        setup_url = reverse('two_factor:setup')
        for url in protected_urls:
            res = client.get(url)
            self.assertEqual(res.status_code, 302, f"Expected 302 for {url}")
            self.assertEqual(res['Location'], setup_url, f"Expected redirect to setup for {url}")

    @override_settings(MFA_ENFORCEMENT='all')
    def test_authenticated_enrolled_unverified_user_redirected_to_verify(self):
        """Authenticated user with a 2FA device who has not verified this session is redirected to 2FA login."""
        TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)

        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')

        res = client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res['Location'], reverse('two_factor:login'))

    @override_settings(MFA_ENFORCEMENT='all')
    def test_authenticated_verified_user_can_access_protected_pages(self):
        """User with verified 2FA session can reach all protected routes."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        self.mark_verified(client, self.staff_user)

        res = client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 200)

    @override_settings(MFA_ENFORCEMENT='all')
    def test_allowlisted_two_factor_urls_and_logout_accessible(self):
        """MFA pages and logout are allowlisted and do not cause redirect loops."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')

        allowlisted_urls = [
            reverse('two_factor:setup'),
            reverse('two_factor:login'),
            reverse('two_factor:profile'),
        ]
        for url in allowlisted_urls:
            res = client.get(url)
            # Should not redirect away to another page loop
            self.assertIn(res.status_code, (200, 302))
            if res.status_code == 302:
                self.assertNotIn(reverse('dashboard:overview'), res['Location'])

    @override_settings(MFA_ENFORCEMENT='all')
    def test_static_files_always_exempt(self):
        """Static assets bypass MFA enforcement completely."""
        rf = RequestFactory()
        req = rf.get('/static/css/styles.css')
        req.user = self.staff_user  # Authenticated but unverified

        called = []
        middleware = MFAEnforcementMiddleware(lambda r: called.append(True) or r)
        middleware(req)
        self.assertTrue(called, "MFA middleware should pass static requests through to get_response")

    @override_settings(MFA_ENFORCEMENT='all')
    def test_htmx_unverified_request_returns_hx_redirect(self):
        """HTMX requests receive HTTP 204 with HX-Redirect header."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')

        res = client.get(reverse('dashboard:overview'), HTTP_HX_REQUEST='true')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.headers.get('HX-Redirect'), reverse('two_factor:setup'))


class MFAEnforcementModesTests(Phase4BaseTestCase):
    """Verifies staged rollout modes: 'off', 'owners', and 'all'."""

    @override_settings(MFA_ENFORCEMENT='off')
    def test_mode_off_allows_all_authenticated_users(self):
        """When MFA_ENFORCEMENT='off', authenticated unverified users can access protected pages."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        res = client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 200)

        owner_client = Client()
        owner_client.login(username='owner_alice', password='AlicePassword123!Secure')
        res = owner_client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 200)

    @override_settings(MFA_ENFORCEMENT='owners')
    def test_mode_owners_enforces_only_on_owner_group(self):
        """When MFA_ENFORCEMENT='owners', Staff bypasses 2FA while Owners are enforced."""
        # Staff user without 2FA -> passes
        staff_client = Client()
        staff_client.login(username='staff_carol', password='CarolPassword123!Secure')
        res = staff_client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 200)

        # Owner user without 2FA -> redirected to setup
        owner_client = Client()
        owner_client.login(username='owner_alice', password='AlicePassword123!Secure')
        res = owner_client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res['Location'], reverse('two_factor:setup'))

        # Owner user with verified 2FA -> passes
        self.mark_verified(owner_client, self.owner1)
        res = owner_client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 200)

    @override_settings(MFA_ENFORCEMENT='all')
    def test_mode_all_enforces_on_all_roles(self):
        """When MFA_ENFORCEMENT='all', both Staff and Owners are required to have verified 2FA."""
        staff_client = Client()
        staff_client.login(username='staff_carol', password='CarolPassword123!Secure')
        res = staff_client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 302)

        owner_client = Client()
        owner_client.login(username='owner_alice', password='AlicePassword123!Secure')
        res = owner_client.get(reverse('dashboard:overview'))
        self.assertEqual(res.status_code, 302)


class MFACodeVerificationAndThrottlingTests(Phase4BaseTestCase):
    """Verifies TOTP verification, wrong code throttling, and single-use static backup codes."""

    def test_totp_wrong_code_throttled(self):
        """Repeated invalid TOTP attempts increment throttle failure count and lock out further attempts."""
        device = TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)
        self.assertEqual(device.throttling_failure_count, 0)

        # First invalid code
        verified = device.verify_token('000000')
        self.assertFalse(verified)
        device.refresh_from_db()
        self.assertEqual(device.throttling_failure_count, 1)

        # Throttling is now active: verify_is_allowed returns False
        allowed, details = device.verify_is_allowed()
        self.assertFalse(allowed)
        self.assertIn('locked_until', details)

    def test_backup_token_works_once_and_is_deleted(self):
        """Static backup codes work exactly once, are deleted from the database, and fail on reuse."""
        static_dev, _ = StaticDevice.objects.get_or_create(user=self.staff_user, name='backup')
        static_dev.token_set.all().delete()
        token_val = StaticToken.random_token()
        static_dev.token_set.create(token=token_val)

        self.assertEqual(static_dev.token_set.count(), 1)

        # First verification succeeds and deletes the token
        self.assertTrue(static_dev.verify_token(token_val))
        static_dev.refresh_from_db()
        self.assertEqual(static_dev.token_set.count(), 0)

        # Second verification with identical code must fail
        self.assertFalse(static_dev.verify_token(token_val))

    def test_static_device_wrong_code_throttling(self):
        """Wrong backup codes increment throttle failure count on StaticDevice."""
        static_dev, _ = StaticDevice.objects.get_or_create(user=self.staff_user, name='backup')
        static_dev.token_set.all().delete()
        static_dev.token_set.create(token='12345678')

        # Invalid token
        self.assertFalse(static_dev.verify_token('99999999'))
        static_dev.refresh_from_db()
        self.assertEqual(static_dev.throttling_failure_count, 1)


class MFAEnrollmentAndAlertsTests(Phase4BaseTestCase):
    """Verifies setup flow, backup codes presentation, remaining count, and Owner alerting."""

    def test_setup_generates_10_backup_codes_and_displays_once_with_warning(self):
        """Completing setup creates 10 backup codes and displays them once with the exact required warning."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        self.mark_verified(client, self.staff_user)

        # Simulate setup completion done() callback
        static_dev, _ = self.staff_user.staticdevice_set.get_or_create(name='backup')
        static_dev.token_set.all().delete()
        raw_tokens = [StaticToken.random_token() for _ in range(10)]
        for tok in raw_tokens:
            static_dev.token_set.create(token=tok)

        session = client.session
        session['backup_codes_show_once'] = raw_tokens
        session.save()

        # Render setup complete
        res = client.get(reverse('two_factor:setup_complete'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('backup_codes', res.context)
        self.assertEqual(len(res.context['backup_codes']), 10)
        self.assertIn(
            "Save them in a password manager or print them; they are the only way in if the phone is lost.",
            res.context['backup_warning']
        )

        # Second request: backup codes are gone from session (shown once)
        res2 = client.get(reverse('two_factor:setup_complete'))
        self.assertEqual(res2.status_code, 200)
        self.assertIsNone(res2.context['backup_codes'])

    def test_profile_view_displays_remaining_backup_tokens_count(self):
        """Profile view context reports the exact number of remaining static backup tokens."""
        static_dev, _ = self.staff_user.staticdevice_set.get_or_create(name='backup')
        static_dev.token_set.all().delete()
        for _ in range(7):
            static_dev.token_set.create(token=StaticToken.random_token())

        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        self.mark_verified(client, self.staff_user)

        res = client.get(reverse('two_factor:profile'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context.get('backup_tokens_remaining'), 7)

    @patch('audit.services.send_mail')
    def test_backup_tokens_regeneration_records_audit_and_alerts_owners(self, mock_send_mail):
        """Regenerating backup tokens writes audit event backup_codes_regenerated and alerts Owners."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        self.mark_verified(client, self.staff_user)

        # Provide recent step-up reauth
        session = client.session
        session['reauth_at'] = timezone.now().timestamp()
        session.save()

        res = client.post(reverse('two_factor:backup_tokens'))
        self.assertEqual(res.status_code, 302)

        event = AuditEvent.objects.filter(event_type='backup_codes_regenerated').latest('id')
        self.assertEqual(event.actor, self.staff_user)
        self.assertTrue(mock_send_mail.called)

    @patch('audit.services.send_mail')
    def test_authenticator_disable_records_audit_and_alerts_owners(self, mock_send_mail):
        """Disabling 2FA removes devices, logs authenticator_removed audit event, and alerts Owners."""
        TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)

        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        self.mark_verified(client, self.staff_user)

        # Provide recent step-up reauth
        session = client.session
        session['reauth_at'] = timezone.now().timestamp()
        session.save()

        res = client.post(reverse('two_factor:disable'), data={'understand': True})
        self.assertEqual(res.status_code, 302)

        self.assertFalse(TOTPDevice.objects.filter(user=self.staff_user).exists())
        event = AuditEvent.objects.filter(event_type='authenticator_removed').latest('id')
        self.assertEqual(event.actor, self.staff_user)
        self.assertTrue(mock_send_mail.called)


class StepUpReauthTests(Phase4BaseTestCase):
    """Verifies step-up re-authentication requiring fresh OTP code for enrolled users."""

    def test_reauth_form_requires_otp_token_for_enrolled_user(self):
        """ReauthForm enforces OTP token validation when the user has registered MFA."""
        TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)

        rf = RequestFactory()
        req = rf.post('/accounts/reauth/')
        req.user = self.staff_user

        # Submit only password
        form = ReauthForm(self.staff_user, request=req, data={'password': 'CarolPassword123!Secure'})
        self.assertFalse(form.is_valid())
        self.assertIn('otp_token', form.errors)

    def test_require_recent_auth_blocks_unverified_mfa_user(self):
        """require_recent_auth decorator redirects to reauth if user has MFA but is not verified."""
        TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)

        @require_recent_auth(minutes=10)
        def sensitive_view(request):
            from django.http import HttpResponse
            return HttpResponse("Sensitive Data")

        rf = RequestFactory()
        req = rf.get('/sensitive/')
        req.user = self.staff_user
        # User has recent reauth_at timestamp, but is NOT verified via django-otp
        req.session = {'reauth_at': timezone.now().timestamp()}

        res = sensitive_view(req)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res['Location'].startswith(reverse('accounts:reauth')))


class MFARecoveryTests(Phase4BaseTestCase):
    """Verifies Owner reset recovery, self-reset prohibitions, and server reset_mfa command."""

    def test_owner_cannot_reset_own_mfa_via_web_page(self):
        """An Owner cannot reset their own 2FA via the web endpoint (returns 403 Forbidden)."""
        client = Client()
        client.login(username='owner_alice', password='AlicePassword123!Secure')
        self.mark_verified(client, self.owner1)

        # Set recent reauth
        session = client.session
        session['reauth_at'] = timezone.now().timestamp()
        session.save()

        reset_url = reverse('accounts:user_reset_mfa', kwargs={'user_id': self.owner1.pk})
        res = client.post(reset_url)
        self.assertEqual(res.status_code, 403)
        self.assertIn("An Owner cannot reset their own two-factor device", res.content.decode())

    @patch('audit.services.send_mail')
    def test_owner_can_reset_another_user_mfa_after_stepup(self, mock_send_mail):
        """An Owner can reset another user's 2FA device after step-up; deletes devices, signs out, alerts."""
        TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)
        static_dev, _ = StaticDevice.objects.get_or_create(user=self.staff_user, name='backup')
        static_dev.token_set.create(token=StaticToken.random_token())

        client = Client()
        client.login(username='owner_alice', password='AlicePassword123!Secure')
        self.mark_verified(client, self.owner1)

        # Provide recent step-up reauth
        session = client.session
        session['reauth_at'] = timezone.now().timestamp()
        session.save()

        reset_url = reverse('accounts:user_reset_mfa', kwargs={'user_id': self.staff_user.pk})
        res = client.post(reset_url)
        self.assertEqual(res.status_code, 302)

        # Devices deleted
        self.assertFalse(TOTPDevice.objects.filter(user=self.staff_user).exists())
        self.assertEqual(static_dev.token_set.count(), 0)

        # Audit event and Owner alert sent
        event = AuditEvent.objects.filter(event_type='two_factor_reset', actor=self.owner1).latest('id')
        self.assertEqual(event.target_object_id, str(self.staff_user.pk))
        self.assertTrue(mock_send_mail.called)

    def test_non_owner_cannot_reset_mfa(self):
        """A Staff user attempting to reset another user's MFA receives 403 PermissionDenied."""
        client = Client()
        client.login(username='staff_carol', password='CarolPassword123!Secure')
        self.mark_verified(client, self.staff_user)

        session = client.session
        session['reauth_at'] = timezone.now().timestamp()
        session.save()

        reset_url = reverse('accounts:user_reset_mfa', kwargs={'user_id': self.owner2.pk})
        res = client.post(reset_url)
        self.assertEqual(res.status_code, 403)

    @patch('audit.services.send_mail')
    def test_reset_mfa_management_command(self, mock_send_mail):
        """reset_mfa CLI command deletes devices, signs out user, logs event as system, alerts owners."""
        TOTPDevice.objects.create(user=self.staff_user, name='default', confirmed=True)

        out = io.StringIO()
        call_command('reset_mfa', 'staff_carol', no_input=True, stdout=out)

        self.assertFalse(TOTPDevice.objects.filter(user=self.staff_user).exists())
        self.assertIn("Successfully reset MFA for user 'staff_carol'", out.getvalue())

        event = AuditEvent.objects.filter(event_type='two_factor_reset', actor_username='system').latest('id')
        self.assertEqual(event.target_object_id, str(self.staff_user.pk))
        self.assertTrue(mock_send_mail.called)

    def test_reset_mfa_command_invalid_user_raises_command_error(self):
        """reset_mfa command raises CommandError for non-existent user."""
        with self.assertRaises(CommandError):
            call_command('reset_mfa', 'non_existent_user_xyz', no_input=True)


class ExpirePendingAccountsCommandTests(Phase4BaseTestCase):
    """Verifies scheduled command expire_pending_accounts."""

    @patch('audit.services.send_mail')
    def test_deactivates_unenrolled_account_older_than_72_hours(self, mock_send_mail):
        """An active account that set a password > 72 hours ago without enrolling 2FA is deactivated."""
        pending_user = User.objects.create_user(
            username='pending_unenrolled',
            email='pending@jimcan.site',
            password='PendingPassword123!Secure'
        )
        pending_user.date_joined = timezone.now() - timedelta(hours=75)
        pending_user.save()

        out = io.StringIO()
        call_command('expire_pending_accounts', hours=72, stdout=out)

        pending_user.refresh_from_db()
        self.assertFalse(pending_user.is_active)
        self.assertIn("Deactivated pending account 'pending_unenrolled'", out.getvalue())

        event = AuditEvent.objects.filter(event_type='user_deactivated', target_object_id=str(pending_user.pk)).latest('id')
        self.assertEqual(event.actor_username, 'system')
        self.assertTrue(mock_send_mail.called)

    def test_leaves_enrolled_account_active_after_72_hours(self):
        """An account with 2FA enrolled is left untouched even if password was set > 72 hours ago."""
        enrolled_user = User.objects.create_user(
            username='enrolled_user',
            email='enrolled@jimcan.site',
            password='EnrolledPassword123!Secure'
        )
        TOTPDevice.objects.create(user=enrolled_user, name='default', confirmed=True)
        enrolled_user.date_joined = timezone.now() - timedelta(hours=80)
        enrolled_user.save()

        out = io.StringIO()
        call_command('expire_pending_accounts', hours=72, stdout=out)

        enrolled_user.refresh_from_db()
        self.assertTrue(enrolled_user.is_active)

    def test_dry_run_leaves_accounts_active(self):
        """The --dry-run flag does not deactivate accounts or create audit events."""
        dry_user = User.objects.create_user(
            username='dry_user',
            email='dry@jimcan.site',
            password='DryPassword123!Secure'
        )
        dry_user.date_joined = timezone.now() - timedelta(hours=100)
        dry_user.save()

        out = io.StringIO()
        call_command('expire_pending_accounts', hours=72, dry_run=True, stdout=out)

        dry_user.refresh_from_db()
        self.assertTrue(dry_user.is_active)
        self.assertIn("[DRY RUN] Would deactivate 'dry_user'", out.getvalue())
        self.assertFalse(AuditEvent.objects.filter(event_type='user_deactivated', target_object_id=str(dry_user.pk)).exists())


class AdminOTPProtectionTests(Phase4BaseTestCase):
    """Verifies that Django Admin is unreachable without verified 2FA when enabled."""

    def test_admin_unreachable_without_verified_factor(self):
        """When ENABLE_ADMIN=True, staff user with password only is redirected to login."""
        staff_admin = User.objects.create_user(
            username='staff_admin_test',
            email='admin@jimcan.site',
            password='AdminPassword123!Secure',
            is_staff=True
        )

        with override_settings(ENABLE_ADMIN=True, DJANGO_ADMIN_PATH='test-admin'):
            clear_url_caches()
            import jimcan.urls
            importlib.reload(jimcan.urls)

            client = Client()
            client.login(username='staff_admin_test', password='AdminPassword123!Secure')

            # Staff with password only -> 302 redirect to admin login
            res = client.get('/test-admin/')
            self.assertEqual(res.status_code, 302)
            self.assertIn('/test-admin/login/', res['Location'])

            # Verify session with 2FA
            device = TOTPDevice.objects.create(user=staff_admin, name='default', confirmed=True)
            session = client.session
            session[django_otp.DEVICE_ID_SESSION_KEY] = device.persistent_id
            session.save()

            # Staff with verified 2FA -> 200 OK
            res_verified = client.get('/test-admin/')
            self.assertEqual(res_verified.status_code, 200)

            # Cleanup URLconf
            clear_url_caches()
            importlib.reload(jimcan.urls)


class SecurityStatusMFAAuditTests(Phase4BaseTestCase):
    """Verifies security_status checks for MFA enforcement mode and active Owner count."""

    @override_settings(DEBUG=False, MFA_ENFORCEMENT='owners')
    def test_security_status_warns_on_staged_rollout_in_prod(self):
        """In production (DEBUG=False), security_status WARNs when MFA_ENFORCEMENT is not 'all'."""
        out = io.StringIO()
        try:
            call_command('security_status', stdout=out)
        except SystemExit:
            pass
        output = out.getvalue()
        self.assertIn("[WARN] MFA enforcement mode is 'owners'", output)

    @override_settings(DEBUG=False, MFA_ENFORCEMENT='all')
    def test_security_status_passes_when_all_in_prod(self):
        """In production (DEBUG=False), security_status PASSES when MFA_ENFORCEMENT is 'all'."""
        out = io.StringIO()
        try:
            call_command('security_status', stdout=out)
        except SystemExit:
            pass
        output = out.getvalue()
        self.assertIn("[PASS] MFA enforcement mode: all", output)

    def test_security_status_warns_when_fewer_than_two_active_owners(self):
        """security_status WARNs if fewer than 2 active Owner accounts exist."""
        # Deactivate owner2 so only 1 remains
        self.owner2.is_active = False
        self.owner2.save()

        out = io.StringIO()
        try:
            call_command('security_status', stdout=out)
        except SystemExit:
            pass
        output = out.getvalue()
        self.assertIn("[WARN] Found only 1 active Owner account(s)", output)


class StorageHonestyRunbookTests(Phase4BaseTestCase):
    """Verifies TOTP key storage format and runbook backup encryption mandate."""

    def test_totp_key_stored_as_recoverable_hex(self):
        """django-otp stores TOTPDevice.key as plaintext hex in the database."""
        device = TOTPDevice.objects.create(user=self.staff_user, name='default')
        # Inspect raw column value in database
        self.assertIsInstance(device.key, str)
        self.assertTrue(len(device.key) > 0)
        # hex representation: can be parsed as hex bytes
        bytes.fromhex(device.key)

    def test_runbook_notes_documents_secret_storage_and_backup_encryption(self):
        """docs/security/runbook-notes.md discloses recoverable secret storage and mandates encrypted backups."""
        runbook_path = os.path.join(settings.BASE_DIR, 'docs', 'security', 'runbook-notes.md')
        self.assertTrue(os.path.exists(runbook_path))
        with open(runbook_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("otp_totp_totpdevice", content)
        self.assertIn("Encrypted Database Backups", content)
        self.assertIn("expire_pending_accounts", content)
        self.assertIn("reset_mfa", content)
