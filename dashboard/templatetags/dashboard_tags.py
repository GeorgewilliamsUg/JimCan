"""
Template filters and tags for Jimcan Operations Dashboard Redesign.
Implements exact currency formatting (ugx_compact, ugx_full), accessible word formatting,
division-by-zero guarded calculations, and status badge helpers.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone

register = template.Library()

def _to_decimal(val):
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    val_str = str(val).replace(',', '').strip()
    if not val_str:
        return None
    try:
        return Decimal(val_str)
    except (InvalidOperation, ValueError):
        return None

@register.filter(name='ugx_compact')
def ugx_compact(value):
    """
    Renders compact UGX:
    - >= 1,000,000,000: 2 decimals, trailing zeros trimmed (e.g. 1.34B, 1.3B, 1B)
    - >= 1,000,000: 1 decimal, trailing zero kept (e.g. 247.8M, 42.0M)
    - < 1,000,000: full number with thousands separators (e.g. 420,000)
    - None / invalid: '-' with aria-label="Not available"
    """
    d = _to_decimal(value)
    if d is None:
        return mark_safe('<span aria-label="Not available" class="text-muted">-</span>')
    
    sign = '-' if d < 0 else ''
    d = abs(d)

    if d >= Decimal('1000000000'):
        b = (d / Decimal('1000000000')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        s = f'{b:.2f}'.rstrip('0').rstrip('.')
        return f'{sign}{s}B'
    elif d >= Decimal('1000000'):
        m = (d / Decimal('1000000')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return f'{sign}{m:.1f}M'
    else:
        full = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return f'{sign}{full:,}'

@register.filter(name='ugx_full')
def ugx_full(value):
    """
    Renders full currency amount with thousands separators.
    None renders '-' with aria-label="Not available".
    """
    d = _to_decimal(value)
    if d is None:
        return mark_safe('<span aria-label="Not available" class="text-muted">-</span>')
    full = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return f'{full:,}'

@register.filter(name='ugx_words')
def ugx_words(value):
    """
    Spoken words representation for accessible screen reader aria-labels.
    e.g. '1 billion 340 million Uganda shillings'
    """
    d = _to_decimal(value)
    if d is None:
        return 'Not available'
    n = int(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    if n == 0:
        return '0 Uganda shillings'
    
    parts = []
    if n < 0:
        parts.append('negative')
        n = abs(n)
        
    billions = n // 1000000000
    rem = n % 1000000000
    millions = rem // 1000000
    rem %= 1000000
    thousands = rem // 1000
    units = rem % 1000
    
    if billions:
        parts.append(f'{billions} billion')
    if millions:
        parts.append(f'{millions} million')
    if thousands:
        parts.append(f'{thousands} thousand')
    if units:
        parts.append(f'{units}')
        
    return ' '.join(parts) + ' Uganda shillings'

@register.filter(name='calc_pct')
def calc_pct(part, whole):
    """
    Calculates percentage (part / whole * 100) rounded to 1 decimal place.
    Guards against division by zero.
    """
    p = _to_decimal(part)
    w = _to_decimal(whole)
    if not p or not w or w == 0:
        return '0.0'
    res = (p / w * Decimal('100')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return f'{res:.1f}'

@register.filter(name='clamp_pct')
def clamp_pct(part, whole):
    """
    Calculates percentage clamped between 0 and 100 for bar widths.
    """
    p = _to_decimal(part)
    w = _to_decimal(whole)
    if not p or not w or w == 0:
        return '0'
    pct = (p / w * Decimal('100')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    clamped = max(Decimal('0'), min(Decimal('100'), pct))
    return f'{clamped:.1f}'

@register.filter(name='calc_diff')
def calc_diff(val1, val2):
    """
    Returns absolute difference between two numbers.
    """
    v1 = _to_decimal(val1) or Decimal('0')
    v2 = _to_decimal(val2) or Decimal('0')
    return abs(v1 - v2)

@register.filter(name='is_greater')
def is_greater(val1, val2):
    """
    Checks if val1 > val2.
    """
    v1 = _to_decimal(val1) or Decimal('0')
    v2 = _to_decimal(val2) or Decimal('0')
    return v1 > v2

@register.filter(name='overdue_count')
def overdue_count(invoices):
    """
    Counts invoices that are overdue (have an outstanding balance or overdue status).
    """
    if not invoices:
        return 0
    count = 0
    for inv in invoices:
        balance = _to_decimal(inv.get('balance_due_ugx', 0))
        status = str(inv.get('status', '')).lower()
        if (balance and balance > 0) or status == 'overdue':
            count += 1
    return count

@register.simple_tag
def time_greeting():
    """
    Returns time-based greeting using local time in active timezone.
    Before 12:00 -> 'Good morning'
    Before 17:00 -> 'Good afternoon'
    Otherwise   -> 'Good evening'
    """
    local_now = timezone.localtime()
    hour = local_now.hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"

@register.filter(name='status_badge')
def status_badge(status_raw):
    """
    Maps existing status values to standard badge markup:
    - Paid or on track: text --green on --green-tint
    - Overdue or over budget: text --red on --red-tint
    - Pending or on hold: text --amber on --amber-tint
    - Neutral or draft: text --text-muted on --paper-sunk
    """
    if not status_raw:
        return mark_safe('<span class="status-badge status-neutral"><span class="badge-dot"></span>Not available</span>')
    
    st = str(status_raw).strip().lower().replace('_', ' ')
    
    # Mapping table
    # Green (paid or on track)
    if st in ('paid', 'won', 'active', 'foundation', 'superstructure', 'finishes', 'brief', 'design', 'handover', 'completed'):
        label = st.title()
        variant = 'status-green'
    # Red (overdue or over budget)
    elif st in ('overdue', 'partially paid', 'part paid', 'lost', 'failed', 'blocked'):
        label = st.title()
        variant = 'status-red'
    # Amber (pending or on hold)
    elif st in ('pending', 'quoted', 'site visit', 'sent', 'on hold', 'review'):
        label = st.title()
        variant = 'status-amber'
    # Neutral (draft, new, void)
    elif st in ('draft', 'new', 'void', 'archived'):
        label = st.title()
        variant = 'status-neutral'
    else:
        # Fallback to neutral per brief requirement
        label = st.title()
        variant = 'status-neutral'
        
    return mark_safe(f'<span class="status-badge {variant}"><span class="badge-dot"></span>{label}</span>')
