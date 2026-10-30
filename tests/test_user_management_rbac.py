"""
Unit and Integration Tests for User Management, RBAC, and Onboarding Email System.
Tests:
- Phase 1: UserProfile Data Model, Operational Roles, and Password Workflow
- Phase 2: Admin UI, User Creation, Role Assignment, and Password Reset Action
- Phase 3: Automated HTML Onboarding Email System, SMTP resilience, and Legal Disclaimer Footer
- Password Workflow: ForcePasswordChangeMiddleware first-login enforcement
"""

import string
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import UserProfile
from accounts.roles import (
    ROLE_ADMIN,
    ROLE_OWNER,
    ROLE_PROJECT_MANAGER,
    ROLE_SITE_ENGINEER,
    ROLE_SITE_STAFF,
    ROLE_ACCOUNTANT,
    ROLE_FINANCE,
    assign_role,
    get_user_role,
    is_admin,
)
from accounts.services import (
    generate_temporary_password,
    send_onboarding_email,
)
from accounts.forms import UserCreateForm

User = get_user_model()


class UserManagementRBACTests(TestCase):
    """Verifies UserProfile, operational roles, and permission architectures."""

    def setUp(self):
        super().setUp()
        call_command('setup_roles')

        # Admin user
        self.admin_user = User.objects.create_user(
            username='admin_alice',
            email='alice@jimcanconstruction.site',
            password='AdminPassword123!',
            first_name='Alice',
            last_name='Admin',
        )
        assign_role(self.admin_user, ROLE_ADMIN)

        # Secondary admin to satisfy >= 2 active owners guardrail
        self.admin_user2 = User.objects.create_user(
            username='admin_bob',
            email='bob@jimcanconstruction.site',
            password='AdminPassword123!',
            first_name='Bob',
            last_name='Admin',
        )
        assign_role(self.admin_user2, ROLE_ADMIN)

        # Standard staff user
        self.staff_user = User.objects.create_user(
            username='engineer_edward',
            email='edward@jimcanconstruction.site',
            password='StaffPassword123!',
            first_name='Edward',
            last_name='Engineer',
        )
        assign_role(self.staff_user, ROLE_SITE_ENGINEER)

    def test_user_profile_automatically_created(self):
        """Every created User automatically has a UserProfile attached via signal."""
        user = User.objects.create_user(
            username='new_staff',
            email='newstaff@jimcanconstruction.site',
            password='TestPassword123!'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(user.profile.user, user)

    def test_operational_role_assignment(self):
        """Assigning operational roles updates both profile and corresponding permission group."""
        user = User.objects.create_user(
            username='pm_user',
            email='pm@jimcanconstruction.site',
            password='TestPassword123!'
        )

        # 1. Project Manager
        assign_role(user, ROLE_PROJECT_MANAGER)
        user.refresh_from_db()
        self.assertEqual(get_user_role(user), ROLE_PROJECT_MANAGER)
        self.assertEqual(user.profile.role, ROLE_PROJECT_MANAGER)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        # 2. Accountant
        assign_role(user, ROLE_ACCOUNTANT)
        user.refresh_from_db()
        self.assertEqual(get_user_role(user), ROLE_ACCOUNTANT)
        self.assertEqual(user.profile.role, ROLE_ACCOUNTANT)

        # 3. Admin
        assign_role(user, ROLE_ADMIN)
        user.refresh_from_db()
        self.assertEqual(get_user_role(user), ROLE_ADMIN)
        self.assertTrue(is_admin(user))

    def test_temporary_password_generator_specifications(self):
        """
        Temporary password must be 12 chars long and contain uppercase,
        lowercase, digits, and special characters.
        """
        for _ in range(50):
            pwd = generate_temporary_password(12)
            self.assertEqual(len(pwd), 12)
            self.assertTrue(any(c in string.ascii_uppercase for c in pwd), "Missing uppercase")
            self.assertTrue(any(c in string.ascii_lowercase for c in pwd), "Missing lowercase")
            self.assertTrue(any(c in string.digits for c in pwd), "Missing digits")
            self.assertTrue(any(c in "!@#$%^&*()-_=+" for c in pwd), "Missing special characters")

    def test_user_create_form_auto_password(self):
        """UserCreateForm with auto password option creates user and sets must_change_password=True."""
        form_data = {
            'first_name': 'Grace',
            'last_name': 'Accountant',
            'email': 'grace@jimcanconstruction.site',
            'role': ROLE_ACCOUNTANT,
            'password_option': 'auto',
            'must_change_password': 'true',
        }
        form = UserCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        created_user = form.save(created_by=self.admin_user)

        self.assertEqual(created_user.email, 'grace@jimcanconstruction.site')
        self.assertEqual(created_user.profile.role, ROLE_ACCOUNTANT)
        self.assertTrue(created_user.profile.must_change_password)
        self.assertEqual(created_user.profile.created_by, self.admin_user)
        self.assertIsNotNone(form.generated_password)
        self.assertEqual(len(form.generated_password), 12)
        # Password works to authenticate
        self.assertTrue(created_user.check_password(form.generated_password))

    def test_user_create_form_custom_password(self):
        """UserCreateForm with custom password validates minimum length."""
        # Short password fails
        form_data = {
            'first_name': 'Sam',
            'last_name': 'Site',
            'email': 'sam@jimcanconstruction.site',
            'role': ROLE_SITE_ENGINEER,
            'password_option': 'manual',
            'custom_password': 'short',
            'must_change_password': 'true',
        }
        form = UserCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_password', form.errors)

        # Valid custom password succeeds
        form_data['custom_password'] = 'CustomValidPass2026!'
        form2 = UserCreateForm(data=form_data)
        self.assertTrue(form2.is_valid(), form2.errors)
        created_user = form2.save(created_by=self.admin_user)
        self.assertTrue(created_user.check_password('CustomValidPass2026!'))
        self.assertTrue(created_user.profile.must_change_password)

    def test_user_create_form_duplicate_email_rejected(self):
        """Duplicate email address fails validation with clear message."""
        form_data = {
            'first_name': 'Alice',
            'last_name': 'Clone',
            'email': 'alice@jimcanconstruction.site',  # duplicate of self.admin_user
            'role': ROLE_SITE_ENGINEER,
            'password_option': 'auto',
        }
        form = UserCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already exists', str(form.errors['email']))


class ForcePasswordChangeMiddlewareTests(TestCase):
    """Verifies that must_change_password strictly intercepts authenticated routes."""

    def setUp(self):
        super().setUp()
        call_command('setup_roles')
        self.user = User.objects.create_user(
            username='temp_user',
            email='temp@jimcanconstruction.site',
            password='InitialPassword123!',
            first_name='Temp',
            last_name='User',
        )
        assign_role(self.user, ROLE_SITE_ENGINEER)
        self.user.profile.must_change_password = True
        self.user.profile.save()

    def test_route_intercepted_and_redirected_to_password_change(self):
        """When must_change_password=True, dashboard routes redirect to /password_change/."""
        client = Client()
        client.force_login(self.user)

        # Attempt to access overview
        resp = client.get(reverse('dashboard:overview'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('password_change'))

        # Attempt to access projects
        resp2 = client.get(reverse('dashboard:projects'))
        self.assertEqual(resp2.status_code, 302)
        self.assertEqual(resp2.url, reverse('password_change'))

    def test_password_change_view_accessible_when_forced(self):
        """The password change and logout endpoints remain accessible."""
        client = Client()
        client.force_login(self.user)

        # Password change page is accessible (200)
        resp = client.get(reverse('password_change'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Password Change Required', resp.content.decode('utf-8'))

    def test_password_change_clears_must_change_password(self):
        """Successfully updating password clears must_change_password to False."""
        client = Client()
        client.force_login(self.user)

        post_data = {
            'old_password': 'InitialPassword123!',
            'new_password1': 'BrandNewSecurePass2026!#',
            'new_password2': 'BrandNewSecurePass2026!#',
        }
        resp = client.post(reverse('password_change'), post_data)
        self.assertEqual(resp.status_code, 302)

        self.user.refresh_from_db()
        self.assertFalse(self.user.profile.must_change_password)

        # Now dashboard access is granted
        resp_overview = client.get(reverse('dashboard:overview'))
        self.assertEqual(resp_overview.status_code, 200)


class OnboardingEmailTests(TestCase):
    """Verifies the automated HTML onboarding email workflow and visual/legal constraints."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='invited_eng',
            email='invited@jimcanconstruction.site',
            password='InitialPassword123!',
            first_name='Kavuma',
            last_name='Joseph',
        )

    def test_send_onboarding_email_content_and_headers(self):
        """
        Dispatches multipart HTML email with credentials, sender sgeorge.ug@gmail.com,
        subject 'Your Jimcan Operations Account Credentials', and required disclaimers.
        """
        mail.outbox = []
        temp_pass = 'Temp99#SecurePass'

        success, err = send_onboarding_email(self.user, temp_pass)
        self.assertTrue(success)
        self.assertIsNone(err)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]

        # 1. Subject and Sender
        self.assertEqual(message.subject, "Your Jimcan Operations Account Credentials")
        self.assertEqual(message.from_email, "sgeorge.ug@gmail.com")
        self.assertEqual(message.to, [self.user.email])

        # 2. Fallback Plain Text Content
        self.assertIn("Hello Kavuma,", message.body)
        self.assertIn("Username / Email:   invited@jimcanconstruction.site", message.body)
        self.assertIn(f"Temporary Password: {temp_pass}", message.body)
        self.assertIn("Intended Recipient Notice:", message.body)
        self.assertIn("sgeorge.ug@gmail.com", message.body)
        self.assertIn("Privacy & Data Usage:", message.body)
        self.assertIn("Security Advisory:", message.body)

        # 3. HTML Alternative Content
        self.assertEqual(len(message.alternatives), 1)
        html_body, mime_type = message.alternatives[0]
        self.assertEqual(mime_type, "text/html")
        self.assertIn("Jimcan Operations Platform", html_body)
        self.assertIn("Hello Kavuma,", html_body)
        self.assertIn("invited@jimcanconstruction.site", html_body)
        self.assertIn(temp_pass, html_body)
        self.assertIn("Intended Recipient Notice:", html_body)
        self.assertIn("sgeorge.ug@gmail.com", html_body)
        self.assertIn("Privacy &amp; Data Usage:", html_body)
        self.assertIn("Security Advisory:", html_body)

    def test_send_onboarding_email_graceful_smtp_failure(self):
        """SMTP errors or timeouts return (False, err) and do not crash execution."""
        with patch('accounts.services.EmailMultiAlternatives.send', side_effect=TimeoutError("SMTP timed out")):
            success, err = send_onboarding_email(self.user, "TempPass123!")
            self.assertFalse(success)
            self.assertIn("SMTP timed out", err)


class AdminTeamManagementViewTests(TestCase):
    """Verifies team list, password reset action, and RBAC gating."""

    def setUp(self):
        super().setUp()
        call_command('setup_roles')

        # Admin
        self.admin_user = User.objects.create_user(
            username='admin_boss',
            email='boss@jimcanconstruction.site',
            password='AdminPassword123!',
            first_name='Boss',
            last_name='Admin',
        )
        assign_role(self.admin_user, ROLE_ADMIN)

        # Secondary Admin
        self.admin_user2 = User.objects.create_user(
            username='admin_boss2',
            email='boss2@jimcanconstruction.site',
            password='AdminPassword123!',
            first_name='Boss2',
            last_name='Admin',
        )
        assign_role(self.admin_user2, ROLE_ADMIN)

        # Staff user
        self.site_user = User.objects.create_user(
            username='site_peter',
            email='peter@jimcanconstruction.site',
            password='StaffPassword123!',
            first_name='Peter',
            last_name='Site',
        )
        assign_role(self.site_user, ROLE_SITE_ENGINEER)

    def _client_with_reauth(self, user):
        client = Client()
        client.force_login(user)
        session = client.session
        session['reauth_at'] = 9999999999.0
        session.save()
        return client

    def test_team_roster_restricted_to_admin(self):
        """Non-admin accounts receive 403 on /settings/team/ and /dashboard/team/."""
        staff_client = Client()
        staff_client.force_login(self.site_user)

        resp1 = staff_client.get(reverse('dashboard:settings_team'))
        self.assertEqual(resp1.status_code, 403)

        resp2 = staff_client.get(reverse('dashboard:dashboard_team'))
        self.assertEqual(resp2.status_code, 403)

        # Admin client gets 200
        admin_client = Client()
        admin_client.force_login(self.admin_user)
        resp3 = admin_client.get(reverse('dashboard:settings_team'))
        self.assertEqual(resp3.status_code, 200)
        self.assertIn('Team & User Management', resp3.content.decode('utf-8'))

    def test_admin_reset_password_action(self):
        """Admin triggering password reset updates password, sets must_change_password, and emails."""
        mail.outbox = []
        admin_client = self._client_with_reauth(self.admin_user)

        old_pass_hash = self.site_user.password

        resp = admin_client.post(
            reverse('accounts:user_reset_password', kwargs={'user_id': self.site_user.pk})
        )
        self.assertEqual(resp.status_code, 302)

        self.site_user.refresh_from_db()
        self.assertNotEqual(self.site_user.password, old_pass_hash)
        self.assertTrue(self.site_user.profile.must_change_password)

        # Verification email was dispatched (audit alert email may also be dispatched to owners)
        onboarding_emails = [m for m in mail.outbox if self.site_user.email in m.to]
        self.assertEqual(len(onboarding_emails), 1)
        self.assertEqual(onboarding_emails[0].to, [self.site_user.email])
        self.assertEqual(onboarding_emails[0].subject, "Your Jimcan Operations Account Credentials")

    def test_admin_reset_password_get_renders_page(self):
        """Admin navigating to reset password via GET renders confirmation page without 405 error."""
        admin_client = self._client_with_reauth(self.admin_user)
        resp = admin_client.get(
            reverse('accounts:user_reset_password', kwargs={'user_id': self.site_user.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Reset User Password', resp.content.decode('utf-8'))
        self.assertIn(self.site_user.username, resp.content.decode('utf-8'))

