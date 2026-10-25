# Jimcan Operations Dashboard: Backend Schema Document

Version 0.1 (draft for review) | 24 October 2026 | Author: George | Companion to PRD, TRD, App Flow and Design Brief v0.1

## 1. Purpose and status labels

This document defines the data model: every table, its fields, relationships, constraints, indexes, permissions, and how reports are derived. It is the contract between the PRD (what the business needs), the App Flow (how data changes) and the Django models that will be written.

**Labels used so nothing is guessed**

- **\[Built\]** exists in the starter project. Only these exist today: Django's built in user, group, permission, session, message and admin tables. **No business tables have been built.** Everything else below is design.
- **\[Decision\]** a design choice made here. Change it before models are written, not after.
- **\[VERIFY\]** depends on the Namecheap database, which has not been checked yet (TRD spike 1).
- **\[S\]** should have, **\[C\]** could have, per the PRD. Unmarked tables are must have for the MVP.
- **\[Open\]** needs an answer from Jimcan.

**Database facts to verify before models are final \[VERIFY\]**

| Fact | Why it matters |
| --- | --- |
| MySQL or MariaDB, and exact version | CHECK constraints are enforced only on MySQL 8.0.16 and later, and MariaDB 10.2.1 and later. Older versions accept them and ignore them |
| InnoDB with utf8mb4 | Needed for row locking (numbering) and full character support |
| JSONField support | Used for audit details and filed figures. If unsupported, use text with JSON inside |
| Trigger and privilege rights | Database level immutability needs triggers. Shared hosting often forbids them |
| Whether PostgreSQL is offered | Would allow partial unique indexes and stronger guards |

The schema deliberately avoids partial indexes and anything MySQL cannot do, so it runs on either engine.

## 2. Design principles

1. **Money is exact.** All money is `Decimal`, never float. Rounding happens in one helper.
2. **Issued means frozen.** Quotes, invoices and locked BOQ versions never change. Corrections are new versions, voids, reversals or credit notes.
3. **Nothing is hard deleted.** Soft delete plus history. Foreign keys use PROTECT, so a used record cannot disappear.
4. **Snapshots on issue.** Totals, tax rates and key text are copied onto the document at issue time so later changes elsewhere never rewrite history.
5. **Cached totals are verifiable.** Fields such as invoice balance are cached for speed, and a nightly check recomputes them from source rows.
6. **One source of truth per fact.** Statements are derived from source tables, not typed again.
7. **Custom user model from day one \[Decision\].** Django cannot switch user models cleanly later. `accounts.User` extends `AbstractUser`.
8. **Two identifiers \[Decision\].** Internal `id` is a big integer (matches `DEFAULT_AUTO_FIELD` \[Built\]). URLs use a random `public_id` UUID so records cannot be guessed by counting.

## 3. Conventions

**Type notation:** `str(n)` varchar, `text`, `dec(16,2)` money, `dec(14,3)` quantity, `pct` decimal(6,2) percentage, `int`, `bool`, `date`, `dt` datetime stored in UTC, `uuid`, `json`, `FK Model` protected foreign key, `?` means nullable, `enum(a,b)` a fixed list.

**Base fields (mixins)**

| Mixin | Fields | Used by |
| --- | --- | --- |
| Stamped | `created_at dt`, `updated_at dt`, `created_by FK User ?`, `updated_by FK User ?` | Every business table unless noted |
| SoftDelete | `is_deleted bool default false`, `deleted_at dt ?`, `deleted_by FK User ?` | Every business table except append only tables |
| PublicId | `public_id uuid unique` | Records shown by URL: Client, Lead, Project, BOQ, Quote, Invoice, Expense, File |
| History | simple\_history copy table `Historical<Model>` | Lead, Client, Project, RateItem, BOQVersion, Quote, Invoice, Payment, Expense, TaxRate, TaxPeriod, CompanyProfile |

The default manager hides soft deleted rows. `all_objects` shows them to Admin tools.

**Currency:** every money bearing table has `currency str(3) default 'UGX'`. MVP rule: one currency per document.

## 4. Relationship map

```
Lead  --converts to-->  Client  --has many-->  Project
Project --has many--> BOQ --has many--> BOQVersion --has many--> BOQSection --has many--> BOQItem
RateItem --copied into--> BOQItem          Supplier --supplies--> RateItem (note), Expense
BOQVersion (locked) --issued as--> Quote --accepted--> Project.contract_value
Project --has many--> Invoice --has many--> InvoiceLine, Payment, WithholdingEntry, CreditNote
Project --has many--> Expense --belongs to--> ExpenseCategory, Supplier, (optional) BOQSection
Project --has many--> PhaseHistory, Milestone, ProjectMember, File
TaxPeriod --collects--> Invoice VAT, Expense VAT, WithholdingEntry, StatutoryEntry
User --acts in--> AuditEvent, history tables, approvals
```

A visual ERD can be generated from the finished Django models and added to this document after the models exist.

## 5. Data dictionary

Base mixins are not repeated per table. Statuses are defined in Section 6.

### 5.1 Accounts and access

```
User  (accounts, extends AbstractUser)   Stamped not needed
  phone            str(30) ?
  job_title        str(80) ?
  must_change_password  bool default false
  (is_active used to disable; users are never deleted)
  Roles are Django Groups: Admin, Manager, Engineer, Accountant

ProjectMember   Stamped
  project          FK Project
  user             FK User
  role_on_project  enum(manager, engineer)
  removed_at       dt ?              (clear it to reactivate)
  unique (project, user)
```

### 5.2 Settings and lookups

```
CompanyProfile   (single row)   History
  legal_name str(200), trading_name str(200) ?, address text, phone str(30), email, website
  tin str(30) ?, vat_number str(30) ?, vat_registered bool
  bank_name, bank_account_name, bank_account_number (shown on invoices)   [Open] exact payment details
  mobile_money_details text ?, logo FK File ?, default_currency str(3)
  default_payment_terms_days int, invoice_footer text ?, quote_footer text ?

AppSetting       key str(80) unique, value json, description str(200)
  (BOQ calculation defaults, overdue grace days, expense approval limit, session length)

DocumentSequence key str(30), year int, last_value int      unique (key, year)
  keys: quote, invoice, credit_note, project

Unit             code str(10) unique, name str(60), is_active
ProjectType      name str(80) unique, is_active, sort_order
ExpenseCategory  name str(80) unique, kind enum(direct_cost, overhead), is_active, sort_order
TextTemplate     kind enum(quote_terms, quote_exclusions, invoice_terms, email), name, body text,
                 is_default bool
```

### 5.3 CRM

```
Client          PublicId, History
  name str(200), client_type enum(individual, company, government, ngo)
  tin str(30) ?, email ?, phone str(30) ?, address text ?, notes text ?
  is_withholding_agent bool ?        [Open] confirm how Jimcan tracks this
  default_payment_terms_days int ?

Contact         client FK Client, name, role ?, phone ?, email ?, is_primary bool

Lead            PublicId, History
  client FK Client ?  (set on conversion), name str(200), phone, email ?
  project_type FK ProjectType ?, location str(200) ?, details text ?
  source enum(website, referral, walk_in, phone, other)
  status enum(new, contacted, site_visit, quoted, won, lost), lost_reason text ?
  assigned_to FK User ?, received_at dt, next_follow_up date ?, estimated_value dec(16,2) ?

LeadActivity    lead FK Lead, kind enum(call, meeting, site_visit, note, email)
  occurred_at dt, outcome str(200) ?, notes text ?, next_follow_up date ?

RateLimitHit    scope str(30), key_hash char(64), created_at dt      (no soft delete)
  stores a hash of the visitor address, never the raw address, for spam limits
```

### 5.4 Projects

```
Project         PublicId, History
  code str(20) unique (from sequence, for example P-2026-001), title str(200)
  client FK Client, lead FK Lead ?, manager FK User ?, location str(200)
  status enum(active, on_hold, completed, cancelled)
  phase enum(brief, design, foundation, superstructure, finishes, handover)
  contract_value dec(16,2) default 0, currency, accepted_quote FK Quote ?
  start_date ?, target_completion ?, actual_completion ?, description text ?

PhaseHistory    (append only) project FK, from_phase ?, to_phase, changed_by FK User, changed_at dt, note ?
Milestone [S]   project FK, title, due_date, completed_on ?, sort_order
VariationOrder [S]  project FK, number, description, amount dec(16,2), status enum(draft, approved, rejected)
```

### 5.5 Rate library and BOQ

```
RateItem        History
  code str(30) unique, description str(300), unit FK Unit
  category enum(material, labour, plant, subcontract)
  rate dec(16,2), currency, supplier FK Supplier ?, notes ?, effective_from date, is_active bool

RateHistory [S] (append only) rate_item FK, old_rate, new_rate, changed_by, changed_at

BOQ             PublicId
  project FK Project ?, lead FK Lead ?, title str(200)
  check: project or lead must be present

BOQVersion      History
  boq FK BOQ, version_no int, status enum(draft, locked, superseded), copied_from FK self ?
  preliminaries_pct pct, contingency_pct pct, overhead_profit_pct pct, vat_rate pct, vat_applies bool
  subtotal dec(16,2), preliminaries_amount, contingency_amount, overhead_profit_amount
  total_excl_vat, vat_amount, total_incl_vat                (recomputed while draft, frozen at lock)
  locked_at dt ?, locked_by FK User ?, content_hash char(64) ?, notes text ?
  unique (boq, version_no)

BOQSection      version FK BOQVersion, code str(10), title str(200), sort_order int, subtotal dec(16,2)

BOQItem
  section FK BOQSection, item_no str(20), description str(300), unit FK Unit
  quantity dec(14,3), rate dec(16,2), amount dec(16,2)       (amount = quantity x rate, rounded, set by service)
  rate_item FK RateItem ?, is_custom bool, is_provisional bool, vat_exempt bool
  notes ?, sort_order int
  checks: quantity >= 0, rate >= 0, amount >= 0
```

The `content_hash` is a SHA 256 of the version's settings and every item at the moment of locking. A nightly check recomputes it for locked versions, and any mismatch is raised as an alert.

### 5.6 Quotes

```
Quote           PublicId, History
  number str(30) unique ?   (assigned at issue so drafts never burn a number)
  boq_version FK BOQVersion, client FK Client, project FK Project ?, lead FK Lead ?
  revision_of FK self ?, status enum(draft, sent, accepted, rejected, expired)
  issued_on date ?, valid_until date ?, sent_at dt ?, accepted_at dt ?
  accepted_by_name str(200) ?, rejected_reason text ?
  terms text, exclusions text ?, notes text ?
  total_excl_vat, vat_amount, total_incl_vat, currency       (copied from the BOQ version at issue)
  pdf_file FK File ?
  check: valid_until >= issued_on
```

### 5.7 Invoicing and payments

```
Invoice         PublicId, History
  number str(30) unique ?   (assigned at issue)
  project FK Project, client FK Client, quote FK Quote ?
  invoice_type enum(deposit, stage, boq, custom, final)
  status enum(draft, sent, part_paid, paid, void)           (overdue is computed, not stored)
  issue_date ?, due_date ?, currency
  subtotal_excl_vat, vat_rate pct, vat_amount, total_incl_vat
  amount_paid, wht_total, credited_total, balance               (cached, verified nightly)
  retention_pct pct ?, retention_held dec(16,2) default 0 [S]
  terms text ?, notes text ?
  voided_at dt ?, voided_by FK User ?, void_reason text ?, pdf_file FK File ?
  check: due_date >= issue_date

InvoiceLine     invoice FK, description str(300), quantity dec(14,3), unit_price dec(16,2),
                amount dec(16,2), vat_applicable bool, boq_item FK BOQItem ?, sort_order

Payment         History
  invoice FK Invoice, received_on date, amount dec(16,2) (> 0), method enum(cash, bank, mobile_money, cheque)
  reference str(100) ?, is_overpayment bool default false, note ?, received_by FK User
  reversed_at dt ?, reversed_by FK User ?, reversal_reason text ?    (payments are never edited or deleted)

WithholdingEntry
  direction enum(receivable, payable [S])
  invoice FK Invoice ?, payment FK Payment ?, expense FK Expense ? (payable only)
  amount dec(16,2), certificate_ref str(100) ?, certificate_date ?, status enum(claimed, certificate_received)
  check: exactly one of invoice or expense is set

CreditNote [S]  number unique ?, invoice FK Invoice, issue_date, reason text,
                amount_excl_vat, vat_amount, total, voided_at ?
RetentionEntry [S]  invoice FK Invoice, kind enum(held, released), amount, entry_date, note ?
```

### 5.8 Expenses and suppliers

```
Supplier        name str(200), contact_person ?, phone ?, email ?, address ?, tin ?, notes ?, is_active

Expense         PublicId, History
  project FK Project ?, is_overhead bool, category FK ExpenseCategory
  boq_section FK BOQSection ?  (for budget versus actual by section)
  supplier FK Supplier ?, expense_date date, description str(300)
  amount_total dec(16,2), vat_amount dec(16,2) default 0, amount_net dec(16,2)   (net = total minus VAT)
  vat_claimable bool, currency, payment_method enum(cash, bank, mobile_money, cheque) ?
  payment_status enum(paid, unpaid), due_date ?, paid_on ?, reference ?
  status enum(draft, pending, approved, rejected, reversed)
  submitted_by FK User, approved_by FK User ?, approved_at ?, rejection_reason ?
  reversed_by FK User ?, reversed_at ?, reversal_reason ?
  receipt_missing bool default false
  check: exactly one of (project set) or (is_overhead true)
  check: amount_total >= 0, vat_amount >= 0, vat_amount <= amount_total
```

Receipts are attached through `File.expense`.

### 5.9 Tax

```
TaxRate         History
  tax_type enum(vat, wht_receivable, wht_payable, nssf_employee, nssf_employer, paye_note)
  name str(80), rate pct, effective_from date, effective_to date ?, threshold_amount dec(16,2) ?, notes ?
  (the active rate is the one whose date range contains the document date;
   overlapping ranges for one type are rejected by the service)

TaxPeriod       History
  kind enum(vat, paye_nssf, wht), period_start date (first day of month)
  status enum(open, ready, filed, amended), filed_on ?, filed_by FK User ?, filing_reference str(100) ?
  filed_figures json ?      (the exact totals at the time of filing)
  unique (kind, period_start)

StatutoryEntry [S]  period FK TaxPeriod, kind enum(paye, nssf_employee, nssf_employer, other),
                    amount dec(16,2), paid_on ?, reference ?, notes ?
```

### 5.10 Files

```
File            PublicId
  kind enum(photo, receipt, drawing, contract, quote_pdf, invoice_pdf, report, other)
  original_name str(255), stored_path str(300) (random name, outside web root)
  mime_type str(100), size_bytes int, sha256 char(64), width int ?, height int ?
  thumbnail_path str(300) ?, caption str(300) ?, taken_at dt ?, phase (project phase when taken) ?
  upload_uuid uuid unique ?   (client generated, makes retries safe)
  parents (nullable): project FK, lead FK, expense FK, invoice FK, quote FK
  uploaded_by FK User
  check: at least one parent is set (except company logo)
  approved_for_portfolio bool default false [C]
```

### 5.11 Notifications and email

```
Notification    user FK User, kind str(40), title str(200), body text ?, link_url str(300) ?
                related_type str(60) ?, related_id str(40) ?, read_at dt ?        (no soft delete)
NotificationPreference [S]  user FK, kind, email_enabled bool, inapp_enabled bool    unique (user, kind)
EmailOutbox     to_email, subject str(200), body_text, body_html ?, status enum(pending, sent, failed)
                attempts int, last_error text ?, next_attempt_at dt, sent_at dt ?, dedupe_key str(100) unique ?
```

### 5.12 Audit, jobs and imports

```
AuditEvent      (append only, no edit or delete in the app)
  occurred_at dt, user FK User ? (null for system), action enum(create, update, status_change, lock, issue,
  void, reverse, payment, filing, override, login, login_failed, permission_denied, export, user_change, job)
  object_type str(60), object_id str(40), summary str(255), details json ?, ip_address ?

JobRun          job_name str(60), started_at dt, finished_at dt ?, status enum(ok, failed), message text ?, details json ?
                (backups, restore tests, consistency checks, email sender; feeds the system health screen)

ImportBatch     kind str(40), filename str(255), status enum(previewed, applied, rolled_back), summary json,
                created_at, created_by, rolled_back_at ?
ImportedRow     batch FK ImportBatch, model str(60), object_id str(40), source_row int

Historical<Model>  generated by django-simple-history: all fields of the model plus history_id,
                   history_date, history_user, history_type, history_change_reason
```

## 6. Enumerations (single source for statuses)

| Entity | Values | Notes |
| --- | --- | --- |
| Lead | new, contacted, site\_visit, quoted, won, lost | Matches App Flow section 7 |
| BOQ version | draft, locked, superseded |  |
| Quote | draft, sent, accepted, rejected, expired |  |
| Project status | active, on\_hold, completed, cancelled |  |
| Project phase | brief, design, foundation, superstructure, finishes, handover | Matches PRD |
| Invoice | draft, sent, part\_paid, paid, void | Overdue is computed |
| Expense | draft, pending, approved, rejected, reversed |  |
| Tax period | open, ready, filed, amended |  |
| Payment method | cash, bank, mobile\_money, cheque | \[Open\] confirm the list |
| Rate category | material, labour, plant, subcontract |  |

Status change rules live in services, not in the database, so a change in rules does not need a migration.

## 7. Constraints and integrity

**Unique:** Project.code, Quote.number, Invoice.number, CreditNote.number, RateItem.code, Unit.code, BOQVersion (boq, version\_no), TaxPeriod (kind, period\_start), DocumentSequence (key, year), File.upload\_uuid, ProjectMember (project, user), NotificationPreference (user, kind), EmailOutbox.dedupe\_key, every public\_id.

Numbers are nullable until issue. Both MySQL and MariaDB allow several NULLs in a unique column, so drafts never collide.

**Check constraints (enforced only if the database version supports them \[VERIFY\]; the service layer and tests enforce them regardless)**

- quantities, rates and amounts are not negative; Payment.amount is above zero
- Expense: project is set or is\_overhead is true, never both, never neither
- BOQ: project or lead is set
- File: at least one parent is set
- WithholdingEntry: exactly one source (invoice or expense)
- dates in order (due after issue, valid until after issue, completion after start)
- vat\_amount not above amount\_total

**Delete rules:** every business foreign key is PROTECT. Nothing cascades. Users are disabled, never deleted. Removing something that is used shows what depends on it.

**Immutability**

- A locked BOQ version, issued quote, issued invoice and filed tax period reject edits in the model's `save()` and in the service layer. History tables and tests prove it.
- The TRD mentions a database level guard for locked BOQ versions. That needs trigger rights, which shared hosting may not give **\[VERIFY\]**. If triggers are unavailable, protection stays in code plus the nightly `content_hash` check, and the TRD wording should be softened to match.
- Audit and history tables have no edit or delete path in the application. A shared hosting database user normally has full rights to its database, so protection is by code, tests and off server backups, not by database permissions **\[VERIFY\]**.

## 8. Money design

| Topic | Rule |
| --- | --- |
| Precision | Money `dec(16,2)`, quantities `dec(14,3)`, percentages `dec(6,2)` |
| Rounding | Whole shilling, half up, applied to each BOQ line and invoice line amount. Totals are sums of rounded lines. One helper function does all rounding |
| BOQ order | Items, then section subtotals, then subtotal, preliminaries, contingency, overheads and profit, total excluding VAT, VAT, total including VAT (PRD section 9) |
| VAT exempt items | Excluded from the VAT base. Marked on the line |
| Snapshots | Rate used, VAT rate and totals stored on the document at issue |
| Cached fields | Invoice `amount_paid`, `wht_total`, `credited_total`, `balance` and BOQ section subtotals. Updated inside the same transaction as the change |
| Invoice balance | `total_incl_vat - amount_paid - wht_total - credited_total` |
| Overpayment | Allowed only if the payment is flagged `is_overpayment`, giving a negative balance that is shown as credit |
| Currency | Stored per document. MVP blocks mixing |

## 9. Numbering

- `DocumentSequence (key, year, last_value)`.
- At issue: inside one transaction, lock the sequence row (`select_for_update`), add one, assign the number, save the document. If anything fails the whole transaction rolls back, so no gap appears.
- Format is configurable, for example `INV-2026-0001`. Voiding keeps the number.
- Concurrency test runs on the real database engine in CI **\[VERIFY\]**, since SQLite does not lock rows the same way.

## 10. Reporting design

MVP statements are derived from source tables by tested selector functions. No separate ledger. Dates are in East Africa Time, and amounts exclude VAT unless stated.

| Report | Definition |
| --- | --- |
| Profit and loss (accrual basis, MVP default) | Revenue = issued, non void invoices by issue date, `subtotal_excl_vat`, less credit notes. Costs = approved, non reversed expenses by expense date, `amount_net`, split by category and project. Overheads where `is_overhead` is true |
| Profit and loss (cash basis) \[S\] | Receipts and paid expenses by payment date, shown net of VAT |
| Cash flow | Money in = non reversed payments by `received_on` (gross). Money out = approved expenses with `payment_status = paid` by `paid_on` or expense date (gross). Net = in minus out |
| Receivables and ageing | Issued, non void invoices with `balance > 0`, grouped by days past `due_date`: current, 1 to 30, 31 to 60, over 60 |
| Payables | Approved expenses with `payment_status = unpaid`, grouped by due date |
| Project profitability | Contract value, invoiced to date, received to date, costs to date (approved expenses), margin = invoiced minus costs, with the basis shown |
| Budget versus actual | Locked BOQ cost budget by section against approved expenses linked to that section |
| VAT summary | Output VAT = `vat_amount` of issued non void invoices in the period, less credit notes. Input VAT = `vat_amount` of approved expenses with `vat_claimable`. Net = output minus input |
| Withholding tax receivable | Sum of `WithholdingEntry` receivable amounts, by period and certificate status |
| Balance view | Cash position (payments less paid expenses since opening balance), receivables, payables, retention held |
| Reconciliation | Recomputes each total a second way and lists any difference |

Which VAT figure applies to which period (invoice date or payment date) and whether the opening balances need their own table **\[Open\]**: confirm with the accountant before the tax module is built.

If accounting depth grows, a `LedgerEntry` table can be added behind the same selectors without changing source tables (TRD section 19).

## 11. Indexes

Indexes beyond primary and unique keys, chosen from the screens and reports above:

| Table | Index |
| --- | --- |
| Lead | (status, next\_follow\_up), (assigned\_to, status), phone, email |
| Client | name, phone, email |
| Project | (status, phase), client, manager |
| BOQItem | section, rate\_item |
| BOQSection | version |
| Quote | (status, valid\_until), client, project |
| Invoice | (status, due\_date), (project, status), client, issue\_date |
| Payment | invoice, received\_on |
| Expense | (project, status), (expense\_date), (category, expense\_date), supplier, (payment\_status, due\_date) |
| WithholdingEntry | invoice, certificate\_ref |
| File | project, expense, (kind, created\_at) |
| Notification | (user, read\_at) |
| EmailOutbox | (status, next\_attempt\_at) |
| AuditEvent | (object\_type, object\_id), (user, occurred\_at), occurred\_at |
| RateLimitHit | (scope, key\_hash, created\_at) |

Indexes are reviewed with real query plans after the first month of data, not guessed.

## 12. Permissions matrix

R read, W create and edit (while allowed by status), A approve, V void or reverse, X export, dash none. Enforced in services and views, and tested for every cell.

| Data | Admin | Manager | Engineer | Accountant |
| --- | --- | --- | --- | --- |
| Users, settings, tax rates | R W | R | - | R |
| Clients, contacts, leads | R W V | R W | - | - |
| Projects | R W V | R W (own or all, \[Open\]) | R (assigned) | R |
| Phase change | W | W | W (assigned) | - |
| Rate library | R W | R W | - | R |
| BOQ and versions | R W V | R W | - | R |
| Quotes | R W V | R W | - | R |
| Invoices and payments | R W V | R W | - | R X |
| Expenses | R W A V | R W A | W own, R own | R X |
| Suppliers | R W | R W | - | R |
| Tax periods and filings | R W V | R | - | R W X |
| Statements and reports | R X | R (own projects) | - | R X |
| Files | R W V | R W | R W (assigned) | R |
| Audit log and system health | R | - | - | - |

Site Engineers never receive pricing, margin, invoice or statement data in any query.

## 13. Seed data and migrations

**Seeded by the first migration or a setup command**

- Groups and their permissions
- Units: a standard construction set (for example m, m2, m3, kg, tonne, number, item, lump sum, day, hour, litre, bag) **\[Open\]** confirm
- Expense categories from the PRD: Materials, Labour, Plant and equipment, Subcontractors, Transport, Permits and fees, Overheads
- Project phases and statuses (as code enumerations, not tables)
- Tax rates as **placeholders** for VAT 18 percent and withholding tax 6 percent, each with a note "verify with accountant" and an effective date **\[Open\]** confirm current URA rates and thresholds
- Empty text templates for terms and exclusions
- Sequences for quote, invoice, credit note and project

**Migration rules**

- Every release has its migrations tested on a copy of production data.
- Expand then contract: add new columns first, move data, remove old columns only in a later release.
- No migration deletes money or audit data.
- A `load_demo_data` command creates fake clients, projects, a BOQ and invoices for local use only. It refuses to run when debug is off.

## 14. Data import mapping

Imports use a preview, an error report, and a batch record so a bad import can be rolled back through `ImportedRow`.

| Source (assumed spreadsheet) | Target | Key checks |
| --- | --- | --- |
| Client list | Client, Contact | Duplicate phone or email, missing name |
| Rate sheet | RateItem | Unit exists, rate numeric and above zero, unique code |
| Supplier list | Supplier | Duplicate names |
| Open projects | Project | Client exists, contract value numeric |
| Open invoices | Invoice, InvoiceLine, Payment | Totals tie to source, balance matches |
| Expense history | Expense | Category, date, amount, project mapping |
| Opening balances | Opening entries (design to be agreed) | Totals agree with the accountant **\[Open\]** |

The real spreadsheet layouts have not been seen **\[Open\]**. This table is a starting assumption.

## 15. Retention and privacy

**Personal data held:** names, phones, emails and addresses in Client, Contact and Lead; staff details in User; hashed visitor addresses in RateLimitHit; IP addresses in AuditEvent; photos that may show people in File.

- Soft delete hides a record. A separate Admin only anonymise action replaces personal fields with placeholders while keeping financial rows intact, for correction or removal requests.
- RateLimitHit rows are purged weekly. AuditEvent IP addresses are cleared after 12 months **\[Decision\]**.
- Financial records are kept for the legal period **\[Open\]** confirm with the accountant.
- Bank and mobile money details of the company appear in CompanyProfile only. No client card or account numbers are stored anywhere.

## 16. Consistency checks (run nightly, results in JobRun)

1. Each invoice `balance` equals its recomputed value
2. Each invoice `amount_paid` equals the sum of non reversed payments
3. Each locked BOQ version's `content_hash` matches its content
4. Each BOQ section `subtotal` equals the sum of its item amounts
5. Sum of issued invoice totals by month equals the revenue reported
6. Issued numbers per key and year have no gaps and no duplicates
7. No money row is linked to a soft deleted parent
8. Every file record has a file on disk, and every file on disk has a record
9. No filed tax period contains entries created after filing without an override event
10. No float style values (more than 2 decimal places) exist in money columns

A failed check emails the Admin and shows on the system health screen.

## 17. Schema tests required before release

- Models reject edits to locked and issued records
- Hard deletion of financial models is blocked
- Constraint checks behave the same on the real engine as on SQLite
- Numbering under concurrent requests produces no gaps or duplicates
- Reports reconcile on randomised data
- No code path uses floats for money (a test scans the source)
- Migrations apply forward on a copy of production data and the previous app version still runs after an expand step

## 18. Open decisions and questions

1. Which database engine and version does the Namecheap plan provide, and are triggers allowed?
2. Should Manager access to projects be limited to assigned ones?
3. Which payment methods does Jimcan really use, and are cheques used?
4. Does Jimcan need a project code format or is the plain sequence fine?
5. VAT timing: tax point by invoice date or by payment date, and how does the accountant want opening balances entered?
6. Does Jimcan track supplier bills with part payments, or paid in full and unpaid only?
7. Do variation orders and retention need to be in the MVP, or can they wait for 1.1?
8. What spreadsheet layouts exist today for rates, clients, invoices and expenses?
9. How long must financial records be kept?
10. Should BOQ items link to expenses at section level, or at item level for finer budget control?

## 19. Approvals

| Name | Role | Decision | Date |
| --- | --- | --- | --- |
| George | Developer and technical owner |  |  |
|  | Jimcan owner or director |  |  |
|  | Accountant |  |  |
