from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from audit.models import SecurityNoise


class Command(BaseCommand):
    help = "Prunes SecurityNoise entries older than 90 days. Never touches AuditEvent."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help="Age threshold in days for pruning noise records (default: 90 days)"
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)

        deleted_count, _ = SecurityNoise.objects.filter(last_seen__lt=cutoff).delete()

        self.stdout.write(self.style.SUCCESS(
            f"[PRUNED] Successfully deleted {deleted_count} SecurityNoise records older than {days} days ({cutoff.isoformat()})."
        ))
        self.stdout.write("Notice: AuditEvent records are append-only and were not touched.")
