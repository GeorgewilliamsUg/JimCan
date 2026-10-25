# Jimcan Operations Dashboard: Comprehensive UI State System

**Document:** `docs/design/states.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard App Flow Document.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20App%20Flow%20Document.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`content.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/content.md)
- [`qa-checklist.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/qa-checklist.md)

---

## 1. System-Wide State Principles

To eliminate layout shifts, prevent accidental double-submits, and ensure data integrity during weak site connectivity, the Jimcan Dashboard implements an explicit, reusable 20-state model. Every screen, component, and table row must handle these states consistently.

---

## 2. Reusable State Specifications

### 2.1 Initial Page Loading
- **Trigger:** Browser navigates to a new URL; initial HTML document request in transit.
- **User-Facing Message:** None (visual skeletons indicate structure).
- **Visual Pattern:** Bone-colored pulsating skeleton boxes (`animate-pulse bg-line/60 rounded-md`) matching the exact layout of cards, tables, and metric blocks. Spinner delayed by 300ms to prevent visual flickering on fast loads.
- **Recovery Action:** Automatic on HTTP 200 payload arrival.
- **Accessibility:** Container marked with `aria-busy="true"` and an off-screen announcement: `<span class="sr-only">Loading page content...</span>`.
- **Data Safety:** Form controls disabled until full DOM readiness.

### 2.2 Partial / Fragment Loading (HTMX)
- **Trigger:** User triggers an HTMX action (filter change, pagination, tab switch).
- **User-Facing Message:** Inline spinner within the clicked element.
- **Visual Pattern:** The triggering button or table row receives the `.htmx-request` class: opacity drops to 70%, pointer events disable, and a 16px CSS spinner renders.
- **Recovery Action:** Replaced automatically by the swapped HTML fragment.
- **Accessibility:** `aria-live="polite"` on target container announces updated content.

### 2.3 Saving / Submitting
- **Trigger:** User clicks a form submission button (`Save`, `Submit for Approval`, `Issue Invoice`).
- **User-Facing Message:** Button text updates (e.g., *"Saving..."*, *"Generating PDF..."*).
- **Visual Pattern:** Primary button background remains `safety`, text dims, button receives `disabled` attribute; pointer events are blocked across the entire form.
- **Recovery Action:** Transition to Saved (2.4) or Validation Error (2.7).
- **Data Safety:** Strict anti-double-submit guard prevents duplicate database inserts (critical for financial vouchers and invoices).

### 2.4 Saved / Success
- **Trigger:** Backend returns HTTP 200/201 confirming database write.
- **User-Facing Message:** Specific toast alert (e.g., *"Lead converted to project successfully"*).
- **Visual Pattern:** Brief inline green checkmark icon (`text-go`) on the button, accompanied by a floating Toast banner in top-right corner that auto-dismisses after 4 seconds.
- **Recovery Action:** Returns to idle state; form resets or page redirects.
- **Accessibility:** Screen reader announces: `<div role="status" aria-live="polite">Lead converted successfully.</div>`.

### 2.5 Pristine Empty State
- **Trigger:** A table or list view query returns zero total records across the entire system.
- **User-Facing Message:** Descriptive explanation (e.g., *"No expenses recorded yet. Track field materials and site disbursements by adding your first expense."*).
- **Visual Pattern:** Centered white card with subtle 1px `line` border, 48px muted outline icon, 16px bold title, 14px muted body, and exactly one `ButtonPrimary` (e.g., `Add Expense`).
- **Recovery Action:** Direct click on primary action button.

### 2.6 Filtered Empty State
- **Trigger:** Search term, date range, or status filter yields zero matching records.
- **User-Facing Message:** *"No records match your active filters."*
- **Visual Pattern:** Clean single table row spanning all columns with a clear button: *"Reset Filters"*.
- **Recovery Action:** Clicking "Reset Filters" dispatches `hx-get` to reload default unfiltered view.

### 2.7 Client-Side Form Validation Error
- **Trigger:** User attempts submit with missing required fields or malformed data.
- **User-Facing Message:** Specific field feedback (e.g., *"Phone number must be at least 10 digits"*, *"Amount is required"*).
- **Visual Pattern:** Input border turns `border-danger`, background receives a subtle pink tint (`bg-red-50/20`), 12px red error text appears immediately below input. Summary card appears at top of form.
- **Recovery Action:** Focus is programmatically shifted to the first invalid field.
- **Accessibility:** Input has `aria-invalid="true"` and `aria-describedby="field-id-error"`.

### 2.8 Server-Side Validation Error (Django Form Error)
- **Trigger:** Backend model validation or business rule fails (e.g., *"Invoice numbering counter collision"*).
- **User-Facing Message:** Exact Django form error string rendered directly from backend template partial.
- **Visual Pattern:** Identical to 2.7, maintaining visual continuity between client and server errors.

### 2.9 Server Error 500 (Unhandled Exception)
- **Trigger:** Internal server exception or database drop.
- **User-Facing Message:** *"System encountered an unexpected issue. Our engineering team has been alerted. Error reference: #ERR-8492."*
- **Visual Pattern:** Clean full-page or card-level error alert in high-contrast charcoal and bone. Technical trace is strictly hidden from screen.
- **Recovery Action:** High-visibility `Retry Action` button; secondary link to return to Dashboard.

### 2.10 Network Error & Offline Mode
- **Trigger:** `navigator.onLine === false` or `fetch()` throws connection timeout on weak 3G site connection.
- **User-Facing Message:** Sticky banner: *"You are working offline. Site photos and notes will queue automatically."*
- **Visual Pattern:** Top fixed 36px amber banner with warning triangle icon.
- **Recovery Action:** Automatic reconnection polling every 10 seconds.
- **Data Safety:** Financial creation forms (Invoices, Quotes, Payments) are strictly locked with notice: *"Financial documents cannot be issued while offline to prevent sequence collisions."*

### 2.11 Pending Sync & Upload Retries
- **Trigger:** Cached offline photo or expense queued in browser `IndexedDB`.
- **User-Facing Message:** *"3 items pending upload..."*
- **Visual Pattern:** Pulsing badge on top navigation bar with rotating sync icon.
- **Recovery Action:** Manual "Sync Now" button on `S-90` (Upload Queue).

### 2.12 Upload Failure
- **Trigger:** Upload rejected due to file size > 10MB, corrupted binary, or server storage limit.
- **User-Facing Message:** *"Upload failed: File exceeds maximum allowed size of 10MB. Please resize image and try again."*
- **Visual Pattern:** Red progress bar accompanied by a `Retry` and `Remove` button pair.

### 2.13 Concurrency / Conflict State
- **Trigger:** Two managers edit the same BOQ item or project status simultaneously; optimistic locking detects version mismatch.
- **User-Facing Message:** *"Record Modified by Another User. Another user updated this project while you were editing. Please review their changes before overwriting."*
- **Visual Pattern:** Split-view comparison modal highlighting modified fields in brass.
- **Recovery Action:** Options: *"Reload Latest Version"* or *"Save Copy as Draft"*.

### 2.14 Permission Denied 403
- **Trigger:** Authenticated user navigates to an unauthorized URL (e.g. Site Engineer navigating to `/tax/`).
- **User-Facing Message:** *"Permission Denied. Your user role (Site Engineer) does not have access to financial tax statements."*
- **Visual Pattern:** Centered warning box with shield icon and return home link.

### 2.15 Locked & Frozen Record State
- **Trigger:** Document reaches an irreversible lifecycle milestone (Locked BOQ Version, Issued Invoice, Closed Tax Period).
- **User-Facing Message:** *"Document Locked. Issued on 24 Oct 2026. Financial records are immutable. To adjust figures, issue a revision or credit note."*
- **Visual Pattern:** Subtle padlock icon next to title; status chip `LOCKED` in bone/charcoal; form fields set to `readonly` or replaced with static text. Action buttons hidden or replaced with `Create Revision` / `Issue Credit Note`.

### 2.16 Archived & Soft-Deleted State
- **Trigger:** Record marked `is_deleted = true`.
- **User-Facing Message:** *"Archived Record. This lead was archived on 12 Oct 2026 by George."*
- **Visual Pattern:** Muted grey banner at top of detail card; watermark `ARCHIVED` in background.
- **Recovery Action:** Admin-only button: *"Restore Record"*.

### 2.17 Boundary & Extreme Data States
- **Zero Values:** Rendered as `UGX 0` (never blank, `-`, or null).
- **Negative Balances:** Formatted in brackets with red font: `<span class="text-danger font-mono font-bold">(UGX 4,250,000)</span>`.
- **Very Large Numbers:** Totals in billions format with exact comma spacing (`UGX 1,420,500,000`). On small KPI cards, abbreviates to `1.42B` with tooltip showing exact whole shillings.
- **Long Text Strings:** Overflow handling uses `truncate` with `title="..."` attribute or multi-line clamp (`line-clamp-2`).
- **Missing Optional Data:** Renders a clean muted em-dash (`—`), never empty whitespace or raw `None` / `null`.

---

## 3. Open Questions Relevant to States
1. `[OQ-09]`: Confirm whether the session timeout warning threshold should be 59 minutes (for 60-min sessions) or shorter for shared site tablets.

---

## 4. Change Log
- **24 October 2026 (v0.1):** Standardized 20-state model specified with triggers, messages, visual patterns, and safety rules.

*Unresolved items must not be treated as approved requirements.*
