"""
Unit and Integration Tests for Admin User Provisioning, Credential Oversight & Permission Management.
Covers:
1. Admin Credential Assignment (uniqueness checks across active and inactive accounts).
2. Credential Visibility & Oversight (Fernet symmetric encryption vault, secure reveal, permanent wipe on 1st login).
3. Granular Permission Overrides (can_view_boq, can_approve_expenses, can_export_tax_reports, can_manage_leads).
4. RBAC security boundaries (Owner/Admin access only to vault credentials).
"""

from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import UserProfile
from accounts.roles import (
    ROLE_ADMIN,
    ROLE_SITE_ENGINEER,
    ROLE_ACCOUNTANT,
    ROLE_PROJECT_MANAGER,
    assign_role,
)
from accounts.forms import UserCreateForm, UserEditForm

User = get_user_model()


class AdminUserProvisioningVaultTests(TestCase):
    """Verifies credential assignment, symmetric vault oversight, and granular overrides."""

    def setUp(self):
        super().setUp()
        call_command('setup_roles')

        # Create Primary Admin User
        self.admin = User.objects.create_user(
            username='admin_boss',
            email='boss@jimcanconstruction.site',
            password='AdminPassword123!',
            first_name='Admin',
            last_name='Boss',
        )
        assign_role(self.admin, ROLE_ADMIN)

        # Create Secondary Admin User to satisfy >= 2 active owners constraint
        self.admin2 = User.objects.create_user(
            username='admin_deputy',
            email='deputy@jimcanconstruction.site',
            password='AdminPassword123!',
            first_name='Deputy',
            last_name='Admin',
        )
        assign_role(self.admin2, ROLE_ADMIN)

        # Create Standard Staff User
        self.staff_engineer = User.objects.create_user(
            username='site_eng',
            email='engineer@jimcanconstruction.site',
            password='EngPassword123!',
            first_name='Site',
            last_name='Engineer',
        )
        assign_role(self.staff_engineer, ROLE_SITE_ENGINEER)

        self.client = Client()

    def test_vault_lifecycle_encryption_and_wipe(self):
        """Tests that initial_credential_vault encrypts with Fernet, decrypts, and wipes on clear."""
        user = User.objects.create_user(
            username='new_joiner',
            email='joiner@jimcanconstruction.site',
            first_name='John',
            last_name='Joiner',
        )
        profile = user.profile
        profile.must_change_password = True

        raw_temp = 'TempPass@2026!'
        profile.set_initial_vault_password(raw_temp)
        profile.save()

        self.assertTrue(profile.must_change_password)

        # Binary field should store Fernet ciphertext (not raw text)
        self.assertIsNotNone(profile.initial_credential_vault)
        self.assertNotEqual(bytes(profile.initial_credential_vault), raw_temp.encode())

        # Admin retrieval should decrypt accurately
        decrypted = profile.get_initial_vault_password()
        self.assertEqual(decrypted, raw_temp)

        # Simulating first forced password rotation
        profile.clear_vault_password()

        # Database state verification: ciphertext must be permanently erased
        profile.refresh_from_db()
        self.assertIsNone(profile.initial_credential_vault)
        self.assertFalse(profile.must_change_password)
        self.assertIsNone(profile.get_initial_vault_password())

    def test_admin_credential_assignment_uniqueness_active_and_inactive(self):
        """Verifies email and username uniqueness checks against both active and inactive users."""
        # Deactivated user in system
        inactive_user = User.objects.create_user(
            username='former_worker',
            email='former@jimcanconstruction.site',
            password='Password123!',
            is_active=False,
        )

        # 1. Attempt duplicate email
        form1 = UserCreateForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'former@jimcanconstruction.site',
            'username': 'new_worker',
            'role': ROLE_SITE_ENGINEER,
            'password_option': 'auto',
            'must_change_password': True,
        })
        self.assertFalse(form1.is_valid())
        self.assertIn('email', form1.errors)
        self.assertIn('already exists', form1.errors['email'][0])

        # 2. Attempt duplicate username
        form2 = UserCreateForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'brand_new@jimcanconstruction.site',
            'username': 'former_worker',
            'role': ROLE_SITE_ENGINEER,
            'password_option': 'auto',
            'must_change_password': True,
        })
        self.assertFalse(form2.is_valid())
        self.assertIn('username', form2.errors)
        self.assertIn('already exists', form2.errors['username'][0])

    def test_granular_permission_overrides_application(self):
        """Verifies that granular boolean toggles map to specific permissions."""
        form_data = {
            'first_name': 'Grace',
            'last_name': 'Namatovu',
            'email': 'grace.n@jimcanconstruction.site',
            'username': 'grace_n',
            'role': ROLE_SITE_ENGINEER,
            'password_option': 'manual',
            'custom_password': 'ManualPass123!',
            'can_view_boq': True,
            'can_approve_expenses': True,
            'can_export_tax_reports': True,
            'can_manage_leads': True,
            'must_change_password': True,
            'send_onboarding_email': False,
        }

        form = UserCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(created_by=self.admin)
        user.refresh_from_db()

        # Verify profile flags
        self.assertTrue(user.profile.can_view_boq)
        self.assertTrue(user.profile.can_view_boq_rates)
        self.assertTrue(user.profile.can_approve_expenses)
        self.assertTrue(user.profile.can_export_tax_reports)
        self.assertTrue(user.profile.can_manage_leads)

        # Fresh user instance for clean permission check
        fresh_user = User.objects.get(pk=user.pk)
        self.assertTrue(fresh_user.has_perm('accounts.view_rates'))
        self.assertTrue(fresh_user.has_perm('accounts.change_expenses'))
        self.assertTrue(fresh_user.has_perm('accounts.view_tax_reports'))
        self.assertTrue(fresh_user.has_perm('accounts.export_reports'))
        self.assertTrue(fresh_user.has_perm('accounts.view_leads'))
        self.assertTrue(fresh_user.has_perm('accounts.add_leads'))
        self.assertTrue(fresh_user.has_perm('accounts.change_leads'))

        # Verify vault stored initial password
        self.assertEqual(user.profile.get_initial_vault_password(), 'ManualPass123!')

    def test_granular_permission_overrides_editing(self):
        """Tests that editing granular permissions dynamically adds and removes permissions."""
        user = User.objects.create_user(
            username='engineer_dan',
            email='dan@jimcanconstruction.site',
            first_name='Dan',
            last_name='Engineer',
        )
        assign_role(user, ROLE_SITE_ENGINEER)

        edit_form = UserEditForm(
            data={
                'first_name': 'Dan',
                'last_name': 'Engineer',
                'email': 'dan@jimcanconstruction.site',
                'role': ROLE_SITE_ENGINEER,
                'can_manage_leads': True,
                'can_approve_expenses': False,
                'can_view_boq': True,
                'can_export_tax_reports': False,
            },
            instance=user
        )
        self.assertTrue(edit_form.is_valid(), edit_form.errors)
        edit_form.save()

        # Fresh user to clear in-memory _perm_cache
        u1 = User.objects.get(pk=user.pk)
        self.assertTrue(u1.profile.can_manage_leads)
        self.assertTrue(u1.has_perm('accounts.change_leads'))

        # Remove lead permission
        edit_form2 = UserEditForm(
            data={
                'first_name': 'Dan',
                'last_name': 'Engineer',
                'email': 'dan@jimcanconstruction.site',
                'role': ROLE_SITE_ENGINEER,
                'can_manage_leads': False,
                'can_approve_expenses': False,
                'can_view_boq': False,
                'can_export_tax_reports': False,
            },
            instance=user
        )
        self.assertTrue(edit_form2.is_valid())
        edit_form2.save()

        # Fresh user to clear in-memory _perm_cache
        u2 = User.objects.get(pk=user.pk)
        self.assertFalse(u2.profile.can_manage_leads)
        self.assertFalse(u2.has_perm('accounts.change_leads'))

    def test_vault_endpoint_access_control(self):
        """Owner/Admin can inspect vault credentials; non-admins receive 403 Forbidden."""
        provisioned_user = User.objects.create_user(
            username='temp_eng',
            email='temp@jimcanconstruction.site',
            first_name='Temp',
            last_name='Eng',
        )
        provisioned_user.profile.set_initial_vault_password('SuperSecretTemp99!')
        provisioned_user.profile.must_change_password = True
        provisioned_user.profile.save()

        # 1. Non-admin access attempt -> 403 Forbidden
        self.client.force_login(self.staff_engineer)
        url = reverse('accounts:user_vault_credential', args=[provisioned_user.pk])
        resp_unauth = self.client.get(url)
        self.assertEqual(resp_unauth.status_code, 403)

        # 2. Admin access attempt -> 200 OK with decrypted password
        self.client.force_login(self.admin)
        resp_admin = self.client.get(url)
        self.assertEqual(resp_admin.status_code, 200)
        data = resp_admin.json()
        self.assertTrue(data['has_vault'])
        self.assertEqual(data['password'], 'SuperSecretTemp99!')

        # 3. Once user clears password, vault endpoint returns None for password
        provisioned_user.profile.clear_vault_password()
        resp_cleared = self.client.get(url)
        self.assertEqual(resp_cleared.status_code, 200)
        data_cleared = resp_cleared.json()
        self.assertFalse(data_cleared['has_vault'])
        self.assertIsNone(data_cleared['password'])

    def test_team_roster_view_renders_vault_and_granular_chips(self):
        """Tests that /dashboard/team/ renders the team credentials ledger properly."""
        user = User.objects.create_user(
            username='clerk_mary',
            email='mary@jimcanconstruction.site',
            first_name='Mary',
            last_name='Clerk',
        )
        assign_role(user, ROLE_SITE_ENGINEER)
        user.profile.set_initial_vault_password('MaryInitial2026!')
        user.profile.can_view_boq = True
        user.profile.must_change_password = True
        user.profile.save()

        self.client.force_login(self.admin)
        url = reverse('accounts:user_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Team Credentials Ledger')
        self.assertContains(resp, 'clerk_mary')
        self.assertContains(resp, 'BOQ Pricing')
        self.assertContains(resp, 'Initial Vault (wipes on 1st login)')
