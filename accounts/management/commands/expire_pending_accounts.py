"""
Command to deactivate pending user accounts that set a password but failed to enroll 2FA
within 72 hours (Phase 4 Task 5).
"""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from django_otp import user_has_device
from accounts.services import sign_out_everywhere
from audit.models import AuditEvent
from audit.services import record_event

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Deactivates active accounts that have set a password but failed to enroll in "
        "Two-Factor Authentication within 72 hours (or a custom threshold via --hours)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=72,
            help="Threshold hours after which pending unenrolled accounts expire (default: 72)."
        )
        parser.add_argument(
            '--now',
            type=str,
            default=None,
            help="Override current timestamp (ISO 8601 string) for testing/simulation."
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simulate account deactivation without writing to the database."
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        now_str = options['now']

        if now_str:
            current_time = parse_datetime(now_str)
            if not current_time:
                from datetime import datetime
                try:
                    current_time = datetime.fromisoformat(now_str)
                except Exception:
                    current_time = timezone.now()
            if timezone.is_naive(current_time):
                current_time = timezone.make_aware(current_time)
        else:
            current_time = timezone.now()

        cutoff = current_time - timedelta(hours=hours)

        # Active users only
        active_users = User.objects.filter(is_active=True)
        expired_count = 0

        for user in active_users:
            # Must have set a password
            if not user.has_usable_password():
                continue

            # If enrolled in 2FA, leave alone!
            if user_has_device(user):
                continue

            # Determine when password was set
            latest_setup = (
                AuditEvent.objects.filter(
                    target_model='User',
                    target_object_id=str(user.pk),
                    event_type__in=['account_setup_completed', 'password_set', 'password_changed']
                )
                .order_by('-timestamp')
                .first()
            )

            pw_time = latest_setup.timestamp if latest_setup else user.date_joined

            if pw_time <= cutoff:
                expired_count += 1
                age_hours = (current_time - pw_time).total_seconds() / 3600.0

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] Would deactivate '{user.username}' (password set {age_hours:.1f}h ago, unenrolled)."
                        )
                    )
                else:
                    user.is_active = False
                    user.save(update_fields=['is_active'])
                    terminated = sign_out_everywhere(user)

                    record_event(
                        event_type="user_deactivated",
                        actor=None,
                        actor_username="system",
                        target_user=user,
                        alert=True,
                        description=(
                            f"Account '{user.username}' deactivated automatically: password was set "
                            f"{age_hours:.1f} hours ago with no 2FA device enrolled (cutoff: {hours}h). "
                            f"Terminated {terminated} session(s). Owner must issue a new setup link."
                        )
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Deactivated pending account '{user.username}' (password set {age_hours:.1f}h ago). "
                            f"Terminated {terminated} session(s)."
                        )
                    )

        if expired_count == 0:
            self.stdout.write(self.style.SUCCESS("No pending unenrolled accounts exceeded the expiration threshold."))
        else:
            action = "would be deactivated" if dry_run else "deactivated"
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"Completed: {expired_count} account(s) {action} (threshold: {hours}h)."
                )
            )
