"""
Centralized Financial & Operational Domain Selectors for Jimcan Construction.
Single source of truth for all dashboard calculations and aggregations across:
- Overview (/overview/)
- Invoices (/invoices/)
- Expenses (/expenses/)
- Projects (/projects/)
- Commercial Leads (/leads/)
- URA Tax Reports (/tax/)
"""

from datetime import date
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from dashboard.data_store import (
    get_expenses_summary,
    get_projects_list,
    get_invoices_list,
    get_tax_summary,
    get_leads_list,
    get_rates_catalog,
    get_site_files_list,
    compute_invoice_status,
    get_status_display,
)


def get_active_projects(can_view_financials: bool = True) -> List[Dict[str, Any]]:
    """
    Returns active construction builds with cost tracking and data scoping.
    Single source of truth for projects data.
    """
    raw_projects = get_projects_list()
    projects = []
    for p_raw in raw_projects:
        p = p_raw.copy()
        p['status_display'] = get_status_display(p.get('status', 'ACTIVE'))
        p['current_phase_display'] = get_status_display(p.get('current_phase', ''))
        p['get_status_display'] = lambda s=p['status_display']: s
        if not can_view_financials:
            p.pop('contract_value', None)
            p.pop('contract_value_fmt', None)
            p.pop('contract_value_ugx', None)
            p.pop('actual_cost_ugx', None)
            p.pop('actual_cost_fmt', None)
            p.pop('budget_spent_pct', None)
        projects.append(p)
    return projects


def get_contract_portfolio_total(projects: Optional[List[Dict[str, Any]]] = None) -> int:
    """
    Calculates Contract Portfolio Total: sum of active project contracts.
    """
    if projects is None:
        projects = get_projects_list()
    return sum(
        int(p.get('contract_value', 0) or p.get('contract_value_ugx', 0))
        for p in projects
        if str(p.get('status', 'ACTIVE')).upper() == 'ACTIVE'
    )


def get_invoices(current_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Returns all milestone claims with dynamically computed status.
    Single source of truth for invoice data.
    """
    return get_invoices_list(current_date=current_date)


def get_invoiced_totals(invoices: Optional[List[Dict[str, Any]]] = None) -> Dict[str, int]:
    """
    Calculates Total Invoiced Gross, Total Invoiced Net, and Output VAT (18%).
    """
    if invoices is None:
        invoices = get_invoices_list()
    total_gross = sum(int(inv.get('gross_amount', 0)) for inv in invoices)
    total_net = sum(int(inv.get('net_amount', 0)) for inv in invoices)
    total_vat = sum(int(inv.get('vat_amount', 0)) for inv in invoices)
    return {
        'gross': total_gross,
        'net': total_net,
        'output_vat': total_vat,
        'gross_fmt': f"{total_gross:,}",
        'net_fmt': f"{total_net:,}",
        'output_vat_fmt': f"{total_vat:,}",
    }


def get_collections_total(invoices: Optional[List[Dict[str, Any]]] = None) -> int:
    """
    Calculates Total Collections Received to Date across all invoices.
    """
    if invoices is None:
        invoices = get_invoices_list()
    return sum(int(inv.get('paid_amount', 0)) for inv in invoices)


def get_outstanding_receivables_total(invoices: Optional[List[Dict[str, Any]]] = None) -> int:
    """
    Calculates Total Outstanding Receivables (Balance Due).
    """
    if invoices is None:
        invoices = get_invoices_list()
    return sum(int(inv.get('balance_due', 0)) for inv in invoices)


def get_overdue_invoices_summary(
    invoices: Optional[List[Dict[str, Any]]] = None,
    current_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Calculates Total Overdue Invoices and Total Overdue Amount:
    Invoices where balance_due > 0 and current_date > due_date.
    """
    if invoices is None:
        invoices = get_invoices_list(current_date=current_date)
    if current_date is None:
        current_date = date.today()

    overdue_list = []
    for inv in invoices:
        balance = inv.get('balance_due', 0)
        due_d = inv.get('due_date')
        if isinstance(due_d, str):
            due_d = date.fromisoformat(due_d)
        if balance > 0 and current_date > due_d:
            overdue_list.append(inv)

    overdue_count = len(overdue_list)
    overdue_amount = sum(inv.get('balance_due', 0) for inv in overdue_list)
    return {
        'count': overdue_count,
        'amount': overdue_amount,
        'amount_fmt': f"{overdue_amount:,}",
        'invoices': overdue_list,
    }


def get_direct_expenses_totals() -> Dict[str, Any]:
    """
    Calculates Total Direct Expenses: Gross, Net, and Input VAT.
    """
    exp_summary = get_expenses_summary()
    return {
        'count': exp_summary['count'],
        'gross': exp_summary['total_gross'],
        'net': exp_summary['total_net'],
        'input_vat': exp_summary['total_vat'],
        'gross_fmt': exp_summary['total_gross_fmt'],
        'net_fmt': exp_summary['total_net_fmt'],
        'input_vat_fmt': exp_summary['total_vat_fmt'],
        'category_breakdown': exp_summary['category_breakdown'],
        'categories': exp_summary['categories'],
        'expenses': exp_summary['expenses'],
    }


def get_tax_report_summary(current_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Returns reconciled statutory tax figures ensuring:
    - Output VAT == sum(Invoice.vat_amount)
    - Input VAT == sum(Expense.vat_amount)
    - Net VAT == Output VAT - Input VAT
    - WHT 6% == sum(Invoice.net_amount * 0.06 for paid invoices)
    """
    exp_totals = get_direct_expenses_totals()
    inv_totals = get_invoiced_totals()
    invoices = get_invoices_list(current_date=current_date)

    input_vat = exp_totals['input_vat']
    output_vat = inv_totals['output_vat']
    net_vat_payable = output_vat - input_vat
    gross_invoiced = inv_totals['gross']
    wht_receivable = sum(inv['net_amount'] * 0.06 for inv in invoices if inv['paid_amount'] > 0)

    tax_data = get_tax_summary()
    filings = tax_data.get('filings', [])

    return {
        'input_vat': input_vat,
        'output_vat': output_vat,
        'net_vat_payable': net_vat_payable,
        'wht_receivable': wht_receivable,
        'gross_invoiced': gross_invoiced,
        'input_vat_fmt': f"{int(input_vat):,}",
        'output_vat_fmt': f"{int(output_vat):,}",
        'net_vat_payable_fmt': f"{int(net_vat_payable):,}",
        'wht_receivable_fmt': f"{int(wht_receivable):,}",
        'gross_invoiced_fmt': f"{int(gross_invoiced):,}",
        'filings': filings,
    }


def get_leads_summary(can_view_financials: bool = True) -> Dict[str, Any]:
    """
    Returns commercial leads with dynamic aggregations for:
    - Total pipeline value
    - Won tenders sum
    - Scheduled site visits count
    """
    raw_leads = get_leads_list()
    leads = []
    pipeline_total = 0
    won_total = 0
    site_visit_count = 0

    for l_raw in raw_leads:
        l = l_raw.copy()
        raw_status = l.get('status', '').upper()
        l['status_display'] = get_status_display(raw_status)
        l['get_status_display'] = lambda s=l['status_display']: s
        b = l.get('budget', 0)
        pipeline_total += b
        if raw_status == 'WON':
            won_total += b
        if raw_status == 'SITE_VISIT':
            site_visit_count += 1

        if not can_view_financials:
            l.pop('budget', None)
            l.pop('budget_fmt', None)
        leads.append(l)

    stage_defs = [
        ('NEW', 'New intake', 'status-neutral', 'Inquiries received'),
        ('SITE_VISIT', 'Site visit', 'status-amber', 'Inspections scheduled'),
        ('QUOTED', 'Quoted', 'status-amber', 'Proposals submitted'),
        ('WON', 'Won', 'status-green', 'Contracts awarded'),
    ]
    stages = []
    for s_key, s_label, s_variant, s_desc in stage_defs:
        s_leads = [l for l in leads if l.get('status', '').upper() == s_key]
        s_budget = sum(l.get('budget', 0) for l in s_leads)
        stages.append({
            'key': s_key,
            'label': s_label,
            'variant': s_variant,
            'description': s_desc,
            'count': len(s_leads),
            'leads': s_leads,
            'total_budget': s_budget,
            'total_budget_fmt': f"{s_budget:,}",
        })

    return {
        'leads': leads,
        'stages': stages,
        'count': len(leads),
        'pipeline_total': pipeline_total,
        'pipeline_total_fmt': f"{pipeline_total:,}",
        'won_total': won_total,
        'won_total_fmt': f"{won_total:,}",
        'site_visit_count': site_visit_count,
    }


def get_dashboard_overview_metrics(current_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Master reconciled financial metrics selector for Overview and KPI cards.
    Guarantees that Overview metrics draw from the identical querysets and
    domain logic as detail views.
    """
    projects = get_projects_list()
    invoices = get_invoices_list(current_date=current_date)
    expenses = get_expenses_summary()

    contract_value = get_contract_portfolio_total(projects)
    invoiced_totals = get_invoiced_totals(invoices)
    invoiced_gross = invoiced_totals['gross']
    invoiced_net = invoiced_totals['net']
    output_vat = invoiced_totals['output_vat']

    collected = get_collections_total(invoices)
    still_owed = get_outstanding_receivables_total(invoices)

    overdue_summary = get_overdue_invoices_summary(invoices, current_date=current_date)
    overdue_count = overdue_summary['count']
    overdue_amount = overdue_summary['amount']

    committed_cost = expenses['total_net']
    committed_cost_gross = expenses['total_gross']
    input_vat = expenses['total_vat']
    net_vat_payable = output_vat - input_vat

    cost_pct = round((committed_cost / contract_value * 100), 1) if contract_value else 0.0
    invoiced_pct = round((invoiced_gross / contract_value * 100), 1) if contract_value else 0.0
    collected_pct = round((collected / invoiced_gross * 100), 1) if invoiced_gross else 0.0
    collection_of_contract_pct = round((collected / contract_value * 100), 1) if contract_value else 0.0

    return {
        'contract_value': contract_value,
        'contract_value_fmt': f"{contract_value:,}",
        'committed_cost': committed_cost,
        'committed_cost_fmt': f"{int(committed_cost):,}",
        'committed_cost_gross': committed_cost_gross,
        'committed_cost_gross_fmt': f"{int(committed_cost_gross):,}",
        'invoiced': invoiced_gross,
        'invoiced_gross': invoiced_gross,
        'invoiced_gross_fmt': f"{invoiced_gross:,}",
        'invoiced_net': invoiced_net,
        'invoiced_net_fmt': f"{invoiced_net:,}",
        'output_vat': output_vat,
        'output_vat_fmt': f"{output_vat:,}",
        'collected': collected,
        'collected_fmt': f"{collected:,}",
        'still_owed': still_owed,
        'still_owed_fmt': f"{still_owed:,}",
        'overdue_count': overdue_count,
        'overdue_amount': overdue_amount,
        'overdue_amount_fmt': f"{overdue_amount:,}",
        'input_vat': input_vat,
        'input_vat_fmt': f"{int(input_vat):,}",
        'net_vat_payable': net_vat_payable,
        'net_vat_payable_fmt': f"{int(net_vat_payable):,}",
        'cost_percentage': cost_pct,
        'invoiced_percentage': invoiced_pct,
        'collected_percentage': collected_pct,
        'collection_of_contract_percentage': collection_of_contract_pct,
    }


def get_invoice_aging_buckets(invoices: Optional[List[Dict[str, Any]]] = None, current_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Computes active aging buckets for outstanding receivables:
    - Current: due today or future
    - 1-30 Days past due
    - 31-60 Days past due
    - 61-90 Days past due
    - 90+ Days past due
    """
    from datetime import datetime as dt_cls
    if current_date is None:
        current_date = date(2026, 1, 20)
    if invoices is None:
        invoices = get_invoices(current_date=current_date)

    buckets = {
        'current': {'key': 'current', 'label': 'Current', 'sublabel': 'Not yet due', 'count': 0, 'amount': 0, 'invoices': []},
        '1_30': {'key': '1_30', 'label': '1–30 Days', 'sublabel': 'Past due', 'count': 0, 'amount': 0, 'invoices': []},
        '31_60': {'key': '31_60', 'label': '31–60 Days', 'sublabel': 'Past due', 'count': 0, 'amount': 0, 'invoices': []},
        '61_90': {'key': '61_90', 'label': '61–90 Days', 'sublabel': 'Past due', 'count': 0, 'amount': 0, 'invoices': []},
        '90_plus': {'key': '90_plus', 'label': '90+ Days', 'sublabel': 'Severely past due', 'count': 0, 'amount': 0, 'invoices': []},
    }

    for inv in invoices:
        bal = inv.get('balance_due', 0)
        if bal <= 0:
            continue
        due = inv.get('due_date')
        if isinstance(due, str):
            try:
                due = dt_cls.strptime(due[:10], '%Y-%m-%d').date()
            except (ValueError, IndexError):
                due = current_date
        elif isinstance(due, dt_cls):
            due = due.date()

        days_past = (current_date - due).days
        if days_past <= 0:
            b_key = 'current'
        elif 1 <= days_past <= 30:
            b_key = '1_30'
        elif 31 <= days_past <= 60:
            b_key = '31_60'
        elif 61 <= days_past <= 90:
            b_key = '61_90'
        else:
            b_key = '90_plus'

        buckets[b_key]['count'] += 1
        buckets[b_key]['amount'] += bal
        buckets[b_key]['invoices'].append(inv)

    for b in buckets.values():
        b['amount_fmt'] = f"{b['amount']:,}"

    return buckets
