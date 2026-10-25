# Jimcan Operations Dashboard: Canonical Screen Inventory & Specifications

**Document:** `docs/design/screens.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard App Flow Document.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20App%20Flow%20Document.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Product Requirements Document %28PRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Product%20Requirements%20Document%20%28PRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Backend Schema Document.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Backend%20Schema%20Document.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`flows.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/flows.md)
- [`roles-permissions.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/roles-permissions.md)
- [`states.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/states.md)

---

## 1. Screen Inventory Overview

The Jimcan Operations Dashboard comprises 47 canonical screens, grouped into 10 operational functional domains. Screen IDs (`S-xx`) correspond strictly to Section 9 of the [App Flow Document](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20App%20Flow%20Document.md).

```
System & Access:    S-00 to S-05
Core Overview:      S-10
Leads & Clients:    S-20 to S-31
Projects:           S-40 to S-48
Rate Library & BOQ: S-50 to S-63
Invoices & Billing: S-70 to S-74
Expenses & Vendors: S-75 to S-79
Reports & Tax:      S-80 to S-89
Media & Sync:       S-90
Admin & Audit:      S-91 to S-96
```

---

## 2. Global Screen Architecture Standards

Every screen adheres to the following behavioral contracts:
1. **One Primary Action:** Exactly one prominent button in Safety Orange (`bg-safety`) per screen canvas.
2. **Standard Landmark Structure:** `<header>` (brand/mobile nav), `<aside>` (desktop sidebar), `<main>` (page title, primary action bar, content cards), and `<footer>` (status, pagination).
3. **Responsive Breakpoint Target:** Mobile phone (360–480px, single column, touch targets ≥ 44px), Tablet (768–1024px), Desktop (1280px+).
4. **Offline Capability:** Critical capture screens (`S-47`, `S-76`, `S-90`) operate offline with a client-side sync queue. Financial creation forms refuse submission offline.

---

## 3. Canonical Screen Specifications

### Domain 0: System, Authentication & Error Boundaries

#### `S-00`: Sign In (`/login/`)
- **Purpose:** Secure authentication gate using Django session auth and `django-axes` brute-force lockout protection.
- **Primary User:** All roles (`Admin`, `Manager`, `Site Engineer`, `Accountant`).
- **Required Permissions:** Public / Unauthenticated.
- **Primary Action:** `Sign In` (`ButtonPrimary`).
- **Main Regions:** Jimcan wordmark, username/email field, password field with visibility toggle, remember session checkbox, CSRF token, login help link.
- **States:**
  - *Loading:* Button disables with inline spinner on POST.
  - *Error:* Generic high-contrast alert: "Invalid credentials. Attempt logged."
  - *Locked:* "Account locked due to consecutive failed attempts. Contact Admin."
- **Mobile Behaviour:** Centered card takes 100% viewport width with 16px margins.

#### `S-01`: Password Reset Request (`/password/reset/`)
- **Purpose:** Initiates self-service password recovery email.
- **Primary User:** All internal roles.
- **Primary Action:** `Send Reset Link`.
- **States:** Success renders a neutral confirmation screen ("If the email exists, a reset link has been dispatched") to prevent user enumeration.

#### `S-03`: Permission Denied (`403`)
- **Purpose:** Clean, informative barrier when an authenticated user attempts unauthorized URL access.
- **Primary User:** All roles.
- **Primary Action:** `Return to Home Dashboard` (`ButtonSecondary`).
- **Main Content:** "Access Restricted. You do not have permission to view this section. If you believe this is an error, contact your system administrator."

#### `S-04`: Page Not Found (`404`)
- **Purpose:** Broken link and missing record handler.
- **Primary Action:** `Back to Safety`.

#### `S-05`: System Error (`500`)
- **Purpose:** Graceful crash boundary for unhandled server exceptions.
- **Content:** Apologetic notification with unique incident correlation ID (`Request ID: #xyz`). No technical stack traces exposed.

---

### Domain 1: Executive & Operational Dashboard

#### `S-10`: Dashboard Home (`/`)
- **Purpose:** Central operational headquarters displaying actionable KPIs, urgent attention queues, recent activity, and cash flow trends.
- **Primary User:** `Admin` (full company view), `Manager` (assigned leads and projects view).
- **Required Permissions:** `auth.is_authenticated`, Role: `Admin` or `Manager`. (Note: `Accountant` redirects to `S-80`, `Site Engineer` redirects to `S-40`).
- **Entry Points:** Post-login landing for management; top sidebar link.
- **Primary Action:** `Record Expense` (quick entry) or `New Lead`.
- **Main Content Regions:**
  1. *Attention Queue:* Actionable alerts (e.g., "3 Overdue Invoices", "2 Pending Site Expenses").
  2. *KPI Cards Row (4 cards):* Active Projects, Unpaid Invoices (UGX), 30-Day Expenses (UGX), Pipeline Value.
  3. *Cash Flow Chart:* Chart.js monthly money in vs money out (embedded JSON data).
  4. *Active Builds Summary:* Table of active projects with phase progress bar and budget health.
  5. *Recent Leads Feed:* Last 5 inbound leads with status chips.
- **States:**
  - *Loading:* Skeleton cards for KPIs; placeholder canvas for Chart.js.
  - *Empty:* If new instance: "Welcome to Jimcan. Begin by configuring company settings or creating your first lead."
- **Acceptance Criteria:** Page load < 3s on 3G; all currency formatted in Geist Mono with `UGX` prefix; right-aligned tabular figures.

---

### Domain 2: Lead CRM & Client Directory

#### `S-20`: Lead Pipeline & List (`/leads/`)
- **Purpose:** Track prospective construction clients from initial web/phone enquiry to contract award.
- **Primary User:** `Admin`, `Manager`.
- **Primary Action:** `Add Lead` (`ButtonPrimary`, opens `S-22`).
- **Secondary Actions:** Toggle Table / Kanban view, Filter by Status, Export to Excel.
- **Main Content Regions:** Filter bar (status, assignee, date range), Summary metrics (Total Leads, Conversion Rate), Lead Table / Pipeline Board (Columns: `New`, `Contacted`, `Site Visit`, `Quoted`, `Won`, `Lost`).
- **States:**
  - *Empty State:* "No active leads. Inbound submissions from jimcanconstruction.site will appear here automatically."

#### `S-21`: Lead Detail & Activity Log (`/leads/<public_id>/`)
- **Purpose:** Comprehensive record of client interaction, site visit notes, requirement files, and conversion actions.
- **Primary Action:** `Convert to Client & Project` (`ButtonPrimary`, visible when status is `Quoted` or `Won`).
- **Secondary Actions:** `Log Activity Note`, `Change Status`, `Edit Lead Details`.
- **Main Regions:** Lead info header, Status progression bar, Contact details card, Requirement files list, Chronological activity timeline with comment form.

#### `S-22`: Lead Create / Edit Modal/Page (`/leads/new/`)
- **Purpose:** Manual recording of telephone, referral, or walk-in enquiries.
- **Primary Action:** `Save Lead`.
- **Fields:** Contact Name, Phone Number, Email, Project Type (Residential, Commercial, Renovation, Civil), Location, Estimated Budget (UGX), Detailed Notes, Assigned Manager.

#### `S-23`: Public Website Enquiry Endpoint (`POST /public/leads/`)
- **Purpose:** Headless endpoint receiving form submissions from static `jimcanconstruction.site`.
- **Security:** IP rate limiting, honeypot field, CSRF exempt or token-secured API key.

#### `S-30`: Client Directory (`/clients/`)
- **Purpose:** Master list of all individuals and corporate entities with active or completed projects.
- **Primary User:** `Admin`, `Manager`, `Accountant` (read-only).
- **Columns:** Client Name, Primary Contact, Phone, Total Projects, Total Invoiced (UGX), Outstanding Balance (UGX), Status.

#### `S-31`: Client Detail & Financial History (`/clients/<public_id>/`)
- **Purpose:** 360-degree financial overview of a client: all associated projects, cumulative invoices, payment history, and credit terms.

---

### Domain 3: Project Management & Site Operations

#### `S-40`: Projects List (`/projects/`)
- **Purpose:** Master portfolio list of active, upcoming, and completed builds.
- **Primary User:** `Admin`, `Manager`, `Site Engineer` (filtered to assigned builds).
- **Landing Screen for:** `Site Engineer`.
- **Primary Action:** `New Project` (`Admin` & `Manager` only).
- **Table Columns:** Project Code, Project Name, Location, Current Phase (Badge), Lead Engineer, Contract Value (UGX), Cost to Date (UGX), Target Handover Date.

#### `S-41`: Project Overview (`/projects/<public_id>/`)
- **Purpose:** Central hub for an individual project build.
- **Primary Action:** `Update Phase` or `Log Site Activity`.
- **Main Regions:**
  - *Header:* Title, Location, Client link, Phase Progress Bar (`Brief` → `Design` → `Foundation` → `Superstructure` → `Finishes` → `Handover`).
  - *Navigation Tabs:* Overview (`S-41`), BOQ (`S-43`), Quotes (`S-44`), Invoices (`S-45`), Expenses (`S-46`), Files/Photos (`S-47`), History (`S-48`).
  - *Financial Health Card:* Budget vs Actual variance, margin indicator (hidden from `Site Engineer`).

#### `S-47`: Project Media & Site Photos (`/projects/<public_id>/files/`)
- **Purpose:** Site progress photo capture, drawing repository, and CAD file viewer.
- **Primary User:** `Site Engineer` (phone-first), `Manager`.
- **Primary Action:** `Take / Upload Photo` (large touch trigger).
- **Offline Behavior:** Photos captured offline are held in local device storage and automatically queued for background upload when connectivity returns.

---

### Domain 4: Rate Library, BOQ Builder & Quotes

#### `S-50`: Rate Library (`/rates/`)
- **Purpose:** Standardized master catalog of construction material, labor, and plant unit rates.
- **Primary User:** `Admin`, `Manager`.
- **Columns:** Item Code, Description, Unit (m², m³, kg, nr, lump sum), Base Material Cost, Labor Cost, Plant Cost, Total Standard Rate (UGX), Last Updated.

#### `S-60`: BOQ Builder & Version Studio (`/boq/<public_id>/`)
- **Purpose:** Desktop-optimized interactive bill of quantities generator with section hierarchies, dynamic markup calculations, and version comparison.
- **Primary User:** `Manager` (Quantity Surveyor), `Admin`.
- **Primary Action:** `Lock & Issue as Quote` (`ButtonPrimary`).
- **Secondary Actions:** `Add Section`, `Import from Rate Library`, `Create New Revision`, `Export Excel`.
- **Main Regions:** Version selector (e.g., `v1.0 [Locked]`, `v1.1 [Draft]`), Tree-view sections, Live summary totals bar (Subtotal, Contingency %, Overhead %, Profit Margin %, VAT 18%, Grand Total UGX).
- **Immutability Contract:** A locked BOQ version cannot be edited. Edits spawn an incremental revision (`v1.1`).

#### `S-62`: Quote Detail & PDF Generator (`/quotes/<public_id>/`)
- **Purpose:** Client-facing formal quotation review and PDF document generation.
- **Primary Action:** `Download Client PDF` (`ReportLab` compiled).
- **Secondary Actions:** `Mark Accepted / Won`, `Mark Rejected`, `Revise Quote`.

---

### Domain 5: Invoicing, Payments & Statutory Withholding

#### `S-70`: Invoice List (`/invoices/`)
- **Purpose:** Complete accounts receivable ledger: progress claims, advance payments, and retention invoices.
- **Primary User:** `Admin`, `Manager`, `Accountant`.
- **Primary Action:** `Create Invoice` (`S-72`).
- **Columns:** Invoice #, Date Issued, Due Date, Project, Client, Net Amount, VAT (18%), Gross Amount (UGX), Paid Amount, Balance Due, Status (`Draft`, `Issued`, `Partially Paid`, `Paid`, `Overdue`, `Void`).

#### `S-71`: Invoice Detail & Payment Ledger (`/invoices/<public_id>/`)
- **Purpose:** Formal invoice display, payment allocation, withholding tax tracking, and audit trail.
- **Primary Action:** `Record Payment` (`ButtonPrimary`, opens `S-73`).
- **Secondary Actions:** `Generate Tax Invoice PDF`, `Issue Credit Note` (`Admin` only), `Void Invoice` (`Admin` only).

#### `S-73`: Payment Recording Modal
- **Purpose:** Log client payment receipt, identify bank account, and deduct statutory Withholding Tax (WHT).
- **Fields:** Payment Date, Amount Received (UGX), Payment Method (Bank Transfer, Cheque, Cash), WHT Deducted (6% toggle / custom UGX), WHT Certificate Reference Number, Receipt Reference.

---

### Domain 6: Expenses, Site Purchasing & Suppliers

#### `S-75`: Expense List & Approval Queue (`/expenses/`)
- **Purpose:** Track company and site expenses; approval inbox for field disbursements.
- **Primary User:** `Admin`, `Manager`, `Accountant`.
- **Primary Action:** `Record Expense` (`S-76`).
- **Filter Tabs:** `All Expenses`, `Pending Approval` (Manager/Admin action required), `Approved`, `Reimbursed`.

#### `S-76`: Expense Entry Form & Mobile Receipt Capture (`/expenses/new/`)
- **Purpose:** Rapid field expense recording on mobile phones with camera receipt capture.
- **Primary User:** `Site Engineer`, `Manager`.
- **Primary Action:** `Submit Expense` (44px touch target).
- **Fields:** Project (Select), Category (Materials, Fuel, Casual Labor, Permits, Subsistence), Amount (UGX, formatted numeric pad), Vendor / Supplier, Receipt Photo (File / Camera upload), Payment Source (Petty Cash, Director Account, Corporate Bank), Description.

#### `S-78`: Supplier Directory & Balances (`/suppliers/`)
- **Purpose:** Vendor directory, trade terms, and outstanding accounts payable balances.

---

### Domain 7: Financial Statements & Uganda Tax Compliance

#### `S-80`: Financial Reports Hub (`/reports/`)
- **Purpose:** Financial statement overview, cash balance, and profitability indicators.
- **Primary User:** `Admin`, `Accountant`.
- **Landing Screen for:** `Accountant`.
- **Report Links:** Profit & Loss (`S-81`), Cash Flow (`S-82`), Balance Sheet Summary (`S-83`), Project Profitability (`S-84`), Aged Debtors & Creditors (`S-85`).

#### `S-86`: Tax Calendar & Compliance Portal (`/tax/`)
- **Purpose:** Uganda Revenue Authority (URA) tax compliance calendar and filing preparation.
- **Primary Action:** `Close Tax Period` (`Admin` & `Accountant`).
- **Sections:**
  - *Monthly VAT Summary (`S-87`):* Output VAT collected on sales vs Input VAT paid on eligible purchases = Net VAT Payable / Credit.
  - *Withholding Tax Summary (`S-88`):* 6% WHT deducted by clients on sales invoices vs WHT withheld on supplier payments.
  - *Statutory Calendar:* Upcoming deadlines (e.g., 15th of month for VAT & PAYE).

---

### Domain 8: File Pipeline, Upload Queue & Sync

#### `S-90`: Upload Queue & Sync Monitor (`/files/`)
- **Purpose:** Visual monitor displaying queued offline uploads, background image compression status, and failed file retries.
- **Primary User:** `Site Engineer`, `Manager`.
- **Main Regions:** Active uploads progress bars, Failed items list with manual "Retry All" trigger, Storage quota usage indicator.

---

### Domain 9: Administration, Security & Auditing

#### `S-92`: System Audit Trail (`/audit/`)
- **Purpose:** Immutability log recording every database mutation (INSERT, UPDATE, DELETE, VOID) with field-level diffs and actor user ID.
- **Primary User:** `Admin` strictly.
- **Columns:** Timestamp (EAT), User, Action, Entity, Record ID, Changes (Diff inspection dialog).

#### `S-93` to `S-96`: Settings Suite
- `S-93`: Company Profile & Document Branding (Jimcan legal name, TIN, physical address, logo).
- `S-94`: Tax Rates & Calculation Rules (Standard VAT 18%, Standard WHT 6%, custom exemptions).
- `S-95`: Document Numbering Sequences (Prefixes and next counters for `JC-INV-`, `JC-QUO-`, `JC-PRJ-`).
- `S-96`: User Management & Role Assignment (Invite user, assign role: `Admin`, `Manager`, `Site Engineer`, `Accountant`, deactivation toggle).

---

## 4. Open Questions Relevant to Screens
1. `[OQ-07]`: Standard numbering format approval for Jimcan documents (e.g. `JC-INV-2026-001` vs simple integer counter).
2. `[OQ-08]`: Whether Site Engineers should have permission to view other engineers' project photos, or strictly assigned projects.

---

## 5. Change Log
- **24 October 2026 (v0.1):** Canonical screen inventory authored, cataloging S-00 through S-96 based on App Flow Document v0.1.

*Unresolved items must not be treated as approved requirements.*
