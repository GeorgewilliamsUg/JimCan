from django.db import models


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
