from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class AppPermission(models.Model):
    """
    Unmanaged model defining custom application permissions not tied directly
    to database tables (Phase 5 Task 1).

    Conforms to Django's unmanaged model permission pattern:
    managed = False, default_permissions = ().
    """
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            # Global / System Permissions
            ('view_financials', 'Can view financials and money-flow figures'),
            ('view_tax_reports', 'Can view tax and statutory reports'),
            ('export_reports', 'Can export financial and operational reports'),
            ('manage_users', 'Can manage users, roles, and credentials'),
            ('view_audit_log', 'Can view security and financial audit trail'),
            ('edit_settings', 'Can edit company configuration and system settings'),

            # Operational Section Permissions
            ('view_overview', 'Can view operational overview dashboard'),
            ('view_leads', 'Can view commercial leads and inquiries'),
            ('add_leads', 'Can create commercial leads and inquiries'),
            ('change_leads', 'Can edit commercial leads and inquiries'),
            ('view_projects', 'Can view active construction builds and projects'),
            ('add_projects', 'Can create construction builds and projects'),
            ('change_projects', 'Can edit construction builds and projects'),
            ('view_rates', 'Can view BOQ master rates and catalog'),
            ('add_rates', 'Can create BOQ master rates and catalog items'),
            ('change_rates', 'Can edit BOQ master rates and catalog items'),
            ('view_invoices', 'Can view client tax invoices and billing claims'),
            ('add_invoices', 'Can create client tax invoices and billing claims'),
            ('change_invoices', 'Can edit draft client tax invoices'),
            ('view_expenses', 'Can view project material and labor expenses'),
            ('add_expenses', 'Can submit project material and labor expenses'),
            ('change_expenses', 'Can edit and approve project expenses'),
            ('view_files', 'Can view field uploads and site documentation'),
            ('add_files', 'Can upload field photos and site documentation'),
            ('change_files', 'Can edit field uploads and site documentation'),
        ]


from cryptography.fernet import Fernet
from django.contrib.auth.models import User as DjangoUser


class UserProfile(models.Model):
    """
    Extended profile for Django auth User.
    Tracks operational role, force-change password requirement, encrypted initial
    credentials vault, granular permission overrides, creator, and metadata.
    """
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner / SuperAdmin'
        PROJECT_MANAGER = 'PM', 'Project Manager'
        SITE_ENGINEER = 'ENGINEER', 'Site Engineer'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant / Auditor'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=50,
        default='',
        blank=True,
        help_text="Operational role identifier"
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text="Requires user to change temporary password upon next login"
    )

    # Encrypted temporary credential storage for admin oversight prior to initial change
    initial_credential_vault = models.BinaryField(
        null=True,
        blank=True,
        help_text="Symmetrically encrypted initial password ciphertext (Fernet)"
    )

    # Granular Permissions Overrides
    can_view_boq = models.BooleanField(default=False, help_text="Access BOQ master pricing")
    can_view_boq_rates = models.BooleanField(default=False, help_text="Access BOQ master rates")
    can_approve_expenses = models.BooleanField(default=False, help_text="Permission to sign off on vouchers")
    can_export_tax_reports = models.BooleanField(default=False, help_text="Permission to download URA schedules")
    can_manage_leads = models.BooleanField(default=False, help_text="Edit and reassign pipeline items")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_profiles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def set_initial_vault_password(self, raw_password: str):
        """Encrypts initial raw password symmetrically and sets Django user password."""
        fernet = Fernet(settings.CREDENTIAL_VAULT_KEY)
        self.initial_credential_vault = fernet.encrypt(raw_password.encode('utf-8'))
        if self.user:
            self.user.set_password(raw_password)

    def get_initial_vault_password(self) -> str | None:
        """Decrypts and returns the initial password if must_change_password is still active."""
        if not self.initial_credential_vault or not self.must_change_password:
            return None
        try:
            fernet = Fernet(settings.CREDENTIAL_VAULT_KEY)
            raw_bytes = bytes(self.initial_credential_vault)
            return fernet.decrypt(raw_bytes).decode('utf-8')
        except Exception:
            return None

    def clear_vault_password(self):
        """Permanently wipes the encrypted vault credential upon first password change."""
        self.initial_credential_vault = None
        self.must_change_password = False
        self.save(update_fields=['initial_credential_vault', 'must_change_password'])


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Guarantees every User has a corresponding UserProfile."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()


# Seamless delegation on Django User model
DjangoUser.Role = UserProfile.Role


def _user_set_initial_vault_password(self, raw_password: str):
    if hasattr(self, 'profile'):
        self.profile.set_initial_vault_password(raw_password)
    else:
        self.set_password(raw_password)


def _user_get_initial_vault_password(self) -> str | None:
    if hasattr(self, 'profile'):
        return self.profile.get_initial_vault_password()
    return None


def _user_clear_vault_password(self):
    if hasattr(self, 'profile'):
        self.profile.clear_vault_password()


DjangoUser.set_initial_vault_password = _user_set_initial_vault_password
DjangoUser.get_initial_vault_password = _user_get_initial_vault_password
DjangoUser.clear_vault_password = _user_clear_vault_password

DjangoUser.initial_credential_vault = property(
    lambda self: self.profile.initial_credential_vault if hasattr(self, 'profile') else None,
    lambda self, val: setattr(self.profile, 'initial_credential_vault', val) if hasattr(self, 'profile') else None
)
DjangoUser.can_view_boq = property(
    lambda self: self.profile.can_view_boq if hasattr(self, 'profile') else False,
    lambda self, val: setattr(self.profile, 'can_view_boq', val) if hasattr(self, 'profile') else None
)
DjangoUser.can_view_boq_rates = property(
    lambda self: (self.profile.can_view_boq_rates or self.profile.can_view_boq) if hasattr(self, 'profile') else False,
    lambda self, val: setattr(self.profile, 'can_view_boq_rates', val) if hasattr(self, 'profile') else None
)
DjangoUser.can_approve_expenses = property(
    lambda self: self.profile.can_approve_expenses if hasattr(self, 'profile') else False,
    lambda self, val: setattr(self.profile, 'can_approve_expenses', val) if hasattr(self, 'profile') else None
)
DjangoUser.can_export_tax_reports = property(
    lambda self: self.profile.can_export_tax_reports if hasattr(self, 'profile') else False,
    lambda self, val: setattr(self.profile, 'can_export_tax_reports', val) if hasattr(self, 'profile') else None
)
DjangoUser.can_manage_leads = property(
    lambda self: self.profile.can_manage_leads if hasattr(self, 'profile') else False,
    lambda self, val: setattr(self.profile, 'can_manage_leads', val) if hasattr(self, 'profile') else None
)

User = DjangoUser
