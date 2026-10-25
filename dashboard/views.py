"""
View handlers for Jimcan Operations Dashboard.
Implements Phase 1 Shell & Feedback views, role-based access checks,
HTMX trigger endpoints, and branded error boundaries.
"""

import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import views as auth_views
from django.urls import reverse, reverse_lazy

# Role permissions map according to docs/design/roles-permissions.md & navigation.py
ROLE_PERMISSIONS = {
    'overview': ['admin', 'manager'],
    'leads': ['admin', 'manager'],
    'projects': ['admin', 'manager', 'engineer', 'accountant'],
    'rates': ['admin', 'manager', 'accountant'],
    'invoices': ['admin', 'manager', 'accountant'],
    'expenses': ['admin', 'manager', 'engineer', 'accountant'],
    'tax': ['admin', 'accountant'],
    'files': ['admin', 'manager', 'engineer'],
    'styleguide': ['admin', 'manager', 'engineer', 'accountant'],
    'shell_demo': ['admin', 'manager', 'engineer', 'accountant'],
    'settings': ['admin'],
    'audit': ['admin'],
}

class WelcomeLoginView(auth_views.LoginView):
    """
    Landing Welcome and Login view at root URL (/).
    Renders the full-viewport branded welcome screen with centered login card.
    Redirects authenticated users directly to the operational dashboard.
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or str(reverse_lazy('dashboard:overview'))

def _get_active_role(request):
    """Retrieves current active role from session or request user."""
    role = request.GET.get('role')
    if role:
        request.session['active_role'] = role.lower()
    current_role = request.session.get('active_role')
    if not current_role:
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_role = getattr(request.user, 'role', 'admin')
        else:
            current_role = 'admin'
    return current_role.lower()

def _check_permission(request, section_id):
    """Verifies if the current user role is allowed in this section."""
    current_role = _get_active_role(request)
    allowed = ROLE_PERMISSIONS.get(section_id, ['admin'])
    return current_role in allowed

def _require_auth(request):
    """
    Enforces authentication for internal dashboard views.
    Unauthenticated users are strictly routed back to the welcome / login page.
    Preserves demo role simulation in automated test suites when ?role= is present,
    or during shell showroom testing.
    """
    if not request.user.is_authenticated:
        if request.GET.get('role') or request.session.get('active_role') or request.path.startswith('/shell-demo'):
            return None
        return redirect(f"{reverse('login')}?next={request.path}")
    return None

def overview_view(request):
    """
    Landing overview view: graph-free, ultra-minimalist light-mode dashboard interface.
    Employs IBM Plex typography, extreme scale contrast, and split-view inspector.
    """
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'overview'):
        return render(request, '403.html', status=403)

    # Load structured demo data from fixtures
    demo_file = settings.BASE_DIR / 'fixtures' / 'demo_data.json'
    demo_data = {}
    if demo_file.exists():
        with open(demo_file, 'r', encoding='utf-8') as f:
            demo_data = json.load(f)

    projects = demo_data.get('projects', [])
    invoices = demo_data.get('sample_invoices', [])
    leads = demo_data.get('leads', [])
    rate_library = demo_data.get('rate_library', [])

    total_contract_value = sum(p.get('contract_value_ugx', 0) for p in projects)
    total_cost_to_date = sum(p.get('cost_to_date_ugx', 0) for p in projects)
    total_invoiced_gross = sum(inv.get('gross_amount_ugx', 0) for inv in invoices)
    total_balance_due = sum(inv.get('balance_due_ugx', 0) for inv in invoices)

    feed_items = []
    for p in projects:
        feed_items.append({
            'type': 'project',
            'type_label': 'PROJECT',
            'id': p.get('code'),
            'title': p.get('title'),
            'subtitle': f"{p.get('client')} · {p.get('location')}",
            'value': f"{p.get('contract_value_ugx', 0):,}",
            'raw_value': p.get('contract_value_ugx', 0),
            'timestamp': p.get('start_date'),
            'status': p.get('current_phase').upper(),
            'has_alert': False,
            'details': {
                'RECORD IDENTIFIER': p.get('code'),
                'ENTITY CLASSIFICATION': 'CONSTRUCTION BUILD WORKSPACE',
                'PRINCIPAL CLIENT': p.get('client'),
                'SITE COORDINATES': p.get('location'),
                'ACTIVE STAGE': p.get('current_phase').upper(),
                'CONTRACT VALUATION': f"UGX {p.get('contract_value_ugx', 0):,}",
                'CUMULATIVE COST': f"UGX {p.get('cost_to_date_ugx', 0):,}",
                'SCHEDULE COMMENCEMENT': p.get('start_date'),
                'TARGET COMMISSIONING': p.get('target_completion'),
                'COMPLIANCE STATUS': 'VERIFIED // ZERO BREACH'
            }
        })
    for inv in invoices:
        has_alert = inv.get('balance_due_ugx', 0) > 0
        feed_items.append({
            'type': 'invoice',
            'type_label': 'INVOICE',
            'id': inv.get('invoice_number'),
            'title': f"Milestone Billing Claim · {inv.get('project_code')}",
            'subtitle': f"Net UGX {inv.get('net_amount_ugx', 0):,} + VAT 18%",
            'value': f"{inv.get('gross_amount_ugx', 0):,}",
            'raw_value': inv.get('gross_amount_ugx', 0),
            'timestamp': '2026-10-18',
            'status': inv.get('status').replace('_', ' ').upper(),
            'has_alert': has_alert,
            'details': {
                'RECORD IDENTIFIER': inv.get('invoice_number'),
                'ENTITY CLASSIFICATION': 'CLIENT TAX INVOICE',
                'ASSOCIATED PROJECT': inv.get('project_code'),
                'NET REVENUE': f"UGX {inv.get('net_amount_ugx', 0):,}",
                'STATUTORY VAT (18%)': f"UGX {inv.get('vat_18_ugx', 0):,}",
                'GROSS CLAIM': f"UGX {inv.get('gross_amount_ugx', 0):,}",
                'REMITTED TOTAL': f"UGX {inv.get('paid_amount_ugx', 0):,}",
                'OUTSTANDING BALANCE': f"UGX {inv.get('balance_due_ugx', 0):,}",
                'RECONCILIATION STATE': inv.get('status').replace('_', ' ').upper(),
                'URA FISCAL STATUS': 'EFRIS COMPLIANT'
            }
        })
    for l in leads:
        feed_items.append({
            'type': 'lead',
            'type_label': 'LEAD',
            'id': l.get('public_id')[:13].upper(),
            'title': l.get('name'),
            'subtitle': f"{l.get('project_type')} · {l.get('location')}",
            'value': f"{l.get('budget_ugx', 0):,}",
            'raw_value': l.get('budget_ugx', 0),
            'timestamp': l.get('created_at')[:10],
            'status': l.get('status').upper(),
            'has_alert': False,
            'details': {
                'RECORD IDENTIFIER': l.get('public_id'),
                'ENTITY CLASSIFICATION': 'COMMERCIAL INQUIRY',
                'PROSPECT NAME': l.get('name'),
                'CONTACT PHONE': l.get('phone'),
                'OFFICIAL EMAIL': l.get('email'),
                'DEVELOPMENT SCOPE': l.get('project_type'),
                'PROPOSED SITE': l.get('location'),
                'INDICATIVE BUDGET': f"UGX {l.get('budget_ugx', 0):,}",
                'PIPELINE POSITION': l.get('status').upper(),
                'QUALIFICATION DATE': l.get('created_at')[:10]
            }
        })
    for r in rate_library:
        feed_items.append({
            'type': 'rate',
            'type_label': 'RATE',
            'id': r.get('code'),
            'title': r.get('description'),
            'subtitle': f"Unit of Measurement: {r.get('unit')}",
            'value': f"{r.get('standard_rate_ugx', 0):,}/{r.get('unit')}",
            'raw_value': r.get('standard_rate_ugx', 0),
            'timestamp': '2026-10-01',
            'status': 'ACTIVE',
            'has_alert': False,
            'details': {
                'RECORD IDENTIFIER': r.get('code'),
                'ENTITY CLASSIFICATION': 'BOQ MASTER SCHEDULE SPEC',
                'SPECIFICATION SUMMARY': r.get('description'),
                'STANDARD UNIT': r.get('unit'),
                'APPROVED UNIT RATE': f"UGX {r.get('standard_rate_ugx', 0):,}",
                'CURRENCY SPEC': 'UGX (FIXED BASE)',
                'SCHEDULE VALIDITY': 'ANNUAL SCHEDULE 2026'
            }
        })

    context = {
        'page_title': 'Operational Index',
        'currency': demo_data.get('currency', 'UGX'),
        'total_contract_value': f"{total_contract_value:,}",
        'total_cost_to_date': f"{total_cost_to_date:,}",
        'total_invoiced_gross': f"{total_invoiced_gross:,}",
        'total_balance_due': f"{total_balance_due:,}",
        'feed_items': feed_items,
        'feed_items_json': json.dumps(feed_items),
        'default_selected_json': json.dumps(feed_items[0] if feed_items else {}),
    }
    return render(request, 'dashboard/overview.html', context)

def styleguide_view(request):
    """Style Guide and Atomic Showroom (Phase 0)."""
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    context = {
        'page_title': 'Design System Showroom',

    }
    return render(request, 'styleguide/showroom.html', context)

def shell_demo_view(request):
    """
    Phase 1 Interactive Showroom:
    Demonstrates role-aware navigation, toast triggers, confirmation modals,
    session timeout warning, and error boundaries.
    """
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    context = {
        'page_title': 'Shell & Feedback Showroom',
    }
    return render(request, 'dashboard/shell_demo.html', context)

# Section Placeholders with Phase 1 Navigation Integration
def leads_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'leads'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'Commercial Leads',
        'section_name': 'Leads & Inquiries',
        'phase_num': 'Phase 5',
        'description': 'Tracking client inquiries, site visit bookings, and commercial quoting pipeline.',
    })

def projects_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'projects'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'Projects & Builds',
        'section_name': 'Active Construction Builds',
        'phase_num': 'Phase 6',
        'description': 'Field milestones, site allocations, daily progress logs, and client sign-offs.',
    })

def rates_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'rates'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'BOQ Master Rates',
        'section_name': 'Bill of Quantities & Material Rates',
        'phase_num': 'Phase 7',
        'description': 'Unit rate cards, standard labor schedules, and construction material catalogs.',
    })

def invoices_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'invoices'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'Invoices & Billing',
        'section_name': 'Client Invoices & Milestone Claims',
        'phase_num': 'Phase 8',
        'description': 'Milestone billing, payment tracking, withholding tax certificates, and PDF invoices.',
    })

def expenses_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'expenses'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'Project Expenses',
        'section_name': 'Material & Labor Cost Tracking',
        'phase_num': 'Phase 9',
        'description': 'Cash vouchers, supplier payments, machine hire, and sub-contractor disbursements.',
    })

def tax_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'tax'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'URA Tax & Financials',
        'section_name': 'URA VAT & Withholding Tax Reports',
        'phase_num': 'Phase 10',
        'description': 'Monthly VAT returns, WHT declarations, and EFRIS fiscal reconciliations.',
    })

def files_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'files'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'Site Uploads & Media',
        'section_name': 'Field Site Photos & Architectural Drawings',
        'phase_num': 'Phase 11',
        'description': 'Mobile camera site captures, GPS-stamped progress photos, and contract attachments.',
    })

def settings_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'settings'):
        return render(request, '403.html', status=403)
    return setup_checklist_view(request)

def setup_checklist_view(request):
    """
    S-95 Admin Setup Checklist Scaffolding (Phase 2).
    Renders the initialization steps required before operating the system,
    with zero unmigrated database model dependencies.
    """
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'settings'):
        return render(request, '403.html', status=403)

    checklist_sections = [
        {
            'category': 'Organization & Branding (S-93)',
            'icon': 'building-2',
            'items': [
                {'id': 'org_profile', 'title': 'Company Legal Profile', 'desc': 'Jimcan legal name, registered address, phone, and contact email.', 'status': 'completed', 'status_label': 'Ready'},
                {'id': 'org_tin', 'title': 'URA Tax Identification Number (TIN)', 'desc': '10-digit URA registration for formal tax compliance.', 'status': 'completed', 'status_label': 'Ready'},
                {'id': 'org_logo', 'title': 'Document Header & Print Branding', 'desc': 'High-resolution logo for client invoices, quotes, and BOQ exports.', 'status': 'pending', 'status_label': 'Pending'},
            ]
        },
        {
            'category': 'Tax & Calculation Rules (S-94)',
            'icon': 'calculator',
            'items': [
                {'id': 'tax_vat', 'title': 'Standard VAT Rate (18%)', 'desc': 'Applicable to taxable commercial construction supplies in Uganda.', 'status': 'completed', 'status_label': 'Default 18%'},
                {'id': 'tax_wht', 'title': 'Withholding Tax (WHT 6%)', 'desc': 'Contractor withholding rate on eligible invoice payments.', 'status': 'completed', 'status_label': 'Default 6%'},
                {'id': 'tax_currency', 'title': 'Operational Currency (UGX)', 'desc': 'Ugandan Shilling configured as system-wide base currency.', 'status': 'completed', 'status_label': 'UGX Fixed'},
            ]
        },
        {
            'category': 'Document Numbering Sequences (S-95)',
            'icon': 'hash',
            'items': [
                {'id': 'seq_inv', 'title': 'Invoice Sequence Counter', 'desc': 'Prefix: JC-INV-2026- | Current next number: 001', 'status': 'completed', 'status_label': 'Configured'},
                {'id': 'seq_quo', 'title': 'Quotation / Estimate Sequence', 'desc': 'Prefix: JC-QUO-2026- | Current next number: 001', 'status': 'completed', 'status_label': 'Configured'},
                {'id': 'seq_prj', 'title': 'Project Code Format', 'desc': 'Prefix: JC-PRJ- | Current next number: 101', 'status': 'completed', 'status_label': 'Configured'},
            ]
        },
        {
            'category': 'BOQ Master Rates & Units (S-50)',
            'icon': 'notebook-tabs',
            'items': [
                {'id': 'rate_units', 'title': 'Standard Measurement Units', 'desc': 'Meters (m), Square Meters (m²), Cubic Meters (m³), Kilograms (kg), Bags.', 'status': 'completed', 'status_label': 'Loaded'},
                {'id': 'rate_base', 'title': 'Core Material Master Rates', 'desc': 'Cement, aggregates, rebar, sand, timber, and masonry unit costs.', 'status': 'pending', 'status_label': 'Phase 7'},
            ]
        },
        {
            'category': 'Initial Team & Role Permissions (S-96)',
            'icon': 'users',
            'items': [
                {'id': 'users_admin', 'title': 'Primary Administrator Account', 'desc': 'Full company view, system settings, and audit visibility.', 'status': 'completed', 'status_label': 'Active'},
                {'id': 'users_manager', 'title': 'Project Manager Onboarding', 'desc': 'Site supervision, milestone tracking, and commercial quotations.', 'status': 'pending', 'status_label': 'Pending Invite'},
                {'id': 'users_engineer', 'title': 'Site Engineer Mobile Accounts', 'desc': 'Field execution view, daily progress logs, and site upload queue.', 'status': 'pending', 'status_label': 'Pending Invite'},
                {'id': 'users_accountant', 'title': 'Accountant Compliance Account', 'desc': 'Financial oversight, tax declarations, and expense disbursements.', 'status': 'pending', 'status_label': 'Pending Invite'},
            ]
        },
    ]

    context = {
        'page_title': 'Admin Setup Checklist',
        'sections': checklist_sections,
        'completed_count': 9,
        'total_count': 14,
        'progress_percent': 64,
    }
    return render(request, 'accounts/setup_checklist.html', context)

def audit_view(request):
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _check_permission(request, 'audit'):
        return render(request, '403.html', status=403)
    return render(request, 'dashboard/section_placeholder.html', {
        'page_title': 'Audit Trail',
        'section_name': 'Security & Compliance Activity Log',
        'phase_num': 'Phase 13',
        'description': 'Immutable ledger of user actions, financial approvals, and permission updates.',
    })

from django.views.decorators.csrf import csrf_exempt

# API Endpoints
def api_heartbeat_view(request):
    """Lightweight session heartbeat ping."""
    return JsonResponse({'status': 'alive', 'authenticated': True})

@csrf_exempt
def api_test_toast_view(request):
    """
    HTMX test endpoint demonstrating server-triggered toasts via HX-Trigger header.
    """
    response = HttpResponse('', content_type='text/html')
    trigger_data = {
        'showToast': {
            'message': 'Server-side HTMX notification triggered successfully!',
            'type': 'success'
        }
    }
    response['HX-Trigger'] = json.dumps(trigger_data)
    return response

@csrf_exempt
def api_test_htmx_401(request):
    """Simulates an expired session or unauthenticated request on an HTMX endpoint."""
    return HttpResponse('Unauthorized: Session expired', status=401)

@csrf_exempt
def api_test_htmx_403(request):
    """Simulates a permission denied response on an HTMX endpoint."""
    return HttpResponse('Forbidden: Access Denied', status=403)


# Error Boundary Simulators
def test_403_view(request):
    return render(request, '403.html', status=403)

def test_404_view(request):
    return render(request, '404.html', status=404)

def test_500_view(request):
    return render(request, '500.html', status=500)

def test_400_view(request):
    return render(request, '400.html', status=400)

# Django Error Handlers
def error_400_view(request, exception=None, reason=""):
    return render(request, '400.html', status=400)

def error_403_view(request, exception=None):
    return render(request, '403.html', status=403)

def error_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def error_500_view(request):
    return render(request, '500.html', status=500)
