import getpass
import sys
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from accounts.roles import ALL_ROLES, ROLE_OWNER, assign_role
from accounts.services import generate_setup_link
from jimcan.security import security_event

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a new user account safely and assigns one of the three canonical roles (Owner, Finance, Site staff)."

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help="Username for the new account")
        parser.add_argument('email', type=str, help="Email address for the new account")
        parser.add_argument(
            '--role',
            type=str,
            default=ROLE_OWNER,
            choices=ALL_ROLES,
            help="Role to assign (default: Owner)"
        )
        parser.add_argument(
            '--link',
            action='store_true',
            help="Do not prompt for password; generate a one-time set-password setup link instead"
        )

    def handle(self, *args, **options):
        username = options['username'].strip()
        email = options['email'].strip()
        role = options['role']
        use_link = options['link']

        if not username:
            self.stdout.write(self.style.ERROR("[ERROR] Username cannot be blank."))
            sys.exit(1)

        if not email or "@" not in email:
            self.stdout.write(self.style.ERROR("[ERROR] A valid email address is required."))
            sys.exit(1)

        if User.objects.filter(username__iexact=username).exists():
            self.stdout.write(self.style.ERROR(f"[ERROR] User with username '{username}' already exists."))
            sys.exit(1)

        if User.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.ERROR(f"[ERROR] User with email '{email}' already exists."))
            sys.exit(1)

        self.stdout.write(self.style.MIGRATE_HEADING(f"=== Creating {role} Account: {username} ==="))

        if use_link:
            # Create user with unusable password and generate link
            user = User.objects.create_user(username=username, email=email)
            user.set_unusable_password()
            user.save()
            assign_role(user, role)
            link = generate_setup_link(user)
            security_event("user_created", username=username, role=role)
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] User '{username}' created with role '{role}'."))
            self.stdout.write("\nOne-Time Set-Password Link (valid 1 hour):")
            self.stdout.write(self.style.SUCCESS(link))
            return

        # Prompt for password interactively
        password = getpass.getpass("Enter password (minimum 12 chars): ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            self.stdout.write(self.style.ERROR("[ERROR] Passwords do not match."))
            sys.exit(1)

        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError as e:
            self.stdout.write(self.style.ERROR("[ERROR] Password does not meet security requirements:"))
            for msg in e.messages:
                self.stdout.write(self.style.ERROR(f"  - {msg}"))
            sys.exit(1)

        user = User.objects.create_user(username=username, email=email, password=password)
        assign_role(user, role)
        security_event("user_created", username=username, role=role)

        self.stdout.write(self.style.SUCCESS(
            f"[SUCCESS] Account '{username}' successfully created with role '{role}'.\n"
            f"- is_superuser: {user.is_superuser}\n"
            f"- is_staff: {user.is_staff}\n"
            f"- Active: {user.is_active}\n"
            f"- Group: {role}"
        ))
