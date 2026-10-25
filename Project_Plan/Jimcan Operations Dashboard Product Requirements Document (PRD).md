# Jimcan Operations Dashboard: Product Requirements Document

Version 0.1 (draft for review) | 24 October 2026 | Author: George | Client: Jimcan Construction

## 1. Purpose of this document

This PRD defines **what** the Jimcan Operations Dashboard must do and **why**, for a first release that real staff use daily with real money data. It is an MVP, not a prototype. That means it must be secure, backed up, accurate in its calculations, usable on a phone at a building site, and supportable after launch.

How it will be built is covered in the TRD. Screens and journeys are in the App Flow document. Tables are in the Backend Schema document.

## 2. Background and problem

Jimcan Construction wins and delivers building work. Today, enquiries, quotes, costs and payments are likely spread across phones, WhatsApp, paper and spreadsheets. The consequences, to be confirmed with Jimcan in discovery:

- Leads are lost or answered late because nobody has one list of who asked for what.
- Quotes take long to prepare and are inconsistent, because rates are retyped for every job.
- Management cannot see, during a project, whether it is making or losing money.
- Tax figures (VAT, withholding tax, PAYE) are assembled at the last minute, with errors and penalty risk.
- Site progress and photos live on personal phones, not with the project record.

## 3. Product vision and goals

**Vision:** one reliable system where an enquiry becomes a quote, a project, an invoice and a set of financial statements, with every figure traceable.

**Goals for the MVP**

1. Capture every lead in one place and never lose a follow-up.
2. Produce a professional, accurate BOQ and quote from a shared rate library in under 30 minutes for a typical job.
3. Track money in and money out per project, so budget versus actual is always visible.
4. Calculate VAT and withholding tax correctly and produce a monthly tax summary in minutes.
5. Generate profit and loss, cash flow and a simple balance view without retyping data.
6. Let site engineers upload progress photos and update project phase from a phone, even on weak signal.
7. Run on low cost hosting (Namecheap) using free software only.

**Non goals for the MVP:** payroll processing, a client portal, supplier portal, full double entry accounting, automatic submission to URA, inventory management, mobile native apps.

## 4. Success metrics

Measured 30 and 90 days after launch. Baselines to be captured during discovery.

| Metric | Target |
| --- | --- |
| Enquiries logged in the system | 100% of new leads |
| Time from enquiry to quote sent | Down by at least 50% from today's baseline |
| Time to prepare a standard BOQ | 30 minutes or less |
| Expenses recorded with project and category | 95% or more |
| Monthly tax summary preparation | 15 minutes or less |
| Weekly active users out of invited staff | 80% or more |
| Calculation errors found in UAT and first month | Zero in BOQ, VAT and statements |
| Page load on a mid range phone, 3G | Under 4 seconds for main screens |

## 5. Users and roles

| Role | Who | Main needs | Device |
| --- | --- | --- | --- |
| Admin | Owner or director | Full control, approvals, statements, users, settings | Laptop and phone |
| Manager | Project or office manager | Leads, BOQs, quotes, invoices, expenses, assigned projects | Laptop, some phone |
| Site Engineer | Engineer or foreman | View assigned projects, upload photos, update phase, log site expenses | Phone, weak signal |
| Accountant (read only) | External or internal accountant | View invoices, expenses, tax and statements, export | Laptop |

**Permission principles**

- Least privilege: each role sees only what its work needs.
- Only Admin can void issued documents, change tax rates, manage users and see all statements.
- Nobody can permanently delete financial records. Removal is a soft delete with an audit entry.
- Site Engineers cannot see client pricing, profit margins or statements.

## 6. Assumptions and constraints

- Hosting is Namecheap shared hosting with Python app support. This must be verified before build, including Python version, memory limit, cron, SMTP limits and disk quota.
- No paid services other than the domain and hosting. Free tools only.
- Currency is Ugandan Shillings (UGX). Whole shilling amounts. USD support is optional and deferred unless Jimcan prices some jobs in USD.
- Initial user count is under 15. Initial data volume is small, so the design must be simple first and scale later.
- Internet is unreliable on sites. Anything a Site Engineer does must tolerate drops.
- Tax rules change. Rates and thresholds are stored as editable settings, never hardcoded.
- A single company (Jimcan) uses the system. Multi company support is out of scope.

## 7. Scope

### In scope for the MVP

1. Accounts, roles, login security
2. Leads and clients (CRM), including intake from the public website contact form
3. Projects with phases and a phase history
4. Rate library (materials, labour, plant, subcontract)
5. BOQ builder with sections, line items, versions, and PDF and Excel export
6. Quotes issued from a BOQ
7. Invoices and payments received, including part payments and retention
8. Expenses and suppliers, with receipt photos
9. Tax tracking: VAT, withholding tax, PAYE and NSSF records
10. Financial statements: profit and loss, cash flow, simple balance view, project profitability
11. Site photo and document uploads
12. Email notifications and an in app notification list
13. Audit history on all money and status changes
14. Backups and a tested restore procedure

### Out of scope (version 2 candidates)

Client portal, supplier purchase orders, payroll runs, timesheets, inventory, e-invoicing integration, mobile money reconciliation, WhatsApp or SMS automation, multi currency accounting, advanced analytics, native mobile apps.

## 8. Functional requirements

Each requirement has an ID. Priority: **M** = must have for MVP, **S** = should have, **C** = could have if time allows. Acceptance criteria are written so they can be tested.

### Module A: Accounts and access

| ID | Requirement | Priority |
| --- | --- | --- |
| A1 | Users sign in with username and password | M |
| A2 | Roles: Admin, Manager, Site Engineer, Accountant | M |
| A3 | Admin creates, disables and resets users. No public sign up | M |
| A4 | Password policy and lockout after repeated failures | M |
| A5 | Session timeout after inactivity | M |
| A6 | Two factor authentication for Admin | S |
| A7 | Users can change their own password | M |

**Acceptance criteria**

- A signed out visitor opening any internal URL is redirected to sign in.
- A Site Engineer who types the URL of a statement or pricing page receives a permission denied response, not the data.
- A disabled user cannot sign in, and existing sessions end.
- Five failed sign ins in a short window lock the account or slow attempts, and the event is logged.

### Module B: Leads and clients

**User stories**

- As a Manager, I see every new enquiry in one list so none is missed.
- As a Manager, I update a lead through a pipeline and record every contact so the team knows the history.
- As an Admin, I assign leads and see who has been slow to respond.

| ID | Requirement | Priority |
| --- | --- | --- |
| B1 | Website contact form creates a lead automatically with name, phone, email, project type, location and details | M |
| B2 | Manual lead entry | M |
| B3 | Pipeline statuses: New, Contacted, Site visit, Quoted, Won, Lost (with reason) | M |
| B4 | Assign a lead to a user | M |
| B5 | Activity log per lead: calls, notes, site visit, with date and user | M |
| B6 | Follow up date and an overdue indicator | M |
| B7 | Clients are a separate record from leads. A won lead creates or links a client | M |
| B8 | Duplicate warning on matching phone or email | S |
| B9 | Email alert to Admin and Managers on a new lead | M |
| B10 | Spam protection on the public form (honeypot and rate limit) | M |
| B11 | Search and filter by status, assignee, date, project type | M |

**Acceptance criteria**

- Submitting the website form with valid data creates a lead within 5 seconds and sends the alert email.
- A form submission with the honeypot filled is silently discarded and logged.
- Moving a lead to Lost requires a reason.
- A lead with a follow up date in the past appears in an Overdue filter and on the dashboard.
- A client with several projects shows all of them on one client page.

### Module C: Projects

| ID | Requirement | Priority |
| --- | --- | --- |
| C1 | Create a project from a won lead or manually, linked to a client | M |
| C2 | Fields: title, location, contract value, start date, target completion, assigned manager and engineers | M |
| C3 | Phases: Brief, Design, Foundation, Superstructure, Finishes, Handover | M |
| C4 | Phase history records who changed the phase and when | M |
| C5 | Project page shows summary, BOQ, invoices, expenses, photos, documents and profit position | M |
| C6 | Project status: Active, On hold, Completed, Cancelled | M |
| C7 | Site Engineers see only projects they are assigned to | M |
| C8 | Milestones with due dates and completion | S |
| C9 | Variation orders linked to a project | S |

**Acceptance criteria**

- Changing a phase never overwrites history. The history list shows every change in order.
- A Site Engineer cannot open an unassigned project even by guessing the URL.
- The project page shows budget, invoiced, received, spent and margin figures that match the underlying records exactly.

### Module D: Rate library

**User story:** As a Manager, I keep one list of current rates so every BOQ uses consistent prices and I update a price once.

| ID | Requirement | Priority |
| --- | --- | --- |
| D1 | Rate items: code, description, unit, category (material, labour, plant, subcontract), rate, supplier note, effective date | M |
| D2 | Edit a rate without changing already issued BOQs and quotes | M |
| D3 | Rate history | S |
| D4 | Import rates from Excel or CSV | S |
| D5 | Search, filter, archive items instead of deleting | M |
| D6 | Assemblies, for example 1 m3 of concrete made from cement, sand, aggregate and labour | C |

**Acceptance criteria**

- Editing a rate updates draft BOQs on request, and never alters issued or accepted versions.
- An archived rate cannot be added to new BOQs but still displays on old ones.

### Module E: BOQ builder

This is the heart of the system and must be correct before anything else ships.

| ID | Requirement | Priority |
| --- | --- | --- |
| E1 | A project can have many BOQs, each with versions (v1, v2 and so on) | M |
| E2 | Sections such as Preliminaries, Substructure, Superstructure, Roofing, Finishes, External works, with reorder | M |
| E3 | Line items: item number, description, unit, quantity, rate, amount | M |
| E4 | Add an item from the rate library, or enter a custom item | M |
| E5 | Live totals as quantities and rates change | M |
| E6 | Section subtotals and grand total | M |
| E7 | Contingency %, overheads and profit %, and VAT, applied in a defined order | M |
| E8 | Provisional sums and prime cost sums marked clearly | S |
| E9 | Copy a BOQ or version to start a new one | M |
| E10 | Lock a version when issued. Locked versions cannot be edited | M |
| E11 | Compare two versions and show differences | C |
| E12 | Export to PDF (client ready) and Excel | M |
| E13 | Internal view (cost and margin) separate from client view (prices only) | M |
| E14 | Bulk paste of quantities from Excel | S |

**Acceptance criteria**

- Line amount equals quantity times rate, rounded to the nearest whole shilling, and the total equals the sum of the rounded lines.
- Totals shown on screen, in PDF and in Excel are identical.
- Editing a locked version is impossible. The user is offered to create a new version instead.
- Deleting a section containing items asks for confirmation and is recorded in the audit history.
- A BOQ of 300 line items loads and recalculates without noticeable delay on a laptop and remains usable on a phone.
- Site Engineers cannot open BOQ prices.

### Module F: Quotes

| ID | Requirement | Priority |
| --- | --- | --- |
| F1 | Create a quote from a locked BOQ version | M |
| F2 | Quote number from a gap free sequence | M |
| F3 | Validity period, payment terms, exclusions, notes using editable templates | M |
| F4 | Status: Draft, Sent, Accepted, Rejected, Expired | M |
| F5 | PDF with company details, logo, tax numbers, terms | M |
| F6 | Email the PDF from the system | S |
| F7 | Accepting a quote creates or updates the project and contract value | M |

**Acceptance criteria**

- Two quotes can never share a number.
- A sent quote cannot be edited. A revision creates a new version that references the earlier one.
- Accepting a quote sets the project contract value to the quote total.

### Module G: Invoices and payments received

| ID | Requirement | Priority |
| --- | --- | --- |
| G1 | Create an invoice for a project: lines, VAT, due date, terms | M |
| G2 | Invoice from quote milestones or percentages (deposit, stage, final) | M |
| G3 | Gap free invoice numbering | M |
| G4 | Status: Draft, Sent, Part paid, Paid, Overdue, Void | M |
| G5 | Record payments with date, amount, method (cash, bank, mobile money) and reference | M |
| G6 | Part payments and an outstanding balance | M |
| G7 | Withholding tax deducted by the client recorded against the payment | M |
| G8 | Retention held and released | S |
| G9 | Credit notes | S |
| G10 | PDF invoice, and emailing it | M, S |
| G11 | Overdue flagging by due date and an ageing report | M |
| G12 | Voiding requires Admin and a reason, and keeps the record | M |

**Acceptance criteria**

- Payments cannot exceed the invoice balance unless explicitly recorded as an overpayment.
- Invoice balance equals invoice total minus payments minus withholding tax recorded.
- A voided invoice remains visible with its number, and is excluded from revenue and VAT totals.
- The ageing report groups unpaid amounts into current, 1 to 30, 31 to 60, and over 60 days.

### Module H: Expenses and suppliers

| ID | Requirement | Priority |
| --- | --- | --- |
| H1 | Record an expense: date, amount, supplier, project, category, payment method, reference | M |
| H2 | Receipt photo or file attached | M |
| H3 | Categories: Materials, Labour, Plant and equipment, Subcontractors, Transport, Permits and fees, Overheads | M |
| H4 | VAT on purchases recorded separately where the supplier charged it | M |
| H5 | Supplier list with contact details and balance owed | M |
| H6 | Unpaid bills (payables) with due dates | S |
| H7 | Site Engineers can submit expenses for approval by a Manager | S |
| H8 | Budget versus actual per project and per BOQ section | M |
| H9 | Overheads not tied to a project | M |
| H10 | Bulk import from Excel | C |

**Acceptance criteria**

- An expense without a project must be marked as overhead.
- Budget versus actual on a project page matches the sum of its expenses exactly.
- An approved expense cannot be edited by its author. Corrections go through a reversal entry or an Admin edit that is logged.

### Module I: Tax

Rates and thresholds below are placeholders to be verified with URA guidance or Jimcan's accountant before launch. All values are stored as editable settings with an effective date.

| ID | Requirement | Priority |
| --- | --- | --- |
| I1 | VAT rate setting, default 18%, applied to invoices and quotes | M |
| I2 | Input VAT recorded on purchases | M |
| I3 | Monthly VAT summary: output VAT, input VAT, net payable or refundable | M |
| I4 | Withholding tax receivable (tax deducted by clients) with certificate reference | M |
| I5 | Withholding tax payable where Jimcan withholds from suppliers | S |
| I6 | PAYE and NSSF records for staff, entered monthly | S |
| I7 | Tax calendar with due dates and reminders | M |
| I8 | Mark a period as filed, with filing reference and date. Filed periods lock | M |
| I9 | Export of tax summaries to Excel and PDF for the accountant | M |
| I10 | Tax rates with effective dates so past documents keep the rate they used | M |

**Acceptance criteria**

- Changing the VAT rate affects only documents created after the effective date.
- The VAT summary for a month equals the sum of VAT on non void invoices dated in that month less VAT on recorded purchases.
- A locked period cannot receive new entries without an Admin override that is logged.
- A reminder email goes out a set number of days before each due date.

### Module J: Financial statements and reports

| ID | Requirement | Priority |
| --- | --- | --- |
| J1 | Profit and loss for any date range, per project and company wide | M |
| J2 | Cash flow: money in, money out, net, by period | M |
| J3 | Simple balance view: cash, receivables, payables, retention | M |
| J4 | Project profitability: contract value, invoiced, received, cost, margin | M |
| J5 | Dashboard KPIs: active projects, receivables, spend this month, VAT payable, overdue items | M |
| J6 | Cash in versus out chart for the last 6 months | M |
| J7 | Export every report to Excel and PDF | M |
| J8 | Accrual and cash views, with the basis labelled on each report | S |
| J9 | Filters by project, client, period | M |

**Acceptance criteria**

- Every figure on a statement can be clicked or traced to the invoices and expenses that make it up.
- Statement totals reconcile to the underlying records. A reconciliation check page shows any difference.
- Reports respect roles. Only Admin and Accountant see company wide statements.

### Module K: Files and site photos

| ID | Requirement | Priority |
| --- | --- | --- |
| K1 | Upload photos and documents (PDF, drawings, contracts) to a project | M |
| K2 | Photos are compressed in the browser before upload | M |
| K3 | Uploads resume or queue when signal drops, and the user sees what is waiting | M |
| K4 | File type and size validation | M |
| K5 | Files are private and only available to users with project access | M |
| K6 | Caption, date taken, phase and uploader recorded | M |
| K7 | Gallery view per project and phase | S |
| K8 | Flag a photo as approved for the public portfolio | C |

**Acceptance criteria**

- A 5 MB phone photo uploads at under 1 MB after compression, with acceptable quality.
- Losing connection mid upload does not lose the photo. It appears in a waiting list and retries.
- Typing a file URL while signed out or without project access returns no file.

### Module L: Notifications

| ID | Requirement | Priority |
| --- | --- | --- |
| L1 | Email on new lead | M |
| L2 | Email or in app alert when a lead follow up is overdue | M |
| L3 | Alert on overdue invoices | M |
| L4 | Tax due date reminders | M |
| L5 | Alert when a project phase changes | S |
| L6 | Each user can switch non critical alerts off | S |

### Module M: Administration and settings

| ID | Requirement | Priority |
| --- | --- | --- |
| M1 | Company profile: name, logo, address, TIN, VAT number, bank and mobile money details | M |
| M2 | Numbering formats for quotes and invoices | M |
| M3 | Tax rate settings with effective dates | M |
| M4 | Document templates: terms, exclusions, payment terms | M |
| M5 | Lists: categories, units, project types | M |
| M6 | Audit log viewer for Admin | M |
| M7 | Data export of all records for Admin | S |

### Module N: Audit and history (cross cutting)

- Every create, change, void and delete on leads, projects, BOQs, quotes, invoices, payments, expenses and tax records stores who, when, and what changed.
- Audit records cannot be edited or deleted through the application.
- Soft deletes only. A deleted record is hidden but recoverable by Admin.

## 9. Business rules

### BOQ and quote calculation order (configurable per company, default shown)

1. Line amount = quantity x rate, rounded to the nearest whole UGX.
2. Section subtotal = sum of line amounts.
3. Subtotal = sum of section subtotals.
4. Add preliminaries if held as a percentage.
5. Add contingency % of the subtotal.
6. Add overheads and profit % of the running total.
7. Total excluding VAT.
8. VAT = VAT rate x total excluding VAT (less any VAT exempt items).
9. Total including VAT.

The exact order and which items are exempt must be confirmed with Jimcan and documented before the BOQ module is built.

### Other rules

- **Numbering:** quote and invoice numbers are sequential, never reused, never skipped, and generated inside a database transaction.
- **Issued means locked:** once a quote or invoice is issued, its content cannot change. Corrections are new versions or credit notes.
- **Invoice balance:** total minus payments minus withholding tax recorded minus credit notes.
- **Overdue:** an invoice is overdue when today is after the due date and the balance is above zero.
- **Project margin:** received or invoiced revenue (basis shown) minus project costs.
- **Period locking:** a filed tax period or closed month rejects new entries unless Admin overrides with a reason.
- **Rounding:** all money stored as exact decimals. No floating point arithmetic.
- **Dates:** East Africa Time, displayed as day, month name, year.

## 10. Non functional requirements

| Area | Requirement |
| --- | --- |
| Performance | Main screens load in under 4 seconds on 3G. Lists are paginated. Reports for one year generate in under 10 seconds |
| Availability | Target 99% monthly uptime on shared hosting, with uptime monitoring and an alert |
| Security | HTTPS only, hashed passwords, CSRF protection, role checks on every view, private file storage, secure session cookies, login throttling, no secrets in code |
| Reliability | Nightly database backup and file backup, copy kept off the server, monthly restore test, recovery within one working day |
| Usability | Usable with one hand on a phone. Large tap targets. Clear errors. Readable in sunlight |
| Accessibility | Sufficient contrast, labelled fields, keyboard navigation on desktop |
| Compatibility | Current Chrome, Edge, Firefox, Safari. Android and iPhone browsers from the last 3 years |
| Maintainability | Business logic in tested service functions, documented setup, readable code |
| Auditability | Complete history on money records |
| Scalability | Handles at least 50 users, 10,000 invoices and 50,000 expense lines without redesign. Clear path to a VPS and a larger database |
| Localisation | UGX formatting, East Africa Time, English |
| Cost | No recurring costs beyond domain and hosting |

## 11. Compliance and data protection

- Tax settings and report formats reviewed by Jimcan's accountant or a URA adviser before go live.
- Confirm whether EFRIS e-invoicing applies to Jimcan. If it does, decide whether MVP invoices are used alongside the official system, and plan integration for a later release.
- Personal data (clients, leads, staff) handled according to the Uganda Data Protection and Privacy Act: collect only what is needed, restrict access, allow correction and removal requests, and state retention periods.
- Financial records retained for the period required by Ugandan law. Confirm the period and configure retention accordingly.
- Terms and privacy text on the public contact form.

## 12. Data migration

- Inventory what exists today: client list, past quotes, rate sheets, expense sheets, invoices.
- Import the rate library and client list before go live.
- Import open invoices and open projects with balances as at the cutover date.
- Past completed jobs are optional and imported only if clean.
- Opening balances (cash, receivables, payables, retention) entered as at the cutover date.
- Every import goes through a preview and error report, and is reconciled against the source totals.

## 13. MVP release criteria (what "done" means)

The MVP launches only when all of the following are true:

1. All **M** requirements pass their acceptance criteria in user acceptance testing with real past jobs.
2. At least three real historic BOQs and five invoices replayed in the system match the old totals to the shilling.
3. Automated tests cover BOQ calculation, VAT, withholding tax, numbering, permissions and statement totals, and they pass.
4. Role permissions tested for every role on every module.
5. HTTPS on, debug off, secrets in environment variables, admin URL protected.
6. A backup has been taken **and restored** successfully on a clean copy.
7. Error logging and uptime monitoring working, with an alert reaching a real person.
8. Site upload tested on a real phone on a weak connection.
9. Opening data imported and reconciled.
10. Staff trained, with a short guide per role.
11. Accountant has reviewed the tax and statement outputs.
12. Written sign off from Jimcan.

## 14. Release phasing

| Release | Contents |
| --- | --- |
| MVP | Modules A to N at priority M, plus the S items that are low effort |
| 1.1 (about 2 to 3 months later) | Remaining S items: 2FA, payables, retention, credit notes, rate history, variation orders, notification preferences |
| 2.0 | Client portal, e-invoicing integration, supplier orders, payroll support, WhatsApp or SMS alerts, mobile money reconciliation, portfolio publishing from approved photos |

## 15. Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Shared hosting limits (memory, processes, PDF libraries) | Features fail in production | Verify hosting early, deploy a test build in week 1, choose a PDF library that runs there |
| Tax rules or rates change | Wrong tax figures | Editable rates with effective dates, accountant review, clear disclaimers |
| Scope creep | Late, unfinished MVP | Frozen MVP scope, parking lot for new ideas, change requests logged |
| Staff do not adopt it | No value | Involve users from design, train, start with a parallel run, track usage |
| Poor connectivity on site | Lost uploads and data | Compression, queueing, resumable uploads, simple forms |
| Data entry errors | Wrong statements | Validation, required fields, reconciliation page, review step for expenses |
| Single developer dependency | Support gaps | Documentation, simple stack, backups, handover guide |
| Data loss | Business harm | Nightly backups, offsite copy, tested restores |
| Calculation bugs | Financial errors | Decimal arithmetic, automated tests, UAT with real jobs |
| Slow hosting | Poor experience | Pagination, indexes, light pages, caching where useful |

## 16. Open questions for Jimcan

1. Which Namecheap plan is in place, and does it include Python app support and cron?
2. Exact BOQ pricing order: preliminaries, contingency, overheads and profit, and what is VAT exempt?
3. Does Jimcan price in USD for any jobs?
4. Is Jimcan VAT registered, and does it have to use EFRIS?
5. Which withholding tax situations occur most (clients who are withholding agents, thresholds)?
6. Does Jimcan run payroll, and does it need PAYE and NSSF tracking in version 1?
7. Who approves expenses, and is there a spending limit by role?
8. How are payments received today (bank, mobile money, cash), and are references needed?
9. How long must records be retained?
10. What documents, logo and terms should appear on quotes and invoices?
11. How many users at launch, and who is who?
12. Who is the accountant, and will they use the system?
13. What existing spreadsheets can be imported, and who owns cleaning them?
14. What is the target go live date, and is there a busy season to avoid?

## 17. Glossary

- **BOQ:** Bill of Quantities. A priced list of the work items, quantities and rates for a project.
- **PRD / TRD:** Product Requirements Document / Technical Requirements Document.
- **UAT:** User Acceptance Testing by the people who will use the system.
- **VAT:** Value Added Tax. **WHT:** Withholding Tax. **PAYE:** Pay As You Earn. **NSSF:** National Social Security Fund.
- **URA:** Uganda Revenue Authority. **EFRIS:** Electronic Fiscal Receipting and Invoicing Solution.
- **Retention:** a portion of payment held by the client until defects are corrected.
- **Soft delete:** hiding a record instead of removing it from the database.

## 18. Approvals

| Name | Role | Decision | Date |
| --- | --- | --- | --- |
|  | Jimcan owner or director |  |  |
|  | Jimcan project manager |  |  |
|  | Accountant |  |  |
| George | Developer |  |  |
