# Jimcan Operations Dashboard: App Flow Document

Version 0.1 (draft for review) | 24 October 2026 | Author: George | Companion to PRD v0.1 and TRD v0.1

## 1. Purpose and how to read this

This document describes **how people move through the system**: which screens exist, how they connect, what each role sees, what happens at every step, and what happens when something goes wrong. It is the bridge between the PRD (what) and the Design Brief and build (screens and code).

**Notation**

- **\[Role\]** is who acts: \[Admin\], \[Manager\], \[Engineer\], \[Accountant\], \[Visitor\] (public website), \[System\] (automatic).
- **S-xx** is a screen ID from the screen inventory in Section 9.
- **PRD ref** points to requirement IDs, for example B1 or E10.
- "Alt" marks an alternative path. "Edge" marks an unusual case that still must work.

## 2. Entry points and landing screens

| Role | After sign in, lands on | Main purpose |
| --- | --- | --- |
| Admin | Dashboard (S-10) | Full overview, approvals, settings |
| Manager | Dashboard (S-10), filtered to their leads and projects | Run leads, BOQs, invoices, expenses |
| Engineer | My Projects (S-40) | Upload photos, update phase, log site expenses |
| Accountant | Reports home (S-80) | Review tax and statements, export |
| Visitor | Public site contact form | Send an enquiry (no login) |

Direct links (for example from an email alert) open the target screen after sign in, then continue to it.

## 3. Sitemap

```
Public site (separate, static)
  Contact form  ->  POST /public/leads/

Dashboard app (login required)
  /login/  /logout/  /password/change/  /password/reset/
  /                          Dashboard
  /leads/                    Lead list, board view
  /leads/new/  /leads/<id>/  Lead detail, activities
  /clients/  /clients/<id>/  Client list and detail
  /projects/                 Project list
  /projects/<id>/            Overview | BOQ | Quotes | Invoices | Expenses | Files | History
  /rates/                    Rate library
  /boq/<id>/                 BOQ builder, versions
  /quotes/  /quotes/<id>/    Quote list, detail, PDF
  /invoices/  /invoices/<id>/ Invoice list, detail, payments
  /expenses/  /expenses/new/ Expense list, entry, approval queue
  /suppliers/                Supplier list and balances
  /tax/                      Tax calendar, VAT summary, withholding, filings
  /reports/                  P&L, cash flow, balance view, project profit, ageing
  /files/                    Upload queue (also inside each project)
  /notifications/            Alert list
  /settings/                 Company, numbering, tax rates, templates, lists, users
  /audit/                    Audit log (Admin)
  /<hidden-admin-path>/      Django admin for master data (Admin only)
```

## 4. Navigation by role

| Menu item | Admin | Manager | Engineer | Accountant |
| --- | --- | --- | --- | --- |
| Dashboard | Yes | Yes | No | Reports home instead |
| Leads and Clients | Yes | Yes | No | No |
| Projects | All | Assigned or all (setting) | Assigned only | Read only |
| BOQ and Rates | Yes | Yes | No | Read only |
| Quotes | Yes | Yes | No | Read only |
| Invoices | Yes | Yes | No | Read only |
| Expenses | Yes | Yes | Submit own | Read only |
| Tax | Yes | View only | No | Yes |
| Reports | Yes | Project reports | No | Yes |
| Files | Yes | Yes | Assigned projects | Read only |
| Settings and Audit | Yes | No | No | No |

Items a role cannot use are **hidden**, and the same rule is **enforced on the server**, so a typed URL returns a permission denied page (S-03).

## 5. Global behaviours (apply to every screen)

**Sign in and session**

- Visiting any internal URL while signed out redirects to sign in, then back to that URL.
- Wrong password shows one generic message. Repeated failures slow or lock the account and notify Admin.
- Idle timeout shows a warning at 1 minute, then signs out. Unsaved form data is kept in the browser where possible, and a returning user is offered it back.
- Sign out clears the session and returns to sign in.

**Screen states, every list and page has all of these**

- **Loading:** skeleton rows or a spinner after 300 ms. No frozen blank screens.
- **Empty:** a plain sentence and one clear action (for example "No leads yet. Add the first lead").
- **Error:** a plain message, what to try, and a retry button. Technical detail goes to the log, not the screen.
- **No permission:** S-03 with a link back to the user's home.
- **Not found:** S-04 with search and home links.
- **Offline:** a banner reading "You are offline. Uploads will send when signal returns". Pages that need live data show the last loaded view as read only or a retry prompt. Money forms refuse to submit offline.

**Forms**

- Required fields marked. Errors appear beside the field and in a summary at top.
- Submit buttons disable during save to prevent double submit.
- Defaults are pre filled (currency UGX, VAT from settings, today's date).
- Leaving a form with unsaved changes asks for confirmation.

**Confirmations**

- Destructive or hard to reverse actions (void, lock, issue, file a tax period, delete section, reassign) always show a confirmation naming the consequence, and ask for a reason where the PRD requires one.
- Successful actions show a short toast. Failures stay on screen until dismissed.

**Lists**

- 25 rows per page, filters and sort in the URL so links can be shared, search box on top, export button where permitted, and filters are remembered per user for the session.

**Notifications**

- A bell shows unread alerts and links to S-90. Email copies follow the notification table in Section 11.

## 6. Core journeys

### J1. First run and user onboarding

**Actors:** \[Admin\], \[System\]. **PRD ref:** A1 to A7, M1 to M5.

1. &#91;Admin\] creates the first superuser from the command line during deployment.
2. &#91;Admin\] signs in and is taken to a **setup checklist** (S-95): company profile, logo, TIN and VAT number, numbering formats, tax rates, categories, units, templates.
3. &#91;Admin\] adds users (S-93): name, email, role, assigned projects. \[System\] emails a set password link valid for 24 hours.
4. User opens the link, sets a password that meets the policy, signs in, and lands on their home screen.

**Alt:** link expired, user requests a new one from sign in. **Edge:** user email already exists, system explains and offers to reactivate. Checklist items show done or not done and block nothing, except that issuing a quote or invoice requires company details.

### J2. Website enquiry becomes a lead

**Actors:** \[Visitor\], \[System\], \[Manager\]. **PRD ref:** B1, B9, B10.

1. &#91;Visitor\] fills the public form (name, phone, email, project type, location, details) and sends.
2. &#91;System\] checks honeypot, timing token and rate limit. Spam is dropped silently and logged.
3. &#91;System\] checks for a duplicate phone or email. If found, it attaches the enquiry as a new activity on the existing lead or client and flags it.
4. Otherwise \[System\] creates a lead with status New and emails \[Admin\] and \[Manager\]s: "New lead: \[project type\] in \[location\]".
5. &#91;Visitor\] sees a thank you message with an expected response time.

**Alt:** invalid input, form shows errors and keeps entries. **Edge:** the system is down, the static site shows a fallback message with a phone number so no enquiry is lost.

### J3. Working a lead to a site visit

**Actors:** \[Manager\], \[Admin\]. **PRD ref:** B2 to B11.

1. &#91;Manager\] opens Leads (S-20) and sees New leads first, with overdue follow ups highlighted.
2. Opens a lead (S-22). Reviews details and duplicate warnings.
3. &#91;Admin\] or \[Manager\] assigns the lead. \[System\] notifies the assignee.
4. Assignee logs a call (activity: type, outcome, notes, next follow up date). Status moves to Contacted.
5. Site visit booked: status Site visit, with date and place. Notes and photos are added after the visit.
6. Lead moves to **Quoted** automatically when a quote is sent, or manually.
7. Outcome: **Won** (create client and project, see J5) or **Lost** (reason required).

**Edge:** two people edit a lead at once, the second save is warned and shown the latest version. Reopening a Lost lead is allowed and logged.

### J4. From rates to BOQ to quote

**Actors:** \[Manager\], \[Admin\]. **PRD ref:** D1 to D5, E1 to E14, F1 to F7.

1. &#91;Manager\] maintains the rate library (S-50) so items and prices are current.
2. From a lead or project, \[Manager\] chooses **New BOQ** (S-51), names it, and picks a template or copies an earlier BOQ.
3. Adds sections (Substructure, Superstructure, and so on) and items. For each item: search the rate library, pick it, enter quantity. Custom items allowed with a flag. Totals update as typing happens.
4. Sets contingency, overheads and profit, VAT treatment. \[System\] shows the full calculation breakdown.
5. &#91;Manager\] reviews on the **internal view** (cost and margin) and previews the **client view** (prices only).
6. &#91;Manager\] chooses **Lock version**. Confirmation explains that it can no longer be edited. \[System\] stores the totals snapshot.
7. &#91;Manager\] creates a **quote** from the locked version (S-60): terms, validity, notes, exclusions from templates. Quote number assigned.
8. &#91;Manager\] previews the PDF, then marks as Sent, with an email option. Lead status becomes Quoted.
9. Client replies. \[Manager\] marks the quote **Accepted** or **Rejected**. Accepted updates the project contract value, or prompts to create the project (J5).
10. If the client wants changes, \[Manager\] creates **v2** by copying v1. v1 stays locked and visible. The quote revision references the earlier one.

**Alt:** import quantities by bulk paste from Excel with a preview of errors. **Edge:** a rate was archived after a draft used it, the line stays and shows an "archived rate" tag. A quote expires, status changes automatically and the manager is notified.

### J5. Creating and running a project

**Actors:** \[Manager\], \[Admin\], \[Engineer\]. **PRD ref:** C1 to C9.

1. After acceptance (or manually), \[Manager\] creates the project from the lead and quote, so client, location and contract value carry over.
2. Sets dates, assigns manager and engineers. Phase starts at Brief or Design.
3. The project page (S-31) is the working hub with tabs: Overview, BOQ, Quotes, Invoices, Expenses, Files, History.
4. As work advances, \[Manager\] or \[Engineer\] changes phase. \[System\] writes a phase history entry (who, when, from, to, optional note) and notifies the manager.
5. At Handover, \[Manager\] marks the project complete after checks (open invoices, unapproved expenses, retention). \[System\] warns about anything open but allows \[Admin\] to proceed with a reason.

**Edge:** an engineer is removed from a project mid way, their access ends immediately but their past uploads stay. A project placed On hold stops reminders but keeps data editable by Admin.

### J6. Recording and approving expenses

**Actors:** \[Manager\], \[Engineer\], \[Admin\]. **PRD ref:** H1 to H10.

1. &#91;Manager\] or \[Engineer\] chooses **Add expense** (S-70), from the project or the main menu.
2. Fills date, supplier (search or add new), project (or marks Overhead), category, amount, VAT charged, payment method, reference. Takes or attaches a receipt photo.
3. &#91;Engineer\] submissions go to **Pending approval**. \[Manager\] submissions are approved automatically unless over their limit.
4. &#91;Manager\] opens the approval queue (S-71), reviews receipt and details, then Approves, Rejects (reason required) or Asks for correction.
5. Approved expenses count in budget versus actual and statements. Rejected ones do not.

**Alt:** supplier bill not yet paid, entered as an unpaid bill with a due date, paid later with a payment record. **Edge:** the receipt is illegible or missing, the expense can be saved with a "receipt missing" flag that shows on reports. Duplicate check warns on same supplier, date and amount.

### J7. Invoicing and getting paid

**Actors:** \[Manager\], \[Admin\]. **PRD ref:** G1 to G12, I4.

1. &#91;Manager\] opens a project, then **New invoice** (S-65), and chooses a type: deposit, stage percentage, from BOQ items, or custom lines.
2. &#91;System\] fills lines and VAT, and shows the amount remaining on the contract.
3. &#91;Manager\] reviews, then **Issues** the invoice. Number assigned, document locked, PDF stored. Option to email it.
4. Status Sent. \[System\] flags it overdue the day after the due date and alerts the owner.
5. Money arrives. \[Manager\] opens the invoice, chooses **Record payment**: date, amount, method, reference. If the client withheld tax, enters the WHT amount and certificate reference.
6. &#91;System\] recalculates the balance. Status becomes Part paid or Paid. Payments appear in cash flow.
7. If retention is held, the invoice shows retention outstanding until released.

**Alt:** a mistake after issue, \[Admin\] voids (reason required) and the manager creates a replacement, or issues a credit note. **Edge:** payment above balance is blocked unless marked as overpayment with a note. Payment recorded on a void invoice is blocked.

### J8. Site engineer: photos and phase update on a phone

**Actors:** \[Engineer\], \[System\]. **PRD ref:** K1 to K7, C4.

1. &#91;Engineer\] opens the app from the home screen icon. Lands on My Projects (S-40) and taps a project.
2. Taps **Add photos**. Camera or gallery opens. Several photos can be selected.
3. The browser compresses each photo. Each shows a thumbnail with a status: Waiting, Sending, Sent.
4. &#91;Engineer\] picks the phase and adds a short note or caption (optional).
5. If signal is weak or gone, photos stay in the **waiting list** and retry automatically when online, and when the app is reopened.
6. &#91;Engineer\] may update the phase from the same screen. The change is saved like any phase change.
7. &#91;System\] shows sent photos in the project gallery and notifies the manager if configured.

**Edge:** the phone sleeps mid upload, retry continues on reopen. The same photo sent twice creates one record, thanks to the client generated ID. A file that fails validation shows why and can be removed from the queue. Storage full on the phone prompts the user to clear space.

### J9. Month end: tax and statements

**Actors:** \[Admin\], \[Accountant\], \[Manager\]. **PRD ref:** I1 to I10, J1 to J9.

1. &#91;System\] sends a reminder before the filing date. The tax calendar (S-85) shows what is due.
2. &#91;Admin\] or \[Accountant\] opens **Tax summary** for the month: VAT on sales, VAT on purchases, net payable, withholding tax received, PAYE and NSSF entries.
3. Each figure links to its source invoices and expenses. A **data quality panel** lists problems first: expenses without VAT info, draft invoices dated in the month, unapproved expenses.
4. Problems are fixed (go to J6 or J7 for corrections), then the summary is regenerated.
5. &#91;Admin\] exports to Excel or PDF for the accountant, files with URA outside the system, then marks the period **Filed** with a reference and date. The period locks.
6. &#91;Admin\] or \[Accountant\] opens Reports (S-80): profit and loss, cash flow, balance view, project profitability, receivables ageing. Chooses period and basis (cash or accrual). Exports as needed.
7. The **reconciliation page** confirms statement totals match source records.

**Edge:** a late invoice must be added to a filed month, \[Admin\] uses an override (reason required) and the system flags the period as amended. Rate change mid year, documents keep the rate in force on their date.

### J10. Administration and upkeep

**Actors:** \[Admin\]. **PRD ref:** M1 to M7, A3.

1. Manage users (S-93): add, change role, disable, reset password. Disabling ends active sessions.
2. Update settings (S-92): company details, numbering, tax rates with effective dates, templates, categories, units.
3. View the audit log (S-94): filter by user, record, action, date. Export for review.
4. Check system health: last backup time and size, last restore test date, job status, disk usage, failed emails (S-96).
5. Review access quarterly: list of users, last login, roles.

### J11. Everyday reporting and dashboard

**Actors:** \[Admin\], \[Manager\]. **PRD ref:** J5, J6, J9.

1. Dashboard (S-10) opens with KPI cards (active projects, receivables, spend, VAT payable), cash chart, project phase bars, and recent expenses. Cards link to the detailed lists.
2. Overdue invoices, overdue follow ups and pending approvals appear as an **Attention** strip with counts and links.
3. A manager sees figures for their own projects. An admin sees everything.

### J12. Corrections and exceptions

| Situation | Who | Flow |
| --- | --- | --- |
| Wrong quote sent | \[Manager\] | Create new version, mark old as superseded, send revised |
| Wrong invoice issued | \[Admin\] | Void with reason, new invoice, or credit note for partial fix |
| Wrong payment recorded | \[Admin\] | Reverse the payment entry with a reason, record the correct one |
| Wrong expense approved | \[Manager\] | Reverse with reason, enter correct expense |
| Entry into a filed period | \[Admin\] | Override with reason, period flagged as amended |
| Reopen a locked BOQ | Not allowed | Copy to a new version |
| Deleted by mistake | \[Admin\] | Restore from soft delete in Admin tools |
| User left the company | \[Admin\] | Disable account, reassign leads and projects |

Nothing in this table removes history. Every row creates an audit entry.

## 7. Status lifecycles

**Lead:** New, Contacted, Site visit, Quoted, Won or Lost. Reopen allowed from Lost to Contacted.

| From | To | Who | Condition |
| --- | --- | --- | --- |
| New | Contacted | Manager, Admin | Activity logged |
| Contacted | Site visit | Manager, Admin | Date set |
| Site visit | Quoted | System or Manager | Quote sent |
| Quoted | Won | Manager, Admin | Quote accepted or manual |
| Any open | Lost | Manager, Admin | Reason required |
| Lost | Contacted | Manager, Admin | Reopen note |

**BOQ version:** Draft, Locked, Superseded. Draft to Locked by Manager or Admin. Locked to Superseded when a newer version is issued.

**Quote:** Draft, Sent, Accepted, Rejected, Expired. Sent cannot return to Draft. A revision creates a new quote linked to the old.

**Project:** Active, On hold, Completed, Cancelled. Phases run Brief, Design, Foundation, Superstructure, Finishes, Handover and may move backward with a note.

**Invoice:** Draft, Sent, Part paid, Paid, Overdue (computed), Void. Draft to Sent by issuing. Sent or Part paid to Paid when balance is zero. Any issued status to Void by Admin with a reason.

**Expense:** Draft, Pending approval, Approved, Rejected, Reversed. Pending to Approved or Rejected by Manager. Approved to Reversed by Manager or Admin with a reason.

**Tax period:** Open, Ready, Filed, Amended. Filed locks the period. Admin override moves it to Amended.

## 8. Data handoffs between modules

| From | To | What carries over |
| --- | --- | --- |
| Website form | Lead | Contact details, project type, location, message |
| Lead | Client and Project | Name, phone, email, location, notes, activity history link |
| Rate library | BOQ item | Description, unit, rate (copied, then independent) |
| Locked BOQ version | Quote | Sections, items, totals snapshot |
| Accepted quote | Project | Contract value, scope reference |
| Project and quote | Invoice | Client, project, contract balance, VAT rate in force |
| Invoice and payments | Cash flow, receivables, VAT output | Dates, amounts, WHT |
| Expense | Budget versus actual, cash flow, VAT input | Project, category, date, VAT |
| Everything | Statements and tax summary | Read through tested selectors, never retyped |

## 9. Screen inventory

| ID | Screen | Purpose | Key actions | Roles |
| --- | --- | --- | --- | --- |
| S-01 | Sign in | Authenticate | Sign in, reset password | All |
| S-02 | Password reset and change | Recover and update password | Request, set | All |
| S-03 | Permission denied | Explain and redirect | Back to home | All |
| S-04 | Not found and error | Handle broken links and faults | Search, retry | All |
| S-10 | Dashboard | Overview and attention list | Open cards, charts | Admin, Manager |
| S-20 | Lead list and board | Triage and track | Filter, assign, add | Admin, Manager |
| S-21 | New lead | Manual entry | Save | Admin, Manager |
| S-22 | Lead detail | History, activities, follow ups | Log call, change status, convert | Admin, Manager |
| S-25 | Client list and detail | Client records and linked projects | Edit, add contact | Admin, Manager |
| S-30 | Project list | Browse projects | Filter, open | Admin, Manager, Accountant |
| S-31 | Project hub | Tabs for everything about a project | Change phase, open tabs | Admin, Manager, Engineer (limited) |
| S-40 | My projects | Engineer home | Open project, upload | Engineer |
| S-41 | Site upload | Add photos, queue status | Capture, caption, retry | Engineer, Manager |
| S-50 | Rate library | Maintain unit rates | Add, edit, archive, import | Admin, Manager |
| S-51 | BOQ builder | Build and price a BOQ | Add items, lock, export | Admin, Manager |
| S-52 | BOQ versions and compare | See history | Copy, compare | Admin, Manager |
| S-60 | Quote detail | Terms, preview, send, accept | Send, accept, revise | Admin, Manager |
| S-61 | Quote list | Track quotes | Filter | Admin, Manager |
| S-65 | Invoice create and detail | Issue and track | Issue, void, payments | Admin, Manager |
| S-66 | Invoice list and ageing | Receivables | Filter, export | Admin, Manager, Accountant |
| S-70 | Expense entry | Capture costs | Save, attach receipt | Admin, Manager, Engineer |
| S-71 | Expense approval queue | Review submissions | Approve, reject | Manager, Admin |
| S-72 | Expense list | Browse and filter | Export | Admin, Manager, Accountant |
| S-75 | Suppliers | Contacts and balances | Add, view bills | Admin, Manager |
| S-80 | Reports home | Choose report | Open | Admin, Accountant, Manager (project) |
| S-81 | Profit and loss | Income and cost by period | Filter, drill down, export | Admin, Accountant |
| S-82 | Cash flow | In and out by period | Filter, export | Admin, Accountant |
| S-83 | Balance view | Cash, receivables, payables | Export | Admin, Accountant |
| S-84 | Project profitability | Contract, cost, margin | Drill down | Admin, Manager (own), Accountant |
| S-85 | Tax calendar and summary | Due dates, VAT, WHT, PAYE | Export, mark filed | Admin, Accountant |
| S-86 | Reconciliation | Check totals | Run check | Admin, Accountant |
| S-90 | Notifications | Alert list | Open, mark read | All |
| S-92 | Settings | Company, numbering, tax, templates | Edit | Admin |
| S-93 | Users | Manage accounts | Add, disable, reset | Admin |
| S-94 | Audit log | Review history | Filter, export | Admin |
| S-95 | Setup checklist | First run guidance | Complete steps | Admin |
| S-96 | System health | Backups, jobs, disk | View | Admin |

## 10. Edge case and error handling matrix

| Case | Expected behaviour |
| --- | --- |
| Network lost while saving a form | Form stays open with a clear message, entries kept, retry button. No silent loss |
| Two users change the same record | Second saver is warned and sees the changes before choosing |
| Browser back after issuing a document | Page shows the locked state, not the old editable form |
| Number sequence conflict | Impossible by design. If the transaction fails, the user sees a retry message |
| Quantity zero, negative or huge | Field validation with limits and a confirmation for very large values |
| Rate missing or archived | Line flagged, totals still calculate, a warning shows before locking |
| VAT exempt items | Tagged on lines and excluded from the VAT base, shown in the breakdown |
| Currency mismatch | Blocked in MVP with an explanation |
| Large BOQ (300 plus lines) | Sections collapse, search within BOQ, saves per row |
| Upload too large or wrong type | Rejected with the reason before and after upload |
| PDF generation fails | Message with retry, the incident is logged, the data is untouched |
| Email fails | Stays in the outbox with retry, failure visible in system health |
| User disabled while signed in | Next request signs them out |
| Date in a locked period | Blocked, Admin override explained |
| Deleting something in use | Blocked with a list of what depends on it, archive offered |
| Slow connection on dashboard | Cards load first, chart loads after, no layout jump |
| Printing | Print styles for lists and documents, no navigation chrome |

## 11. Notification triggers

| Event | Recipients | Channel | Timing |
| --- | --- | --- | --- |
| New lead | Admin, Managers | Email, in app | Immediate |
| Lead assigned | Assignee | Email, in app | Immediate |
| Follow up overdue | Assignee, Admin | In app, daily email digest | Daily 06:00 |
| Quote expiring | Quote owner | In app | 3 days before |
| Quote accepted | Admin, Manager | Email, in app | Immediate |
| Phase changed | Project manager | In app, optional email | Immediate |
| Expense needs approval | Approvers | In app, email digest | Immediate and daily |
| Expense rejected | Submitter | In app | Immediate |
| Invoice overdue | Owner, Admin | In app, email | Day after due, weekly after |
| Payment recorded | Admin | In app | Immediate |
| Tax due soon | Admin, Accountant | Email, in app | 7 and 2 days before |
| Backup failed or job failed | Admin | Email | Immediate |
| New user or password reset | User | Email | Immediate |

Users can turn off non critical alerts (not security or failure alerts).

## 12. Traceability to the PRD

| Journey | PRD modules covered |
| --- | --- |
| J1 | A, M |
| J2, J3 | B, L |
| J4 | D, E, F |
| J5 | C |
| J6 | H |
| J7 | G, I |
| J8 | K, C |
| J9 | I, J |
| J10 | A, M, N |
| J11 | J |
| J12 | G, H, I, N |

Every PRD requirement marked M must appear in at least one journey step or screen. Any gap found during review is added to this document or the PRD.

## 13. Flow acceptance checklist

Before the design and build of a module starts, confirm:

1. Every journey step has a screen and an owner role
2. Every status change has a rule for who, when and why
3. Every irreversible action has a confirmation and an audit entry
4. Each screen has designs for loading, empty, error, no permission and offline states
5. The shortest path for the most common task takes fewer than 6 taps or clicks
6. The engineer journey (J8) has been tested on a real phone with a throttled network
7. Jimcan has walked through J4, J7 and J9 on paper and agreed they match their reality

## 14. Open questions

1. Do managers see all projects or only assigned ones?
2. What spending limit lets a manager approve their own expenses?
3. Should quotes need Admin approval before sending?
4. Who is allowed to change a project's phase, and should some phase changes need approval?
5. Will clients ever need to sign or confirm acceptance inside the system, or is email enough?
6. Which payment details must appear on invoices (bank, mobile money numbers)?
7. Are there standard payment schedules (for example 30, 40, 30 percent) to offer as presets?
8. How should retention be handled in invoices, if used?
9. Does Jimcan want a weekly summary email to the owner?

## 15. Approvals

| Name | Role | Decision | Date |
| --- | --- | --- | --- |
|  | Jimcan owner or director |  |  |
|  | Jimcan project manager |  |  |
|  | Accountant |  |  |
| George | Developer |  |  |
