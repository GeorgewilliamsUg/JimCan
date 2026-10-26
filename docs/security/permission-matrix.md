# Permission Matrix (Phase 0 Audit)
**Jimcan Operations Dashboard**
**Date:** 2026-10-26  
**Auditor:** Senior Django Security Engineer (Antigravity)

---

## Permission Matrix Key
- **V**: View
- **C**: Create
- **E**: Edit
- **X**: Void / Reverse (Never a physical hard delete; follows financial audit trail)
- *Blank*: No Access (HTTP 403 Forbidden or filtered from querysets)

---

## Proposed Role Matrix (Adjusted to Real App Pages & Models)

| Functional Area & URL Route | Real Schema Models / Artifacts | Owner | Finance | Site Staff | Adjustments & Security Notes from Proposal |
|---|---|---|---|---|---|
| **Dashboard Money-Flow Figures** (`/overview/` KPIs) | Contract values, cost-to-date, gross invoices, balance due | **V** | **V** | | **Aligned.** Must be removed from DOM when Site Staff logs in. |
| **Dashboard Non-Financial Parts** (`/overview/` Feed) | Active build feed, recent activities, milestone progress | **V** | **V** | **V** | **Aligned.** Project feed items must be scoped to assigned builds for Site Staff. |
| **Projects** (`/projects/`) | `Project`, `Milestone`, `PhaseHistory`, `ProjectMember` | **V C E X** | **V** | **V** | **Adjusted:** Scoped to assigned projects only via `ProjectMember`. Site Staff cannot create or edit projects. |
| **Commercial Leads** (`/leads/`) | `Lead`, `LeadActivity`, `Client` | **V C E X** | **V C E** | | **Aligned.** Subject to confirmation at Gate 1 (Question 2). |
| **BOQ Versioned Documents** (`/rates/`, `/boq/`) | `BOQ`, `BOQVersion`, `BOQSection`, `BOQItem` | **V C E X** | **V C E** | **V** | **Adjusted (Split):** Site staff can view BOQ items for field execution, but preliminaries, contingencies, and markup margins are masked. |
| **Master Rate Library** (`/rates/`) | `RateItem`, `Unit`, `Supplier` | **V C E X** | **V C E** | **V** | **Adjusted (Split):** Site staff can view standard rates; only Owner and Finance manage prices and suppliers. |
| **Client Quotes** (`/quotes/`) | `Quote` | **V C E X** | **V C E** | | **Added:** Explicitly tracks client quotations. Finance can only edit draft quotes; issued quotes are frozen. |
| **Client Invoices** (`/invoices/`) | `Invoice`, `InvoiceLine`, `CreditNote`, `RetentionEntry` | **V C E X** | **V C E** | | **Aligned:** Finance may only edit drafts. Issued invoices are immutable; corrections require credit note / reversal. |
| **Project Expenses** (`/expenses/`) | `Expense`, `ExpenseCategory`, `Supplier`, `Payment` | **V C E X** | **V C E** | **V C** | **Aligned:** Site staff can only Create and View their *own* submitted expenses. No edits permitted after submission. |
| **Tax & statutory reports** (`/tax/`) | `TaxPeriod`, `TaxRate`, `StatutoryEntry`, `WithholdingEntry`| **V** | **V** | | **Aligned.** Monthly VAT returns, WHT schedules, statutory compliance. |
| **Site Uploads & Media** (`/files/`) | `File` (photos, site drawings, delivery notes) | **V C E X** | **V** | **V C** | **Aligned.** Site staff can upload field photos; only Owner can void. Exif GPS scrubbed on server. |
| **User & Role Management** (`/settings/users/`)| `auth.User`, `UserProfile`, `auth.Group` | **V C E** | | | **Aligned.** Owner creates accounts and sets roles. Deactivation only (is_active=False); accounts never hard deleted. |
| **Company & App Settings** (`/settings/`, `/setup/`) | `CompanyProfile`, `AppSetting`, `DocumentSequence` | **V E** | | | **Aligned.** Admin setup checklist, numbering sequences, branding. |
| **Security Audit Log** (`/audit/`) | `AuditEvent`, `JobRun` | **V** | | | **Aligned.** Read-only immutable ledger. |
| **Showroom & Styleguide** (`/styleguide/`, `/shell-demo/`) | Templates only | *DEBUG only* | | | **Adjusted:** Strictly restricted to `DEBUG=True`. Must return 404 in production. |
| **Internal Heartbeat & Utility APIs** (`/api/*`) | Session handlers | **V** | **V** | **V** | **Adjusted:** Must require authenticated session. Fake `{authenticated: true}` response removed. |

---

## Detailed Summary of Changes from Original Starting Proposal

1. **Split "BOQ and Rates" into Two Explicit Rows:**
   - *BOQ Versioned Documents:* Full commercial breakdown (overhead, profit, preliminaries, contingencies, tax). Site staff must not see profit margins.
   - *Master Rate Library:* Unit rates for standard building materials (cement, sand, steel, labor). Site staff can view these for measurement.
2. **Explicit "Client Quotes" Category Added:**
   - The backend schema document designates `Quote` as an independent entity issued from a locked `BOQVersion`. Permissions mirror Invoices (drafts editable by Finance; issued quotes locked; voids require Owner approval).
3. **Data Scoping for Site Staff on Projects:**
   - The proposed matrix suggested assigned projects "if an assignment concept already exists". The backend schema document confirms `ProjectMember` exists with `(project, user, role_on_project)`. Site staff views will be strictly filtered to records where `ProjectMember` links the authenticated user to that project.
4. **Hard Gating on Showroom & Test Views:**
   - `/styleguide/`, `/shell-demo/`, and `/test-*` error boundary simulators are currently exposed in URL routing without environment checks. They are now formally marked as accessible **only when `DEBUG is True`**, returning HTTP 404 in production.
5. **Session Heartbeat & HTMX Test Endpoints:**
   - `/api/heartbeat/` and `/api/test-*` currently lack authentication or CSRF protection. In the final matrix, all endpoints require session authentication.
