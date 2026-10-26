# Model Classification
**Jimcan Operations Dashboard**
**Date:** 2026-10-26  
**Auditor:** Senior Django Security Engineer (Antigravity)

---

## 1. Classification Overview

To enforce strict security boundaries, financial integrity rules (Phase 6), and data scoping (Phase 5), all application models are categorized into four classes:

1. **Financial**: Invoices, expenses, rates, BOQ versions, tax filings, payments, and budgets. **Never hard deleted; edits restricted to draft stages; issued records are locked and require immutable reversal/credit note mechanisms.**
2. **Operational**: Construction builds, client inquiries, field site uploads, progress milestones, and suppliers. **Soft deleted with audit history; access scoped by role and project assignment.**
3. **Identity & Access**: User accounts, credentials, role groups, permissions, and sessions. **Subject to MFA, strict lockout rules, no superusers, and least privilege.**
4. **System & Other**: Company configuration, document sequence generators, email queues, and immutable audit ledgers.

---

## 2. Complete Model Directory & Proposed Classification

### Class 1: Financial Models (Highest Integrity Level)

| Model Name | Core Purpose | Immutability & Deletion Policy | EFRIS / Statutory Flags |
|---|---|---|---|
| `Invoice` | Client milestone billings and tax invoices | **Never hard deleted.** Drafts editable; issued invoices frozen. Corrections via `CreditNote`. | Tracks statutory VAT 18%, WHT 6%. Needs decision on EFRIS FDN / QR code. |
| `InvoiceLine` | Individual line items on an invoice | Child of `Invoice`. Locked when parent invoice is issued. | VAT-applicable boolean flag. |
| `Payment` | Cash/bank remittances received against invoices | **Append-only.** Payments are never edited or deleted. Reversals create negative balancing entries with reason. | Tracks payment reference, bank/mobile money account. |
| `CreditNote` | Official invoice reversals, cancellations, and discounts | **Append-only.** Numbered sequentially, immutable once issued. | Essential for EFRIS compliance if invoices are fiscalized. |
| `WithholdingEntry`| Withholding Tax (WHT 6%) deduction tracking | Immutable once filed. Linked to Invoice or Expense. | Required for URA WHT returns and credit certificates. |
| `RetentionEntry` | Construction defects liability retention (held/released) | Append-only ledger linked to parent invoice. | Tracks contractual retention funds. |
| `Expense` | Project direct material/labor disbursements and overheads | **Never hard deleted.** Drafts editable; submitted expenses locked. Void requires Owner reversal. | Tracks VAT claimable status, net, VAT, and gross totals. |
| `ExpenseCategory`| Classification of costs (direct cost vs overhead) | Soft delete; cannot delete if active expenses reference it. | Categorization for tax deduction rules. |
| `BOQ` | Bill of Quantities container (linked to Project or Lead) | Soft delete permitted only while in preliminary draft. | Base container for commercial pricing. |
| `BOQVersion` | Versioned schedule of quantities, preliminaries, markup | **Frozen at lock.** SHA-256 content hash verified nightly. | Contains preliminaries %, contingency %, overhead/profit %, and VAT rate. |
| `BOQSection` | Work trade breakdown (e.g. Substructure, Masonry) | Frozen when parent `BOQVersion` is locked. | Subtotal monetary values. |
| `BOQItem` | Granular measured items with quantity, rate, amount | Frozen when parent `BOQVersion` is locked. Quantity, rate, and amount enforced >= 0. | VAT-exempt flag, standard rate reference. |
| `RateItem` | Master catalog of material, labor, and plant unit rates | Historical tracking via `RateHistory`. Rates cannot be deleted if referenced in issued BOQs. | Standard unit price library. |
| `RateHistory` | Audit trail of rate card price changes | **Append-only.** Logs old rate, new rate, user, timestamp. | Internal audit of price adjustments. |
| `Quote` | Commercial estimate issued to prospective clients | Drafts editable by Finance; issued quotes locked. Voids require Owner authorization. | Copies frozen pricing from locked `BOQVersion`. |
| `TaxPeriod` | Monthly statutory tax filing window (VAT, PAYE, WHT) | Once status is `filed`, locked permanently with snapshot of filed figures. | Official URA monthly tax reconciliation. |
| `TaxRate` | Statutory tax brackets (VAT 18%, WHT 6%, NSSF 10%/5%) | Date-ranged effective validity. Historical records immutable. | Statutory tax configuration. |
| `StatutoryEntry` | Statutory liability ledger (PAYE, NSSF) | Append-only remittances. | Statutory compliance. |

---

### Class 2: Operational Models

| Model Name | Core Purpose | Access & Scoping Policy |
|---|---|---|
| `Project` | Construction builds under contract | Scoped to assigned `ProjectMember` for Site Staff; company-wide for Owner/Finance. |
| `ProjectMember` | Maps users to projects with roles (`manager`, `engineer`) | Owner-managed. Dictates data access boundaries for Site Staff. |
| `Milestone` | Schedule targets and contractual delivery phases | Site staff can view; Owner/Finance can update completion dates. |
| `PhaseHistory` | Audit log of build phase progression | **Append-only.** Logs stage progression (Foundation, Superstructure, Finishes). |
| `VariationOrder`| Scope of work adjustments requested by client | Scoped to project. Requires Owner approval before conversion to Quote. |
| `Client` | Commercial clients and government entities | Owner and Finance view/edit. Includes TIN and withholding agent status. |
| `Contact` | Key individuals associated with clients | Soft delete allowed. |
| `Lead` | Sales inquiries, site visit requests, commercial leads | Owner and Finance access. Status progression tracked. |
| `LeadActivity` | Call logs, site visits, and correspondence | Append-only activity trail. |
| `File` | Field photographs, site drawings, contracts, receipts | Stored outside web root with random names. GPS metadata stripped on ingest. |
| `Supplier` | Construction material vendors and subcontractors | Managed by Finance and Owner. Includes TIN. |

---

### Class 3: Identity & Access Models

| Model Name | Core Purpose | Security Policy |
|---|---|---|
| `auth.User` | Primary Django user entity (Already in database: 4 users) | **Do NOT swap `AUTH_USER_MODEL`.** Superuser access forbidden. Passwords hashed with Argon2. |
| `UserProfile` | One-to-one extension (`job_title`, `phone`, `must_change_pwd`)| Enforces 2FA enrollment state and password rotation. |
| `auth.Group` | Predefined roles: `Owner`, `Finance`, `Site Staff` | Users belong to exactly one role group. |
| `auth.Permission` | Granular Django model permissions | Explicitly assigned to groups; no individual bypasses. |
| `sessions.Session` | Django active session store | Strict session expiry (12h idle, 30m sensitive). Cookie `HttpOnly`, `SameSite=Lax`, `Secure`. |

---

### Class 4: System & Other Models

| Model Name | Core Purpose | Immutability & Retention Policy |
|---|---|---|
| `CompanyProfile`| Legal company name, TIN, VAT number, bank details | Single-row model. History tracked via simple-history. |
| `AppSetting` | Key/value operational settings | Owner-only edit. Changes logged to `AuditEvent`. |
| `DocumentSequence`| Sequential counter for Quotes, Invoices, Projects | Concurrency-safe atomic incrementing. Never reset or reused. |
| `Unit` | Units of measurement (m, m², m³, kg, bag) | Managed by Finance/Owner. |
| `ProjectType` | Taxonomy for builds | Managed by Owner. |
| `TextTemplate` | Legal terms, boilerplate exclusions, email copy | Managed by Owner. |
| `RateLimitHit` | SHA-256 hashed client IP records for rate limiting | Automatically purged after 24 hours. Never stores raw IPs. |
| `Notification` | In-app user notifications | Personal to each user. |
| `NotificationPreference`| User email/in-app alert toggles | Managed by user. |
| `EmailOutbox` | Outbound email delivery queue with retry logs | Logs send status without storing sensitive credentials or tokens. |
| `AuditEvent` | **Immutable security and financial audit log** | **Append-only.** No user or admin can edit or delete rows. Retained for 7+ years. |
| `JobRun` | Automated background task and health check ledger | Retained for 90 days. |
| `ImportBatch` / `ImportedRow` | Migration and CSV import rollback ledgers | Audits imported records. |
| `admin.LogEntry` | Built-in Django admin historical log | Maintained for legacy admin actions. |
| `contenttypes.ContentType` | Django generic foreign key registry | System standard. |

---

## 3. Statutory & EFRIS Field Assessment

During the code audit, the following findings regarding URA EFRIS (Electronic Fiscal Receipting and Invoicing System) were identified:

1. **Mock EFRIS Data in Existing Code:**  
   In `dashboard/views.py` (line 159), the prototype code injects:
   `'URA FISCAL STATUS': 'EFRIS COMPLIANT'`
   This was hardcoded demonstration data.
2. **Current Schema Coverage:**  
   `CompanyProfile` includes:
   - `tin` (`str(30)`)
   - `vat_number` (`str(30)`)
   - `vat_registered` (`bool`)
   `Client` includes:
   - `tin` (`str(30)`)
   - `is_withholding_agent` (`bool`)
3. **Missing EFRIS-Specific Fiscal Fields:**  
   If Jimcan integrates with EFRIS, the following fields must be formally added to `Invoice` in Phase 6:
   - `efris_fdn`: Fiscal Document Number (official 20-digit URA reference)
   - `efris_verification_code`: URA anti-fake code
   - `efris_qr_code`: Path or data for the printed QR verification code
   - `efris_submission_status`: (`pending`, `submitted`, `failed`, `exempt`)
   - `efris_submitted_at`: Timestamp of successful fiscalization
4. **Impact on Void / Correction Flow:**  
   If EFRIS is active, an issued invoice **cannot be voided locally**; it must be reversed through a URA Credit Note submitted to EFRIS. This decision is presented for human sign-off in Question 1 of `decisions-needed.md`.
