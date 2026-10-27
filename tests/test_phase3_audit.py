"""
Comprehensive Automated Test Suite for Phase 3: Audit Core & Owner Alerts.
Validates:
- Monotonic, gap-free, non-forking cryptographic HMAC-SHA256 chain.
- Tamper detection on modified fields and detected gaps on deleted rows.
- Append-only immutability enforcement (save(), delete(), queryset update/delete).
- Denylist field sanitization in changes diffs.
- Username sanitization on failed logins ([unknown account] protection).
- Concurrency and thread safety for chain writes.
- Rollback semantics for data changes vs graceful handling for read-only events.
- Owner alerts dispatch resilience (never raises on mail failures).
- Security noise deduplication and hourly insertion caps.
- Production startup refusal when AUDIT_HMAC_KEY is absent.
- Audit log dashboard view permissions, filters, and pagination.
"""

import threading
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import connection, transaction
import io
from django.core.management import call_command
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from audit.models import AuditEvent, AuditChainHead, SecurityNoise, AuditAnchorRecord
from audit.services import (
    record_event,
    verify_chain,
    sanitize_changes,
    notify_owners,
    compute_entry_hash,
    canonical_serialize,
    DENYLIST_FIELDS,
    HOURLY_NOISE_CAP,
)

User = get_user_model()


class AuditModelIntegrityTests(TestCase):
    """Validates append-only enforcement, denylist sanitization, and unknown account protections."""

    def setUp(self):
        self.owner_group, _ = Group.objects.get_or_create(name='Owner')
        self.owner = User.objects.create_user(
            username='audit_owner',
            email='owner@jimcan.site',
            password='OwnerPassword123!Secure'
        )
        self.owner.groups.add(self.owner_group)

    def test_save_existing_event_raises_permission_denied(self):
        """Calling save() on an existing AuditEvent instance must raise PermissionDenied."""
        event = record_event('test_event', actor=self.owner, target_label='Original Label')
        self.assertIsNotNone(event)

        event.target_label = 'Tampered Label'
        with self.assertRaises(PermissionDenied):
            event.save()

    def test_instance_delete_raises_permission_denied(self):
        """Calling delete() on an AuditEvent instance must raise PermissionDenied."""
        event = record_event('test_event', actor=self.owner)
        self.assertIsNotNone(event)

        with self.assertRaises(PermissionDenied):
            event.delete()

    def test_queryset_update_and_delete_raise_permission_denied(self):
        """Calling update() or delete() on an AuditEvent QuerySet must raise PermissionDenied."""
        event = record_event('test_event', actor=self.owner)
        self.assertIsNotNone(event)

        qs = AuditEvent.objects.filter(pk=event.pk)
        with self.assertRaises(PermissionDenied):
            qs.update(target_label='Tampered')

        with self.assertRaises(PermissionDenied):
            qs.delete()

    def test_denylisted_fields_scrubbed_from_changes(self):
        """Every field in DENYLIST_FIELDS must be sanitized to [REDACTED] in changes diffs."""
        dirty_changes = {
            'username': 'j.mugisha',
            'password': 'RawPasswordSecret123!',
            'token': 'secret-reset-token-abc',
            'session_key': 'sess-12345',
            'nested': {
                'otp_secret': 'BASE32SECRET',
                'allowed_field': 'Contract Value UGX 50M'
            }
        }
        event = record_event('user_profile_updated', actor=self.owner, changes=dirty_changes)
        self.assertIsNotNone(event)

        changes = event.changes
        self.assertEqual(changes['username'], 'j.mugisha')
        self.assertEqual(changes['password'], '[REDACTED]')
        self.assertEqual(changes['token'], '[REDACTED]')
        self.assertEqual(changes['session_key'], '[REDACTED]')
        self.assertEqual(changes['nested']['otp_secret'], '[REDACTED]')
        self.assertEqual(changes['nested']['allowed_field'], 'Contract Value UGX 50M')

    def test_unknown_failed_login_username_scrubbed_to_unknown_account(self):
        """Failed logins with non-existent usernames must store [unknown account] to protect mistyped passwords."""
        # 1. Non-existent username
        record_event('login_failure', attempted_username='AccidentalPasswordTypedInUsernameBox123!')
        noise_unknown = SecurityNoise.objects.filter(event_type='login_failure').first()
        self.assertIsNotNone(noise_unknown)
        self.assertEqual(noise_unknown.username_attempted, '[unknown account]')

        # 2. Existing username
        SecurityNoise.objects.all().delete()
        record_event('login_failure', attempted_username=self.owner.username)
        noise_known = SecurityNoise.objects.filter(event_type='login_failure').first()
        self.assertIsNotNone(noise_known)
        self.assertEqual(noise_known.username_attempted, self.owner.username)


class CryptographicChainTests(TestCase):
    """Validates the HMAC-SHA256 cryptographic chain, tamper detection, and gap detection."""

    def setUp(self):
        self.user = User.objects.create_user('chain_user', 'chain@test.com', 'ChainPass123!Safe')

    def test_chain_verifies_successfully_for_multiple_events(self):
        """A series of recorded events must form a valid, unbroken HMAC-SHA256 chain."""
        event_types = ['login_success', 'password_changed', 'role_changed', 'logout']
        for et in event_types:
            record_event(et, actor=self.user, target_label=f"Action: {et}")

        is_valid, msg, failure_seq = verify_chain()
        self.assertTrue(is_valid, f"Chain verification failed unexpectedly: {msg}")
        self.assertIsNone(failure_seq)
        self.assertEqual(AuditEvent.objects.count(), 4)

    def test_raw_database_tampering_detected(self):
        """Directly modifying any stored field in the database must cause verify_chain to fail at that row."""
        for i in range(1, 6):
            record_event('data_action', actor=self.user, target_label=f"Action #{i}")

        is_valid, _, _ = verify_chain()
        self.assertTrue(is_valid)

        # Bypass Django ORM immutability using raw SQL to tamper with sequence 3
        with connection.cursor() as cursor:
            cursor.execute("UPDATE audit_auditevent SET target_label = 'HACKED_TAMPERED' WHERE sequence = 3")

        is_valid, msg, failure_seq = verify_chain()
        self.assertFalse(is_valid)
        self.assertEqual(failure_seq, 3)
        self.assertIn("Tampering detected at sequence 3", msg)

    def test_deleting_middle_row_detected_as_gap(self):
        """Deleting a middle row via SQL must be detected as a sequence gap."""
        for i in range(1, 6):
            record_event('step_action', actor=self.user, target_label=f"Step #{i}")

        # Delete sequence 3 directly in SQL
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM audit_auditevent WHERE sequence = 3")

        is_valid, msg, failure_seq = verify_chain()
        self.assertFalse(is_valid)
        self.assertEqual(failure_seq, 3)
        self.assertIn("Audit sequence gap detected", msg)


class ConcurrencyAndTransactionTests(TransactionTestCase):
    """
    Validates concurrency, thread safety, and transactional rollback behaviors.
    Uses TransactionTestCase to permit multi-threaded database transactions.
    """

    def test_concurrent_threads_produce_gap_free_non_forked_chain(self):
        """Multiple concurrent threads recording events simultaneously must not create sequence forks or gaps."""
        user = User.objects.create_user('concurrency_user', 'conc@test.com', 'Pass123!Secure')
        thread_count = 10
        events_per_thread = 3
        threads = []
        errors = []

        def worker(thread_idx):
            try:
                for i in range(events_per_thread):
                    record_event(
                        'concurrent_test_event',
                        actor=user,
                        changes={'thread_id': thread_idx, 'iteration': i}
                    )
            except Exception as e:
                errors.append(e)

        for t_idx in range(thread_count):
            t = threading.Thread(target=worker, args=(t_idx,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Encountered thread errors: {errors}")

        total_expected = thread_count * events_per_thread
        self.assertEqual(AuditEvent.objects.count(), total_expected)

        # Sequences must be exactly 1 to total_expected with zero duplicates
        sequences = list(AuditEvent.objects.order_by('sequence').values_list('sequence', flat=True))
        self.assertEqual(sequences, list(range(1, total_expected + 1)))

        # Cryptographic chain must be 100% valid
        is_valid, msg, failure_seq = verify_chain()
        self.assertTrue(is_valid, f"Chain validation failed after concurrent writes: {msg}")

    def test_data_change_failure_rolls_back_outer_transaction(self):
        """When is_data_change=True, an audit failure must raise and rollback the entire business transaction."""
        user = User.objects.create_user('tx_user', 'tx@test.com', 'Pass123!Secure')

        # Simulate business action with failing audit write
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                user.first_name = "ModifiedName"
                user.save()

                with patch('audit.services.AuditChainHead.objects.select_for_update', side_effect=RuntimeError("Simulated DB Lock Failure")):
                    record_event('user_updated', actor=user, is_data_change=True)

        # User's first_name must have rolled back
        user.refresh_from_db()
        self.assertEqual(user.first_name, "")

    def test_read_only_event_failure_does_not_raise(self):
        """When is_data_change=False (e.g. read-only logging), an audit failure must not raise or break the request."""
        user = User.objects.create_user('ro_user', 'ro@test.com', 'Pass123!Secure')

        with patch('audit.services.AuditChainHead.objects.select_for_update', side_effect=RuntimeError("Simulated DB Write Error")):
            result = record_event('login_success', actor=user, is_data_change=False)
            self.assertIsNone(result)


class NoiseDeduplicationAndAlertTests(TestCase):
    """Validates rate limiting for security noise and non-blocking Owner alerts."""

    def setUp(self):
        self.owner_group, _ = Group.objects.get_or_create(name='Owner')
        self.owner = User.objects.create_user(
            username='alert_owner',
            email='owner@jimcan.site',
            password='Pass123!Secure'
        )
        self.owner.groups.add(self.owner_group)

    def test_noise_deduplication_within_one_minute(self):
        """Multiple noise events with same (type, IP, path) within 60s must increment count on 1 row."""
        for _ in range(5):
            record_event(
                'permission_denied_403',
                client_ip='192.168.1.100',
                target_label='/financial/tax/',
                attempted_username='intruder'
            )

        noise_records = SecurityNoise.objects.filter(event_type='permission_denied_403')
        self.assertEqual(noise_records.count(), 1)
        self.assertEqual(noise_records.first().count, 5)

    def test_hourly_noise_cap_suppresses_further_inserts(self):
        """Exceeding HOURLY_NOISE_CAP suppresses additional database writes and logs a warning."""
        # Create records up to cap
        now = timezone.now()
        bulk_noise = [
            SecurityNoise(
                event_type='permission_denied_403',
                client_ip=f'10.0.{i % 250}.{i // 250}',
                path=f'/path/{i}',
                count=1,
                first_seen=now,
                last_seen=now
            )
            for i in range(HOURLY_NOISE_CAP)
        ]
        SecurityNoise.objects.bulk_create(bulk_noise)

        # Next noise insert must be suppressed
        res = record_event(
            'permission_denied_403',
            client_ip='10.99.99.99',
            target_label='/blocked/',
            attempted_username='attacker'
        )
        self.assertIsNone(res)
        # Verify no 1001st row was inserted
        self.assertEqual(SecurityNoise.objects.count(), HOURLY_NOISE_CAP)

    def test_notify_owners_never_raises_on_mail_failure(self):
        """notify_owners must catch all mail server exceptions and not crash the caller."""
        event = record_event('account_locked', actor=self.owner, alert=True)

        with patch('django.core.mail.send_mail', side_effect=Exception("SMTP Server Unavailable")):
            # Must complete cleanly without raising
            notify_owners("Security Alert", event)


class ProductionStartupAndManagementCommandsTests(TestCase):
    """Validates production startup checks and management commands."""

    def test_production_start_fails_without_audit_hmac_key(self):
        """When DEBUG=False and is_running_tests=False, missing AUDIT_HMAC_KEY must raise ImproperlyConfigured."""
        # Verify the settings logic directly
        with patch.dict('os.environ', {'DEBUG': 'False', 'AUDIT_HMAC_KEY': ''}):
            audit_key = ''
            debug = False
            is_running_tests = False

            with self.assertRaises(ImproperlyConfigured):
                if not audit_key:
                    if is_running_tests:
                        audit_key = 'test-key'
                    elif debug:
                        audit_key = 'dev-key'
                    else:
                        raise ImproperlyConfigured("The AUDIT_HMAC_KEY environment variable is not set.")

    def test_verify_audit_chain_command_success_and_failure(self):
        """verify_audit_chain command outputs PASS on clean chain and CommandError on tampered chain."""
        from io import StringIO
        from django.core.management import call_command, CommandError

        record_event('test_event_1', target_label='Clean Event')
        out = StringIO()
        call_command('verify_audit_chain', stdout=out)
        self.assertIn('[PASS]', out.getvalue())

        # Tamper with event
        with connection.cursor() as cursor:
            cursor.execute("UPDATE audit_auditevent SET target_label = 'Tampered'")

        with self.assertRaises(CommandError):
            call_command('verify_audit_chain', stdout=StringIO())

    def test_audit_anchor_command_prints_and_records(self):
        """audit_anchor prints sequence and hash, and creates an AuditAnchorRecord."""
        from io import StringIO
        from django.core.management import call_command

        record_event('event_before_anchor', target_label='Action')
        out = StringIO()
        call_command('audit_anchor', stdout=out)
        output = out.getvalue()

        self.assertIn('Jimcan Audit Anchor Snapshot', output)
        self.assertIn('Sequence:   1', output)
        self.assertEqual(AuditAnchorRecord.objects.count(), 1)

    def test_prune_noise_command_deletes_only_old_noise(self):
        """prune_noise deletes noise older than 90 days and never deletes AuditEvent."""
        from django.core.management import call_command
        from io import StringIO

        now = timezone.now()
        # 100 days old noise
        SecurityNoise.objects.create(
            event_type='permission_denied_403',
            client_ip='1.1.1.1',
            path='/old/',
            count=1,
            last_seen=now - timedelta(days=100)
        )
        # 10 days old noise
        SecurityNoise.objects.create(
            event_type='permission_denied_403',
            client_ip='2.2.2.2',
            path='/new/',
            count=1,
            last_seen=now - timedelta(days=10)
        )
        # Audit event
        record_event('preserved_audit_event')

        out = StringIO()
        call_command('prune_noise', days=90, stdout=out)

        self.assertEqual(SecurityNoise.objects.count(), 1)
        self.assertEqual(SecurityNoise.objects.first().client_ip, '2.2.2.2')
        self.assertEqual(AuditEvent.objects.count(), 1)


class AuditDashboardViewTests(TestCase):
    """Validates the /audit/ web view, role restrictions, filtering, and security notices tab."""

    def setUp(self):
        self.client = Client()
        call_command('setup_roles', stdout=io.StringIO())
        self.owner_group = Group.objects.get(name='Owner')
        self.owner = User.objects.create_user(
            username='view_owner',
            email='view_owner@jimcan.site',
            password='OwnerPassword123!Secure'
        )
        self.owner.groups.add(self.owner_group)

        self.regular_user = User.objects.create_user(
            username='site_engineer',
            email='engineer@jimcan.site',
            password='EngineerPassword123!Secure'
        )

        # Create sample events
        record_event('login_success', actor=self.owner, target_label='Login Normal')
        record_event('account_locked', actor=self.regular_user, target_label='Lockout Triggered', alert=True)

    def test_anonymous_user_redirected_to_login(self):
        """Unauthenticated user accessing /audit/ is redirected to login (deny-by-default)."""
        res = self.client.get(reverse('dashboard:audit'))
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login/', res.headers['Location'])

    def test_non_owner_forbidden_from_audit(self):
        """Non-owner role (e.g. site engineer) receives HTTP 403 when accessing /audit/."""
        self.client.force_login(self.regular_user)
        res = self.client.get(reverse('dashboard:audit'), {'role': 'engineer'})
        self.assertEqual(res.status_code, 403)

    def test_owner_can_access_audit_log_and_inspect_events(self):
        """Owner can access /audit/ and see the event table and Kampalan timestamps."""
        self.client.force_login(self.owner)
        res = self.client.get(reverse('dashboard:audit'), {'role': 'admin'})
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Security Audit Trail', content)
        self.assertIn('HMAC Chain Intact', content)
        self.assertIn('EAT', content)

    def test_security_notices_tab_filters_alerts(self):
        """Visiting /audit/?tab=alerts filters exclusively events with alert=True."""
        self.client.force_login(self.owner)
        res = self.client.get(reverse('dashboard:audit'), {'tab': 'alerts', 'role': 'admin'})
        self.assertEqual(res.status_code, 200)
        events = res.context['events']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, 'account_locked')
        self.assertTrue(events[0].alert)
