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


class UserProfile(models.Model):
    """
    Extended profile for Django auth User.
    Tracks operational role, force-change password requirement, creator, and metadata.
    """
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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Guarantees every User has a corresponding UserProfile."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
