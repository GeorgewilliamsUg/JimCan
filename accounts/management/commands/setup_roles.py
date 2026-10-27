"""
Management command: setup_roles (Phase 5 Task 1).
Creates or updates the groups from accounts/roles.py idempotently.
Running it twice changes nothing; it removes permissions no longer listed.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from accounts.roles import ROLE_PERMISSIONS, ALL_ROLES


class Command(BaseCommand):
    help = "Idempotently provisions or updates user role groups and permissions matching accounts/roles.py."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Provisioning Roles and Permissions ==="))

        total_groups_updated = 0
        total_perms_assigned = 0

        for role_name in ALL_ROLES:
            group, created = Group.objects.get_or_create(name=role_name)
            action = "Created" if created else "Configured"

            declared_perm_strings = ROLE_PERMISSIONS.get(role_name, [])
            resolved_permissions = []
            missing_perms = []

            for perm_str in declared_perm_strings:
                if '.' in perm_str:
                    app_label, codename = perm_str.split('.', 1)
                    perm = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=codename
                    ).first()
                else:
                    perm = Permission.objects.filter(codename=perm_str).first()

                if perm:
                    resolved_permissions.append(perm)
                else:
                    missing_perms.append(perm_str)

            if missing_perms:
                self.stdout.write(self.style.WARNING(
                    f"  [WARN] Missing permissions in DB for {role_name}: {', '.join(missing_perms)}"
                ))

            # Idempotent assignment: group.permissions.set() clears any unlisted perms
            current_perms = set(group.permissions.all())
            target_perms = set(resolved_permissions)

            added = target_perms - current_perms
            removed = current_perms - target_perms

            group.permissions.set(resolved_permissions)
            total_groups_updated += 1
            total_perms_assigned += len(resolved_permissions)

            diff_msg = []
            if added:
                diff_msg.append(f"+{len(added)} added")
            if removed:
                diff_msg.append(f"-{len(removed)} removed")
            diff_str = f" ({', '.join(diff_msg)})" if diff_msg else " (unchanged)"

            self.stdout.write(self.style.SUCCESS(
                f"  [{action}] {role_name:12}: {len(resolved_permissions)} permissions{diff_str}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n[DONE] Successfully configured {total_groups_updated} groups with {total_perms_assigned} permissions."
        ))
