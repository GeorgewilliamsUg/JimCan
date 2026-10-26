from django.core.management.base import BaseCommand
from django.utils import timezone
from audit.models import AuditChainHead, AuditAnchorRecord


class Command(BaseCommand):
    help = "Prints and records the latest audit sequence number, head hash, and timestamp for off-site verification."

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-record',
            action='store_true',
            help='Print anchor without persisting to AuditAnchorRecord table'
        )

    def handle(self, *args, **options):
        head, _ = AuditChainHead.objects.get_or_create(id=1)
        now = timezone.now()

        seq = head.latest_sequence
        head_hash = head.latest_hash
        timestamp_str = now.isoformat()

        if not options.get('no_record'):
            AuditAnchorRecord.objects.create(
                sequence=seq,
                head_hash=head_hash,
                created_at=now
            )

        self.stdout.write(self.style.MIGRATE_HEADING("=== Jimcan Audit Anchor Snapshot ==="))
        self.stdout.write(f"Sequence:   {seq}")
        self.stdout.write(f"Head Hash:  {head_hash}")
        self.stdout.write(f"Timestamp:  {timestamp_str}")
        self.stdout.write(self.style.SUCCESS("\n[ANCHOR RECORDED] Store this snapshot outside the server weekly."))
