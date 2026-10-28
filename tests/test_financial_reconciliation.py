"""
Automated Financial Reconciliation and Single Source of Truth Unit Tests.
Validates mathematical integrity across Overview, Invoices, Expenses, Projects, Leads, and Tax views.
"""

from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from accounts.roles import ROLE_FINANCE, ROLE_OWNER, assign_role
from dashboard.selectors import (
    get_active_projects,
    get_contract_portfolio_total,
    get_invoices,
    get_invoiced_totals,
    get_collections_total,
    get_outstanding_receivables_total,
    get_overdue_invoices_summary,
    get_direct_expenses_totals,
    get_tax_report_summary,
    get_leads_summary,
    get_dashboard_overview_metrics,
    compute_invoice_status,
    get_status_display,
)

User = get_user_model()


class FinancialReconciliationTests(TestCase):
    """
    Asserts mathematical consistency, single-source-of-truth calculations,
    and dynamic status computation across the domain.
    """

    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', stdout=None)

        cls.owner = User.objects.create_user(
            username='reconcile_owner',
            email='owner_rec@jimcan.site',
            password='TestPassword123!',
        )
        assign_role(cls.owner, ROLE_OWNER)

        cls.finance = User.objects.create_user(
            username='reconcile_finance',
            email='finance_rec@jimcan.site',
            password='TestPassword123!',
        )
        assign_role(cls.finance, ROLE_FINANCE)

    def _client(self):
        c = Client()
        c.force_login(self.owner)
        return c

    def test_reconciliation_exact_brief_assertions(self):
        """
        Directly asserts the 7 reconciliation equations specified in Phase 1:
        1. Overview.contract_value == sum(Project.contract_value for active projects)
        2. Overview.invoiced == sum(Invoice.gross_total)
        3. Overview.still_owed == sum(Invoice.balance_due)
        4. Overview.committed_cost == sum(Expense.net_amount)
        5. Overview.overdue_count == count(Invoice where balance_due > 0 and due_date < today)
        6. TaxReport.output_vat == sum(Invoice.vat_amount)
        7. TaxReport.input_vat == sum(Expense.vat_amount)
        """
        today = date.today()
        metrics = get_dashboard_overview_metrics(current_date=today)
        projects = get_active_projects(can_view_financials=True)
        invoices = get_invoices(current_date=today)
        expenses_data = get_direct_expenses_totals()
        tax_report = get_tax_report_summary(current_date=today)

        # 1. Overview.contract_value == sum(Project.contract_value for active projects)
        active_projects_contract_sum = sum(
            p['contract_value'] for p in projects if p.get('status', 'ACTIVE') == 'ACTIVE'
        )
        self.assertEqual(metrics['contract_value'], active_projects_contract_sum)

        # 2. Overview.invoiced == sum(Invoice.gross_total)
        invoices_gross_total = sum(inv['gross_amount'] for inv in invoices)
        self.assertEqual(metrics['invoiced'], invoices_gross_total)
        self.assertEqual(metrics['invoiced_gross'], invoices_gross_total)

        # 3. Overview.still_owed == sum(Invoice.balance_due)
        invoices_balance_due_sum = sum(inv['balance_due'] for inv in invoices)
        self.assertEqual(metrics['still_owed'], invoices_balance_due_sum)

        # 4. Overview.committed_cost == sum(Expense.net_amount)
        expenses_net_sum = sum(e['net_ugx'] for e in expenses_data['expenses'])
        self.assertEqual(metrics['committed_cost'], expenses_net_sum)

        # 5. Overview.overdue_count == count(Invoice where balance_due > 0 and due_date < today)
        overdue_calc_count = sum(
            1 for inv in invoices
            if inv['balance_due'] > 0 and (
                date.fromisoformat(inv['due_date']) if isinstance(inv['due_date'], str) else inv['due_date']
            ) < today
        )
        self.assertEqual(metrics['overdue_count'], overdue_calc_count)

        # 6. TaxReport.output_vat == sum(Invoice.vat_amount)
        invoices_vat_sum = sum(inv['vat_amount'] for inv in invoices)
        self.assertEqual(tax_report['output_vat'], invoices_vat_sum)

        # 7. TaxReport.input_vat == sum(Expense.vat_amount)
        expenses_vat_sum = sum(e['vat_ugx'] for e in expenses_data['expenses'])
        self.assertEqual(tax_report['input_vat'], expenses_vat_sum)

    def test_overview_view_context_matches_selectors(self):
        """
        Validates that GET /overview/ context variables are identical to the
        centralized selector metrics, eliminating any hardcoded or stale fixtures.
        """
        client = self._client()
        resp = client.get(reverse('dashboard:overview'))
        self.assertEqual(resp.status_code, 200)

        today = date.today()
        metrics = get_dashboard_overview_metrics(current_date=today)

        ctx = resp.context
        self.assertEqual(ctx['total_contract_value_raw'], metrics['contract_value'])
        self.assertEqual(ctx['committed_cost'], metrics['committed_cost'])
        self.assertEqual(ctx['total_invoiced_gross_raw'], metrics['invoiced'])
        self.assertEqual(ctx['total_receivable'], metrics['still_owed'])
        self.assertEqual(ctx['overdue_count'], metrics['overdue_count'])
        self.assertEqual(ctx['output_vat'], metrics['output_vat'])
        self.assertEqual(ctx['input_vat'], metrics['input_vat'])

    def test_detail_views_reconciliation_consistency(self):
        """
        Validates that Invoices, Expenses, Projects, Leads, and Tax views
        draw from identical totals as the Overview view.
        """
        client = self._client()

        # Invoices Page
        resp_inv = client.get(reverse('dashboard:invoices'))
        self.assertEqual(resp_inv.status_code, 200)
        self.assertEqual(resp_inv.context['total_gross'], get_invoiced_totals()['gross'])
        self.assertEqual(resp_inv.context['total_collected'], get_collections_total())
        self.assertEqual(resp_inv.context['total_balance'], get_outstanding_receivables_total())

        # Expenses Page
        resp_exp = client.get(reverse('dashboard:expenses'))
        self.assertEqual(resp_exp.status_code, 200)
        exp_totals = get_direct_expenses_totals()
        self.assertEqual(resp_exp.context['total_net_fmt'], exp_totals['net_fmt'])
        self.assertEqual(resp_exp.context['total_gross_fmt'], exp_totals['gross_fmt'])

        # Tax Page
        resp_tax = client.get(reverse('dashboard:tax'))
        self.assertEqual(resp_tax.status_code, 200)
        tax_totals = get_tax_report_summary()
        self.assertEqual(resp_tax.context['output_vat'], tax_totals['output_vat'])
        self.assertEqual(resp_tax.context['input_vat'], tax_totals['input_vat'])
        self.assertEqual(resp_tax.context['net_vat_payable'], tax_totals['net_vat_payable'])

        # Leads Page
        resp_leads = client.get(reverse('dashboard:leads'))
        self.assertEqual(resp_leads.status_code, 200)
        leads_data = get_leads_summary()
        self.assertEqual(resp_leads.context['pipeline_total'], leads_data['pipeline_total'])
        self.assertEqual(resp_leads.context['won_total'], leads_data['won_total'])
        self.assertEqual(resp_leads.context['site_visit_count'], leads_data['site_visit_count'])

    def test_dynamic_status_computation_rules(self):
        """
        Tests the 4 dynamic invoice status rules:
        - Paid: balance_due <= 0
        - Overdue: balance_due > 0 and current_date > due_date
        - Partially Paid: balance_due > 0 and amount_paid > 0 and current_date <= due_date
        - Sent / Issued: balance_due == total_gross and current_date <= due_date
        """
        today = date(2026, 10, 28)

        # 1. Paid
        status, label = compute_invoice_status(
            balance_due=0,
            paid_amount=1000000,
            gross_amount=1000000,
            due_date=today - timedelta(days=10),
            current_date=today,
        )
        self.assertEqual(status, 'PAID')
        self.assertEqual(label, 'Paid')

        # 2. Overdue
        status, label = compute_invoice_status(
            balance_due=500000,
            paid_amount=0,
            gross_amount=500000,
            due_date=today - timedelta(days=5),
            current_date=today,
        )
        self.assertEqual(status, 'OVERDUE')
        self.assertEqual(label, 'Overdue')

        # 3. Partially Paid
        status, label = compute_invoice_status(
            balance_due=300000,
            paid_amount=200000,
            gross_amount=500000,
            due_date=today + timedelta(days=10),
            current_date=today,
        )
        self.assertEqual(status, 'PART_PAID')
        self.assertEqual(label, 'Part paid')

        # 4. Sent / Issued
        status, label = compute_invoice_status(
            balance_due=500000,
            paid_amount=0,
            gross_amount=500000,
            due_date=today + timedelta(days=10),
            current_date=today,
        )
        self.assertEqual(status, 'SENT')
        self.assertEqual(label, 'Sent')

    def test_status_display_clean_human_readable_mapping(self):
        """
        Validates mapping of raw database choices to clean sentence-case strings.
        """
        self.assertEqual(get_status_display('PART_PAID'), 'Part paid')
        self.assertEqual(get_status_display('SITE_VISIT'), 'Site visit')
        self.assertEqual(get_status_display('PAID'), 'Paid')
        self.assertEqual(get_status_display('OVERDUE'), 'Overdue')
        self.assertEqual(get_status_display('SENT'), 'Sent')
        self.assertEqual(get_status_display('QUOTED'), 'Quoted')
        self.assertEqual(get_status_display('WON'), 'Won')
        self.assertEqual(get_status_display('ACTIVE'), 'Active')
        self.assertEqual(get_status_display('EXTERNAL_WORKS'), 'External works')
