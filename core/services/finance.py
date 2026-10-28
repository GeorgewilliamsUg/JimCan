"""
Finance Domain Service for Jimcan Operations.
Exposes centralized aggregations and financial reconciliation metrics.
"""

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
    get_invoice_aging_buckets,
    compute_invoice_status,
    get_status_display,
)

__all__ = [
    'get_active_projects',
    'get_contract_portfolio_total',
    'get_invoices',
    'get_invoiced_totals',
    'get_collections_total',
    'get_outstanding_receivables_total',
    'get_overdue_invoices_summary',
    'get_direct_expenses_totals',
    'get_tax_report_summary',
    'get_leads_summary',
    'get_dashboard_overview_metrics',
    'get_invoice_aging_buckets',
    'compute_invoice_status',
    'get_status_display',
]
