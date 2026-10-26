import getpass
import sys
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from jimcan.security import security_event

User = get_user_model()


class Command(BaseCommand):
    help = "Interactively bootstraps the first Owner account. Refuses to run if any user exists."

    def handle(self, *args, **options):
        # 1. Refuse if any user already exists
        if User.objects.exists():
            self.stdout.write(self.style.ERROR(
                "[ERROR] An account already exists in the database. "
                "bootstrap_owner can only be run on an initial empty database."
            ))
            sys.exit(1)

        self.stdout.write(self.style.MIGRATE_HEADING("=== Jimcan First Owner Account Setup ==="))
        self.stdout.write("Note: The Owner account will be active, non-staff, and non-superuser, belonging to the Owner group.\n")

        # 2. Prompt for username
        username = input("Owner Username: ").strip()
        if not username:
            self.stdout.write(self.style.ERROR("[ERROR] Username cannot be blank."))
            sys.exit(1)

        # 3. Prompt for email
        email = input("Owner Email: ").strip()
        if not email or "@" not in email:
            self.stdout.write(self.style.ERROR("[ERROR] A valid email address is required."))
            sys.exit(1)

        # 4. Prompt interactively for password using getpass (hidden input)
        password = getpass.getpass("Password (min 12 chars): ")
        password_confirm = getpass.getpass("Confirm Password: ")

        if password != password_confirm:
            self.stdout.write(self.style.ERROR("[ERROR] Passwords do not match."))
            sys.exit(1)

        # 5. Validate against configured password validators
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError as e:
            self.stdout.write(self.style.ERROR("[ERROR] Password does not meet security requirements:"))
            for msg in e.messages:
                self.stdout.write(self.style.ERROR(f"  - {msg}"))
            sys.exit(1)

        # 6. Create account: active, not staff, not superuser
        owner = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )

        # 7. Attach to Owner group (create group if missing)
        owner_group, _ = Group.objects.get_or_create(name='Owner')
        owner.groups.add(owner_group)

        # 8. Emit structured security event
        security_event("owner_bootstrapped", username=username, email=email)

        self.stdout.write(self.style.SUCCESS(
            f"\n[SUCCESS] Owner account '{username}' created successfully in group 'Owner'."
        ))
