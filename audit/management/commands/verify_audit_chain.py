from django.core.management.base import BaseCommand, CommandError
from audit.services import verify_chain, notify_owners


class Command(BaseCommand):
    help = "Verifies the cryptographic HMAC-SHA256 integrity and sequence continuity of the audit log."

    def handle(self, *args, **options):
        self.stdout.write("Verifying Jimcan cryptographic audit chain...")
        is_valid, message, failure_seq = verify_chain()

        if is_valid:
            self.stdout.write(self.style.SUCCESS(f"[PASS] {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"[FAIL] {message}"))
            # Notify Owners of tampering or chain corruption
            notify_owners(
                subject="Tampering Detected: Audit Chain Verification Failure",
                event=f"Chain failure detected at sequence {failure_seq}: {message}"
            )
            raise CommandError(f"[FAIL] {message}")
