"""
Automated Test Suite for Live Operational Sections.
Validates that all 7 operational sections:
- Expenses (/expenses/)
- Projects (/projects/)
- Invoices (/invoices/)
- Master Rates (/rates/)
- URA Tax (/tax/)
- Commercial Leads (/leads/)
- Field Files (/files/)
render live, authentic construction data from construction_expenses.xlsx,
and strictly uphold Phase 5 server-side data scoping rules between roles.
"""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from accounts.roles import ROLE_FINANCE, ROLE_OWNER, ROLE_SITE_STAFF, assign_role

User = get_user_model()


class TestLiveDataSections(TestCase):
    """Verifies live data propagation and scoping across all 7 operational pages."""

    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', stdout=None)

        cls.owner = User.objects.create_user(
            username='test_owner_live',
            email='owner@jimcan.site',
            password='TestPassword123!',
        )
        assign_role(cls.owner, ROLE_OWNER)

        cls.finance = User.objects.create_user(
            username='test_finance_live',
            email='finance@jimcan.site',
            password='TestPassword123!',
        )
        assign_role(cls.finance, ROLE_FINANCE)

        cls.staff = User.objects.create_user(
            username='test_staff_live',
            email='staff@jimcan.site',
            password='TestPassword123!',
        )
        assign_role(cls.staff, ROLE_SITE_STAFF)

    def _client_for(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_expenses_page_financial_role(self):
        """Owner and Finance see 100 expenses, financial totals, and category breakdown."""
        for user in (self.owner, self.finance):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:expenses'))
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.context['can_view_financials'])
            self.assertEqual(resp.context['expenses_count'], 100)
            self.assertIn('total_gross_fmt', resp.context)
            self.assertIn('total_net_fmt', resp.context)
            self.assertIn('total_vat_fmt', resp.context)
            self.assertIn('category_breakdown', resp.context)
            html = resp.content.decode('utf-8')
            self.assertIn('Gross Disbursements', html)
            self.assertIn('UGX 621,355,500', html)
            self.assertIn('JCC-001', html)

    def test_expenses_page_site_staff_scoping(self):
        """Site staff sees 100 vouchers but financial totals are scrubbed on server."""
        c = self._client_for(self.staff)
        resp = c.get(reverse('dashboard:expenses'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['can_view_financials'])
        self.assertEqual(resp.context['expenses_count'], 100)
        self.assertNotIn('total_gross_fmt', resp.context)
        self.assertNotIn('total_net_fmt', resp.context)
        self.assertNotIn('total_vat_fmt', resp.context)
        self.assertNotIn('category_breakdown', resp.context)

        # Individual voucher amounts are scrubbed to '—'
        first_exp = resp.context['expenses'][0]
        self.assertEqual(first_exp['gross_fmt'], '—')
        self.assertNotIn('gross_ugx', first_exp)

        html = resp.content.decode('utf-8')
        self.assertNotIn('Gross Disbursements', html)
        self.assertNotIn('UGX 621,355,500', html)
        self.assertIn('CONFIDENTIAL', html)

    def test_projects_page_financial_role(self):
        """Owner and Finance see 8 projects with contract values and actual costs."""
        for user in (self.owner, self.finance):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:projects'))
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.context['can_view_financials'])
            self.assertEqual(resp.context['projects_count'], 8)
            self.assertIn('total_gross_fmt', resp.context)
            html = resp.content.decode('utf-8')
            self.assertIn('Kampala Office Block', html)
            self.assertIn('UGX 12.92 B', html)

    def test_projects_page_site_staff_scoping(self):
        """Site staff sees 8 projects but financial contract/cost figures are scrubbed."""
        c = self._client_for(self.staff)
        resp = c.get(reverse('dashboard:projects'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['can_view_financials'])
        self.assertEqual(resp.context['projects_count'], 8)
        self.assertNotIn('total_gross_fmt', resp.context)

        first_p = resp.context['projects'][0]
        self.assertNotIn('contract_value', first_p)
        self.assertNotIn('actual_cost_ugx', first_p)
        self.assertNotIn('contract_value_fmt', first_p)

        html = resp.content.decode('utf-8')
        self.assertNotIn('UGX 12.92 B', html)
        self.assertIn('Site Safety Record', html)

    def test_invoices_page_access(self):
        """Owner and Finance access invoices; Site staff receives 403."""
        for user in (self.owner, self.finance):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:invoices'))
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['invoices_count'], 11)
            html = resp.content.decode('utf-8')
            self.assertIn('INV-2026-001', html)
            self.assertIn('PAID', html)

        c = self._client_for(self.staff)
        resp = c.get(reverse('dashboard:invoices'))
        self.assertEqual(resp.status_code, 403)

    def test_rates_page_access(self):
        """All authenticated roles with view_rates see the 19 master rates."""
        for user in (self.owner, self.finance, self.staff):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:rates'))
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['rates_count'], 19)
            html = resp.content.decode('utf-8')
            self.assertIn('MAT-CEM-01', html)
            self.assertIn('42.5N Pozzolana Cement', html)

    def test_tax_page_access(self):
        """Owner and Finance access URA tax ledger; Site staff receives 403."""
        for user in (self.owner, self.finance):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:tax'))
            self.assertEqual(resp.status_code, 200)
            html = resp.content.decode('utf-8')
            self.assertIn('URA Tax &amp; Statutory Reports', html)
            self.assertIn('PRN-2601-98421', html)

        c = self._client_for(self.staff)
        resp = c.get(reverse('dashboard:tax'))
        self.assertEqual(resp.status_code, 403)

    def test_leads_page_access(self):
        """Owner and Finance access leads; Site staff receives 403."""
        for user in (self.owner, self.finance):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:leads'))
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['leads_count'], 4)
            html = resp.content.decode('utf-8')
            self.assertIn('LEAD-2026-081', html)
            self.assertIn('Dr. Patrick Ssenyonga', html)

        c = self._client_for(self.staff)
        resp = c.get(reverse('dashboard:leads'))
        self.assertEqual(resp.status_code, 403)

    def test_files_page_access(self):
        """All operational roles access site files and media."""
        for user in (self.owner, self.finance, self.staff):
            c = self._client_for(user)
            resp = c.get(reverse('dashboard:files'))
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['files_count'], 6)
            html = resp.content.decode('utf-8')
            self.assertIn('Structural-Foundation-Plan', html)
