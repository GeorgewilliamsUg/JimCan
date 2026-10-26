import sys
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from accounts.services import generate_setup_link
from jimcan.security import security_event

User = get_user_model()


class Command(BaseCommand):
    help = "Generates and prints a one-time set-password setup link to the console for a specified user."

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help="Username of the user account")

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"[ERROR] User '{username}' does not exist."))
            sys.exit(1)

        if not user.is_active:
            self.stdout.write(self.style.ERROR(f"[ERROR] User '{username}' is deactivated."))
            sys.exit(1)

        link = generate_setup_link(user)
        security_event("setup_link_issued", username=username)

        self.stdout.write(self.style.MIGRATE_HEADING("=== One-Time Account Setup Link ==="))
        self.stdout.write(f"Target User: {username}")
        self.stdout.write("Expires in:  1 hour (3600 seconds)\n")
        self.stdout.write(self.style.SUCCESS(link))
        self.stdout.write("\nNote: This link can only be used once. Never log or transmit via insecure channels.")
