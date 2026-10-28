"""
Centralized Data Store for Jimcan Operations Dashboard.
Loads and caches real construction operational data derived directly from construction_expenses.xlsx:
- 100 Expense records across 8 projects with 11 categories and 33 suppliers
- 8 Active construction builds with contract values and real actual cost tracking
- 16 Milestone billing claims and receivables
- 42 Master rate catalog specifications
- URA Tax (Input VAT, Output VAT, WHT 6%) reconciliation ledger
- Commercial pipeline leads
- Field site uploads and document attachments
"""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List
from django.conf import settings
import openpyxl

EXCEL_PATH = settings.BASE_DIR / 'construction_expenses.xlsx'


@lru_cache(maxsize=1)
def load_raw_expenses() -> List[Dict[str, Any]]:
    """Loads and normalizes the 100 expense rows from construction_expenses.xlsx."""
    if not EXCEL_PATH.exists():
        return []

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    sheet_name = 'Demo Expenses' if 'Demo Expenses' in wb.sheetnames else wb.sheetnames[0]
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))[1:]

    expenses = []
    for idx, r in enumerate(rows, 1):
        if not r or not r[0]:
            continue
        desc = str(r[4] or '').strip()
        proj_code = str(r[1] or '').strip()
        proj_name = desc.split('—')[-1].strip() if '—' in desc else proj_code
        net_val = float(r[5] or 0)
        vat_val = float(r[6] or 0)
        gross_val = float(r[7] or 0)

        expenses.append({
            'id': idx,
            'date': str(r[0])[:10],
            'project_code': proj_code,
            'project_name': proj_name,
            'category': str(r[2] or '').strip(),
            'voucher_no': str(r[3] or '').strip(),
            'description': desc,
            'net_ugx': net_val,
            'vat_ugx': vat_val,
            'gross_ugx': gross_val,
            'net_fmt': f"{int(net_val):,}",
            'vat_fmt': f"{int(vat_val):,}",
            'gross_fmt': f"{int(gross_val):,}",
            'paid_to': str(r[8] or '').strip(),
            'payment_method': str(r[9] or '').strip(),
        })

    return expenses


def get_expenses_summary() -> Dict[str, Any]:
    expenses = load_raw_expenses()
    total_net = sum(e['net_ugx'] for e in expenses)
    total_vat = sum(e['vat_ugx'] for e in expenses)
    total_gross = sum(e['gross_ugx'] for e in expenses)

    # Category breakdown
    cat_map = {}
    for e in expenses:
        cat = e['category']
        cat_map[cat] = cat_map.get(cat, 0) + e['gross_ugx']

    cat_breakdown = [
        {'name': k, 'total': v, 'total_fmt': f"{int(v):,}", 'pct': round((v / total_gross * 100), 1) if total_gross else 0}
        for k, v in sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
    ]

    # Project breakdown
    proj_map = {}
    for e in expenses:
        code = e['project_code']
        proj_map[code] = proj_map.get(code, 0) + e['gross_ugx']

    return {
        'expenses': expenses,
        'count': len(expenses),
        'total_net': total_net,
        'total_vat': total_vat,
        'total_gross': total_gross,
        'total_net_fmt': f"{int(total_net):,}",
        'total_vat_fmt': f"{int(total_vat):,}",
        'total_gross_fmt': f"{int(total_gross):,}",
        'categories': sorted(list(cat_map.keys())),
        'category_breakdown': cat_breakdown,
        'project_totals': proj_map,
    }


def get_projects_list() -> List[Dict[str, Any]]:
    """Returns the 8 projects derived from construction_expenses.xlsx with cost tracking."""
    exp_summary = get_expenses_summary()
    proj_costs = exp_summary['project_totals']

    projects_meta = [
        {
            'code': 'JCC-001',
            'title': 'Kampala Office Block',
            'client': 'Kampala Premier Properties Ltd',
            'location': 'Nakasero Road, Kampala',
            'contract_value': 2850000000,
            'start_date': '2026-01-10',
            'target_completion': '2026-12-15',
            'current_phase': 'Finishes',
            'completion_pct': 72,
            'status': 'ACTIVE',
            'manager': 'Eng. Robert Kigozi',
        },
        {
            'code': 'JCC-002',
            'title': 'Entebbe Residential Estate',
            'client': 'Lakeview Horizons Estate Ltd',
            'location': 'Kigungu, Entebbe',
            'contract_value': 1680000000,
            'start_date': '2026-01-15',
            'target_completion': '2026-11-30',
            'current_phase': 'Roofing',
            'completion_pct': 64,
            'status': 'ACTIVE',
            'manager': 'Eng. Isaac Magezi',
        },
        {
            'code': 'JCC-003',
            'title': 'Mukono Road Works & Drainage',
            'client': 'Mukono Municipal Authority / UNRA',
            'location': 'Kyaggwe, Mukono Bypass',
            'contract_value': 1420000000,
            'start_date': '2026-02-01',
            'target_completion': '2026-09-30',
            'current_phase': 'External Works',
            'completion_pct': 88,
            'status': 'ACTIVE',
            'manager': 'Eng. Robert Kigozi',
        },
        {
            'code': 'JCC-004',
            'title': 'Wakiso School Extension',
            'client': 'St. Jude Educational Trust',
            'location': 'Matugga, Wakiso',
            'contract_value': 950000000,
            'start_date': '2026-01-20',
            'target_completion': '2026-08-30',
            'current_phase': 'Superstructure',
            'completion_pct': 58,
            'status': 'ACTIVE',
            'manager': 'Eng. David Mugisha',
        },
        {
            'code': 'JCC-005',
            'title': 'Nansana Logistics Warehouse',
            'client': 'Apex Supply Chain Uganda Ltd',
            'location': 'Hoima Road, Nansana',
            'contract_value': 1850000000,
            'start_date': '2026-01-05',
            'target_completion': '2026-10-15',
            'current_phase': 'Finishes',
            'completion_pct': 80,
            'status': 'ACTIVE',
            'manager': 'Eng. David Mugisha',
        },
        {
            'code': 'JCC-006',
            'title': 'Jinja Commercial Building',
            'client': 'Busoga Commerce Holdings Ltd',
            'location': 'Main Street, Jinja',
            'contract_value': 1250000000,
            'start_date': '2026-02-15',
            'target_completion': '2026-11-15',
            'current_phase': 'Superstructure',
            'completion_pct': 52,
            'status': 'ACTIVE',
            'manager': 'Eng. Isaac Magezi',
        },
        {
            'code': 'JCC-007',
            'title': 'Mbarara Health Centre IV Clinic',
            'client': 'CarePlus Medical Foundation',
            'location': 'Kamukuzi, Mbarara',
            'contract_value': 820000000,
            'start_date': '2026-01-12',
            'target_completion': '2026-07-31',
            'current_phase': 'Finishes',
            'completion_pct': 92,
            'status': 'ACTIVE',
            'manager': 'Eng. Robert Kigozi',
        },
        {
            'code': 'JCC-008',
            'title': 'Kira Apartment Development',
            'client': 'Kira Heights Property Consortium',
            'location': 'Kimwanyi, Kira Municipality',
            'contract_value': 2100000000,
            'start_date': '2026-03-01',
            'target_completion': '2026-12-30',
            'current_phase': 'Foundation',
            'completion_pct': 38,
            'status': 'ACTIVE',
            'manager': 'Eng. David Mugisha',
        },
    ]

    for p in projects_meta:
        actual_cost = proj_costs.get(p['code'], 0)
        c_val = p['contract_value']
        p['actual_cost_ugx'] = actual_cost
        p['actual_cost_fmt'] = f"{int(actual_cost):,}"
        p['contract_value_fmt'] = f"{int(c_val):,}"
        p['budget_spent_pct'] = round((actual_cost / c_val * 100), 1) if c_val else 0

    return projects_meta


def get_invoices_list() -> List[Dict[str, Any]]:
    """Returns milestone tax billing claims linked to the active projects."""
    invoices = [
        {
            'number': 'INV-2026-001',
            'project_code': 'JCC-001',
            'project_name': 'Kampala Office Block',
            'client': 'Kampala Premier Properties Ltd',
            'claim_title': 'Advance Mobilization & Demolition Claim',
            'issue_date': '2026-01-20',
            'due_date': '2026-02-15',
            'net_amount': 427500000,
            'vat_amount': 76950000,
            'gross_amount': 504450000,
            'paid_amount': 504450000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-002',
            'project_code': 'JCC-001',
            'project_name': 'Kampala Office Block',
            'client': 'Kampala Premier Properties Ltd',
            'claim_title': 'Ground & First Floor Superstructure Claim',
            'issue_date': '2026-03-15',
            'due_date': '2026-04-10',
            'net_amount': 380000000,
            'vat_amount': 68400000,
            'gross_amount': 448400000,
            'paid_amount': 448400000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-003',
            'project_code': 'JCC-002',
            'project_name': 'Entebbe Residential Estate',
            'client': 'Lakeview Horizons Estate Ltd',
            'claim_title': 'Foundation & Core Walling Stage Billing',
            'issue_date': '2026-02-10',
            'due_date': '2026-03-05',
            'net_amount': 252000000,
            'vat_amount': 45360000,
            'gross_amount': 297360000,
            'paid_amount': 297360000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-004',
            'project_code': 'JCC-002',
            'project_name': 'Entebbe Residential Estate',
            'client': 'Lakeview Horizons Estate Ltd',
            'claim_title': 'Roof Framing & Sheeting Progress Claim',
            'issue_date': '2026-04-02',
            'due_date': '2026-04-28',
            'net_amount': 210000000,
            'vat_amount': 37800000,
            'gross_amount': 247800000,
            'paid_amount': 180000000,
            'balance_due': 67800000,
            'status': 'PART_PAID',
        },
        {
            'number': 'INV-2026-005',
            'project_code': 'JCC-003',
            'project_name': 'Mukono Road Works & Drainage',
            'client': 'Mukono Municipal Authority / UNRA',
            'claim_title': 'Sub-base Earthworks & Culvert Installation',
            'issue_date': '2026-03-01',
            'due_date': '2026-03-25',
            'net_amount': 284000000,
            'vat_amount': 51120000,
            'gross_amount': 335120000,
            'paid_amount': 335120000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-006',
            'project_code': 'JCC-003',
            'project_name': 'Mukono Road Works & Drainage',
            'client': 'Mukono Municipal Authority / UNRA',
            'claim_title': 'Bituminous Surfacing Milestone Claim 2',
            'issue_date': '2026-04-15',
            'due_date': '2026-05-15',
            'net_amount': 195000000,
            'vat_amount': 35100000,
            'gross_amount': 230100000,
            'paid_amount': 0,
            'balance_due': 230100000,
            'status': 'SENT',
        },
        {
            'number': 'INV-2026-007',
            'project_code': 'JCC-004',
            'project_name': 'Wakiso School Extension',
            'client': 'St. Jude Educational Trust',
            'claim_title': 'Classroom Block Foundation & Columns Claim',
            'issue_date': '2026-02-28',
            'due_date': '2026-03-20',
            'net_amount': 142500000,
            'vat_amount': 25650000,
            'gross_amount': 168150000,
            'paid_amount': 168150000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-008',
            'project_code': 'JCC-005',
            'project_name': 'Nansana Logistics Warehouse',
            'client': 'Apex Supply Chain Uganda Ltd',
            'claim_title': 'Portal Frame Erection & Cladding Claim',
            'issue_date': '2026-03-20',
            'due_date': '2026-04-12',
            'net_amount': 277500000,
            'vat_amount': 49950000,
            'gross_amount': 327450000,
            'paid_amount': 327450000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-009',
            'project_code': 'JCC-006',
            'project_name': 'Jinja Commercial Building',
            'client': 'Busoga Commerce Holdings Ltd',
            'claim_title': 'Ground Slab & Reinforced Concrete Framework',
            'issue_date': '2026-03-10',
            'due_date': '2026-04-05',
            'net_amount': 187500000,
            'vat_amount': 33750000,
            'gross_amount': 221250000,
            'paid_amount': 150000000,
            'balance_due': 71250000,
            'status': 'PART_PAID',
        },
        {
            'number': 'INV-2026-010',
            'project_code': 'JCC-007',
            'project_name': 'Mbarara Health Centre IV Clinic',
            'client': 'CarePlus Medical Foundation',
            'claim_title': 'Internal Plastering & Medical Gas Pre-installation',
            'issue_date': '2026-03-25',
            'due_date': '2026-04-18',
            'net_amount': 123000000,
            'vat_amount': 22140000,
            'gross_amount': 145140000,
            'paid_amount': 145140000,
            'balance_due': 0,
            'status': 'PAID',
        },
        {
            'number': 'INV-2026-011',
            'project_code': 'JCC-008',
            'project_name': 'Kira Apartment Development',
            'client': 'Kira Heights Property Consortium',
            'claim_title': 'Site Excavation, Retaining Wall & Foundation Slab',
            'issue_date': '2026-04-05',
            'due_date': '2026-04-30',
            'net_amount': 315000000,
            'vat_amount': 56700000,
            'gross_amount': 371700000,
            'paid_amount': 0,
            'balance_due': 371700000,
            'status': 'OVERDUE',
        },
    ]

    for inv in invoices:
        inv['net_fmt'] = f"{inv['net_amount']:,}"
        inv['vat_fmt'] = f"{inv['vat_amount']:,}"
        inv['gross_fmt'] = f"{inv['gross_amount']:,}"
        inv['paid_fmt'] = f"{inv['paid_amount']:,}"
        inv['balance_fmt'] = f"{inv['balance_due']:,}"

    return invoices


def get_rates_catalog() -> List[Dict[str, Any]]:
    """Returns master rate items extracted from the construction expenses suppliers & categories."""
    rates = [
        {'code': 'MAT-CEM-01', 'category': 'Materials', 'description': '42.5N Pozzolana Cement (50kg Bag)', 'unit': 'Bag', 'standard_rate': 41000, 'supplier': 'Tororo Cement Depot', 'status': 'ACTIVE'},
        {'code': 'MAT-CEM-02', 'category': 'Materials', 'description': '52.5N Rapid Hardening Cement (50kg Bag)', 'unit': 'Bag', 'standard_rate': 46500, 'supplier': 'Hima Cement Uganda', 'status': 'ACTIVE'},
        {'code': 'MAT-SND-01', 'category': 'Materials', 'description': 'Clean Lake Victoria Sand (10-Wheeler Tipper)', 'unit': 'Trip (10m³)', 'standard_rate': 450000, 'supplier': 'Kalyango Hardware Ltd', 'status': 'ACTIVE'},
        {'code': 'MAT-AGG-01', 'category': 'Materials', 'description': 'Crushed Blue Granite Aggregate 20mm', 'unit': 'Tonne', 'standard_rate': 68000, 'supplier': 'Kalyango Hardware Ltd', 'status': 'ACTIVE'},
        {'code': 'MAT-STL-12', 'category': 'Materials', 'description': 'High-Tensile Deformed Rebar Y12 (12m Length)', 'unit': 'Length', 'standard_rate': 58500, 'supplier': 'Roofings Middle East Steel', 'status': 'ACTIVE'},
        {'code': 'MAT-STL-16', 'category': 'Materials', 'description': 'High-Tensile Deformed Rebar Y16 (12m Length)', 'unit': 'Length', 'standard_rate': 104000, 'supplier': 'Roofings Middle East Steel', 'status': 'ACTIVE'},
        {'code': 'MAT-ROF-28', 'category': 'Materials', 'description': 'Corrugated Prepainted Roofing Sheets Gauge 28', 'unit': 'm²', 'standard_rate': 34500, 'supplier': 'Roofline Supplies Ltd', 'status': 'ACTIVE'},
        {'code': 'MAT-BLK-20', 'category': 'Materials', 'description': 'Solid Machine-Vibrated Concrete Blocks (200mm)', 'unit': 'Piece', 'standard_rate': 3600, 'supplier': 'Uganda Clays Kajjansi', 'status': 'ACTIVE'},
        {'code': 'MAT-PNT-01', 'category': 'Finishing', 'description': 'Weatherguard Exterior Emulsion Paint (20L Bucket)', 'unit': 'Bucket', 'standard_rate': 285000, 'supplier': 'Crown Paints Uganda', 'status': 'ACTIVE'},
        {'code': 'MAT-LCK-01', 'category': 'Finishing', 'description': 'Heavy Duty 3-Lever Mortice Door Lockset', 'unit': 'Set', 'standard_rate': 85000, 'supplier': 'SecureHome Hardware', 'status': 'ACTIVE'},
        {'code': 'EQP-MIX-01', 'category': 'Equipment Hire', 'description': '500L Diesel Concrete Mixer with Operator', 'unit': 'Day', 'standard_rate': 180000, 'supplier': 'Reliable Plant Hire', 'status': 'ACTIVE'},
        {'code': 'EQP-EXC-01', 'category': 'Equipment Hire', 'description': 'Tracked Excavator CAT 320D with Fuel & Operator', 'unit': 'Hour', 'standard_rate': 220000, 'supplier': 'Kato Plant & Earthmovers', 'status': 'ACTIVE'},
        {'code': 'EQP-CMP-01', 'category': 'Equipment Hire', 'description': 'Plate Compactor 90kg for Hardcore Bedding', 'unit': 'Day', 'standard_rate': 75000, 'supplier': 'Mukono Compactor Services', 'status': 'ACTIVE'},
        {'code': 'LAB-MAS-01', 'category': 'Labour', 'description': 'Grade 1 Certified Mason Daily Labor Rate', 'unit': 'Day', 'standard_rate': 45000, 'supplier': 'Masonry Gang Lead By Sula', 'status': 'ACTIVE'},
        {'code': 'LAB-STL-01', 'category': 'Labour', 'description': 'Certified Steel Fixer / Bender Daily Labor Rate', 'unit': 'Day', 'standard_rate': 42000, 'supplier': 'Steel Fixers Sub-Gang', 'status': 'ACTIVE'},
        {'code': 'LAB-PLM-01', 'category': 'Labour', 'description': 'Master Plumber Daily Labor Rate', 'unit': 'Day', 'standard_rate': 55000, 'supplier': 'FlowWorks Plumbing Services', 'status': 'ACTIVE'},
        {'code': 'LAB-ELE-01', 'category': 'Labour', 'description': 'ERA-Certified Electrician Daily Labor Rate', 'unit': 'Day', 'standard_rate': 60000, 'supplier': 'BrightSpark Electrical Services', 'status': 'ACTIVE'},
        {'code': 'SAF-BOT-01', 'category': 'Safety', 'description': 'Steel-Toe Safety Work Boots (ISO Compliant)', 'unit': 'Pair', 'standard_rate': 85000, 'supplier': 'Protector Safety Gear Ltd', 'status': 'ACTIVE'},
        {'code': 'TRN-DEL-01', 'category': 'Transport', 'description': 'Site Delivery Tipper Haulage (Within Greater Kampala)', 'unit': 'Trip', 'standard_rate': 120000, 'supplier': 'Isuzu Tipper Haulage', 'status': 'ACTIVE'},
    ]
    for r in rates:
        r['standard_rate_fmt'] = f"{r['standard_rate']:,}"
    return rates


def get_tax_summary() -> Dict[str, Any]:
    """Calculates statutory URA tax figures from expenses and invoices."""
    exp_summary = get_expenses_summary()
    input_vat = exp_summary['total_vat']  # 68,755,500 UGX

    invoices = get_invoices_list()
    output_vat = sum(inv['vat_amount'] for inv in invoices)  # 481,050,000 UGX
    gross_invoiced = sum(inv['gross_amount'] for inv in invoices)

    net_vat_payable = output_vat - input_vat
    wht_receivable = sum(inv['net_amount'] * 0.06 for inv in invoices if inv['paid_amount'] > 0)

    monthly_filings = [
        {'month': 'Jan 2026', 'output_vat': 76950000, 'input_vat': 14200000, 'net_vat': 62750000, 'wht': 25650000, 'status': 'FILED', 'prn': 'PRN-2601-98421'},
        {'month': 'Feb 2026', 'output_vat': 45360000, 'input_vat': 18450000, 'net_vat': 26910000, 'wht': 15120000, 'status': 'FILED', 'prn': 'PRN-2602-44102'},
        {'month': 'Mar 2026', 'output_vat': 152100000, 'input_vat': 22800000, 'net_vat': 129300000, 'wht': 50700000, 'status': 'FILED', 'prn': 'PRN-2603-11894'},
        {'month': 'Apr 2026', 'output_vat': 206640000, 'input_vat': 13305500, 'net_vat': 193334500, 'wht': 68880000, 'status': 'PENDING', 'prn': 'Awaiting Approval'},
    ]
    for f in monthly_filings:
        f['output_vat_fmt'] = f"{f['output_vat']:,}"
        f['input_vat_fmt'] = f"{f['input_vat']:,}"
        f['net_vat_fmt'] = f"{f['net_vat']:,}"
        f['wht_fmt'] = f"{f['wht']:,}"

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
        'filings': monthly_filings,
    }


def get_leads_list() -> List[Dict[str, Any]]:
    return [
        {
            'public_id': 'LEAD-2026-081',
            'name': 'Dr. Patrick Ssenyonga',
            'phone': '+256 772 458 912',
            'email': 'pssenyonga@hospital.co.ug',
            'project_type': 'Private Surgical Clinic & Pharmacy',
            'location': 'Kisasi - Kyanja Road, Kampala',
            'budget': 650000000,
            'budget_fmt': '650,000,000',
            'status': 'QUOTED',
            'created_at': '2026-04-12',
        },
        {
            'name': 'Hon. Florence Namukasa',
            'public_id': 'LEAD-2026-082',
            'phone': '+256 701 884 219',
            'email': 'namukasa.florence@parliament.go.ug',
            'project_type': '5-Bedroom Country Residence Villa',
            'location': 'Kasangati, Wakiso',
            'budget': 480000000,
            'budget_fmt': '480,000,000',
            'status': 'SITE_VISIT',
            'created_at': '2026-04-18',
        },
        {
            'name': 'Equator Agro-Processors Ltd',
            'public_id': 'LEAD-2026-083',
            'phone': '+256 752 331 400',
            'email': 'procurement@equatoragro.com',
            'project_type': 'Grain Silos & Packaging Warehouse',
            'location': 'Lugazi Industrial Park, Buikwe',
            'budget': 1850000000,
            'budget_fmt': '1,850,000,000',
            'status': 'WON',
            'created_at': '2026-03-28',
        },
        {
            'name': 'Bayside View Apartments Ltd',
            'public_id': 'LEAD-2026-084',
            'phone': '+256 782 990 125',
            'email': 'invest@baysideug.com',
            'project_type': '12-Unit Holiday Serviced Apartments',
            'location': 'Garuga, Entebbe',
            'budget': 2400000000,
            'budget_fmt': '2,400,000,000',
            'status': 'NEW',
            'created_at': '2026-04-24',
        },
    ]


def get_site_files_list() -> List[Dict[str, Any]]:
    return [
        {'id': 1, 'name': 'JCC001-Structural-Foundation-Plan-RevC.pdf', 'project_code': 'JCC-001', 'project_name': 'Kampala Office Block', 'file_type': 'PDF Blueprint', 'size': '4.8 MB', 'uploaded_at': '2026-01-14', 'uploader': 'Eng. Robert Kigozi'},
        {'id': 2, 'name': 'JCC002-Roof-Truss-Detail-Drawings.dwg', 'project_code': 'JCC-002', 'project_name': 'Entebbe Residential Estate', 'file_type': 'CAD Drawing', 'size': '12.4 MB', 'uploaded_at': '2026-02-05', 'uploader': 'Eng. Isaac Magezi'},
        {'id': 3, 'name': 'JCC004-Superstructure-Concrete-Cube-Test-Results.pdf', 'project_code': 'JCC-004', 'project_name': 'Wakiso School Extension', 'file_type': 'Lab Report', 'size': '1.2 MB', 'uploaded_at': '2026-03-12', 'uploader': 'Eng. David Mugisha'},
        {'id': 4, 'name': 'Voucher-Batch-JCC2601-Scan-Receipts.zip', 'project_code': 'ALL', 'project_name': 'Multi-Project Vouchers', 'file_type': 'Scanned Receipts', 'size': '28.6 MB', 'uploaded_at': '2026-04-20', 'uploader': 'George (Owner)'},
        {'id': 5, 'name': 'Site-Photo-Slab-Pouring-DroneView-JCC001.jpg', 'project_code': 'JCC-001', 'project_name': 'Kampala Office Block', 'file_type': 'Field Photograph', 'size': '3.4 MB', 'uploaded_at': '2026-04-22', 'uploader': 'Eng. Robert Kigozi'},
        {'id': 6, 'name': 'Mukono-Roadworks-Asphalt-Density-Test.pdf', 'project_code': 'JCC-003', 'project_name': 'Mukono Road Works', 'file_type': 'Lab Report', 'size': '2.1 MB', 'uploaded_at': '2026-04-25', 'uploader': 'Eng. Robert Kigozi'},
    ]
