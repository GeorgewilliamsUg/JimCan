"""
Server management command to reset Two-Factor Authentication for a user (Phase 4 Task 6).
Requires shell access, prints clear warnings, invalidates all sessions, writes audit event as 'system',
and alerts all Owners.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from django_otp import devices_for_user
from accounts.services import sign_out_everywhere
from audit.services import record_event

User = get_user_model()


class Command(BaseCommand):
    help = "Resets Two-Factor Authentication devices and backup codes for a user account."

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help="The username of the account to reset."
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help="Bypass interactive confirmation prompt."
        )

    def handle(self, *args, **options):
        username = options['username'].strip()
        no_input = options['no_input']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist.")

        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING(f"WARNING: Resetting Two-Factor Authentication for '{username}'"))
        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(
            "This command will:\n"
            f"  1. Permanently delete all registered TOTP authenticator devices for '{username}'.\n"
            f"  2. Invalidate and purge all static backup recovery codes.\n"
            f"  3. Immediately terminate all active sessions for '{username}'.\n"
            f"  4. Require '{username}' to re-enroll in Two-Factor Authentication on their next sign-in.\n"
            "  5. Record a tamper-evident audit event as 'system' and alert all active Owners.\n"
        )

        if not no_input:
            confirm = input(f"Are you sure you want to proceed with resetting MFA for '{username}'? (yes/no): ").strip().lower()
            if confirm != 'yes':
                self.stdout.write(self.style.NOTICE("MFA reset cancelled by operator."))
                return

        # Delete all registered OTP devices and tokens
        devices = list(devices_for_user(user))
        deleted_count = 0
        for device in devices:
            device.delete()
            deleted_count += 1

        # Sign out everywhere
        terminated_sessions = sign_out_everywhere(user)

        # Record tamper-evident audit event as 'system' and alert all Owners
        record_event(
            event_type="two_factor_reset",
            actor=None,
            actor_username="system",
            target_user=user,
            alert=True,
            description=(
                f"MFA reset via CLI command 'reset_mfa' for user '{username}'. "
                f"Removed {deleted_count} device(s) and terminated {terminated_sessions} active session(s)."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully reset MFA for user '{username}'. "
                f"Removed {deleted_count} device(s) and terminated {terminated_sessions} active session(s). "
                f"Audit event recorded and Owners alerted."
            )
        )
