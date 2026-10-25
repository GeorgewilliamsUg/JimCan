# Jimcan Operations Dashboard

## Front-End Project Plan: UI and UX

**Version:** 0.2 expanded implementation plan  
**Date:** 24 October 2026  
**Author:** George  
**Scope:** Phases 1–18, with Phase 0 treated as the prerequisite foundation phase  
**Companion documents:** PRD, TRD, App Flow, Design Brief, Backend Schema, Implementation Plan

---

## 1. Plan purpose

This plan defines how the Jimcan Operations Dashboard front end will be designed, built, tested, reviewed, integrated with the backend, and prepared for launch.

The product is a responsive Django web application for construction operations. It supports leads, projects, BOQs, rates, quotes, invoices, payments, expenses, suppliers, site uploads, tax, reports, documents, notifications, and administration.

The front end will be built in vertical feature slices. Each slice must be usable, accessible, responsive, connected to the approved data contract, and supported by tests before the next slice begins.

Phase 0 remains the prerequisite for this plan. It establishes the design tokens, style guide, screenshot workflow, demo-data layer, CI checks, shell fixes, and baseline accessibility controls.

## 2. Planning assumptions

- Django templates remain the primary rendering layer.
- HTMX is used for partial updates and progressively enhanced interactions.
- Alpine.js is used only for small client-side behaviours.
- Tailwind tokens remain the source of truth for visual styling.
- Chart.js is retained for the dashboard charts unless a later technical decision replaces it.
- The application is usable on 360–1440 px screens and supports keyboard and screen-reader use.
- UGX is the primary currency, but currency formatting is implemented as a reusable rule rather than hard-coded into individual screens.
- The backend exposes stable data functions or view contracts matching the shapes agreed in the companion documents.
- The project has at least one Admin, Manager, Accountant, Engineer, and field-user test account.
- Estimates are working days and exclude major backend-model changes, procurement delays, and unresolved business decisions.

## 3. Delivery principles

1. Build components before repeating patterns in screens.
2. Use one data function per screen or feature boundary.
3. Treat loading, empty, error, permission, offline, and long-content states as part of the feature.
4. Do not show controls that do not work.
5. Validate important workflows with representative users before calling a phase complete.
6. Keep all decisions, assumptions, and unresolved questions in a dated decision log.
7. Prefer small vertical releases over waiting for the whole dashboard to be finished.
8. Protect financial, tax, project, and customer data through both interface and server-side permissions.

## 4. Release structure

### Release A: Foundation and operating core

Phases 0–4:

- Stable shell and feedback patterns
- Sign in and onboarding
- Shared UI kit
- Dashboard

### Release B: Commercial workflow

Phases 5–11:

- Leads and clients
- Projects
- Rate library
- BOQ builder
- Quotes
- Invoices and payments
- Expenses and suppliers

### Release C: Field, reporting, and documents

Phases 12–14:

- Site uploads and offline support
- Tax and reports
- Documents and print layouts

### Release D: Administration and productivity

Phases 15–16:

- Notifications, settings, and administration
- Global search and productivity features

### Release E: Launch readiness

Phases 17–18:

- Hardening and quality assurance
- Handover and launch preparation

## 5. Phase summary

| Phase | Name                               |   Estimate | Primary outcome                                          |
| ----- | ---------------------------------- | ---------: | -------------------------------------------------------- |
| 1     | App shell and feedback patterns    |   4–6 days | Reliable application frame and common feedback behaviour |
| 2     | Sign in and onboarding             |   3–4 days | Secure entry and first-run setup                         |
| 3     | Shared UI kit                      |   6–9 days | Reusable, tested forms and data patterns                 |
| 4     | Dashboard                          |   3–4 days | Role-specific operational overview                       |
| 5     | Leads, clients, and public enquiry |   5–7 days | Lead capture and client management workflow              |
| 6     | Projects                           |   5–6 days | Project setup, detail, and activity workflow             |
| 7     | Rate library                       |   3–4 days | Reusable rates, units, and pricing data                  |
| 8     | BOQ builder                        | 15–22 days | Core quantity and cost planning workflow                 |
| 9     | Quotes                             |   4–6 days | Quote preparation, approval, and revision workflow       |
| 10    | Invoices and payments              |   6–8 days | Issuing, tracking, and recording payments                |
| 11    | Expenses and suppliers             |   5–7 days | Expense capture, approval, and supplier management       |
| 12    | Site upload and offline PWA        |   6–9 days | Field uploads with resilient sync behaviour              |
| 13    | Tax and reports                    |  8–12 days | Tax-period workflows and management reporting            |
| 14    | Documents and print                |   5–7 days | Reliable PDF, print, and document layouts                |
| 15    | Notifications, settings, and admin |   6–8 days | Administration, users, preferences, and alerts           |
| 16    | Search and productivity            |   3–5 days | Permission-aware global search and shortcuts             |
| 17    | Hardening and quality assurance    |  6–10 days | Release candidate with defects and risks controlled      |
| 18    | Handover and launch preparation    |   3–4 days | Production-ready release and operational handover        |

**Phase 1–18 estimate:** approximately 96–138 working days.  
**Including Phase 0:** approximately 99–143 working days.

## 6. Common phase gate

Every phase must pass the following gate before it is closed:

### Entry criteria

- The previous phase has passed its exit criteria.
- The feature scope and screen list are agreed.
- Required backend data shapes are documented.
- Open decisions that could change the design are resolved or explicitly accepted as risks.
- Representative sample data exists, including awkward cases.

### Build criteria

- The feature uses shared tokens and components.
- Every interactive control has a working destination or action.
- The feature has loading, empty, error, permission, and success states where applicable.
- The feature works as a normal page load as well as through HTMX where HTMX is used.
- Form behaviour includes validation, duplicate-submit prevention, CSRF/session handling, and unsaved-change handling where applicable.

### Review criteria

- Responsive checks at 360, 390, 768, 1024, and 1440 px.
- Keyboard path and visible focus reviewed.
- Screen-reader labels and announcements reviewed.
- Contrast and colour-use checks pass.
- Automated rendering, permission, and interaction tests pass.
- Screenshots at 390 and 1440 px are captured.
- At least one representative user completes the agreed task set.
- Findings are fixed or recorded with an owner and accepted due date.

### Exit criteria

- No blocker or critical defect remains.
- All accepted deviations are recorded in the decision or risk log.
- The style guide is updated for any new pattern.
- The feature's data contract and test fixtures are documented.
- The product owner accepts the feature against its acceptance criteria.

---

# 7. Detailed phase plans

## Phase 1: App shell and feedback patterns

**Estimate:** 4–6 days  
**Depends on:** Phase 0  
**Primary users:** All authenticated users  
**Screens:** Shell, mobile drawer, error pages, confirmation dialog, session timeout warning

### Goal

Create a reliable application frame that behaves consistently across every later feature. Users should always know where they are, what happened, what is loading, and what action is available next.

### Build activities

1. Implement role-aware navigation and separate administrative navigation from operational navigation.
2. Match active navigation by section and URL prefix rather than exact page name.
3. Build the responsive mobile drawer with focus trapping, Escape handling, backdrop handling, scroll locking, and focus restoration.
4. Build the page-header component with title, subtitle, breadcrumbs, primary action, and responsive secondary-action menu.
5. Build the user menu with profile, role, password change, and POST sign-out.
6. Remove or hide the non-functional search field and notification control until their phases are complete.
7. Convert Django messages into accessible toasts with success, warning, and error behaviour.
8. Add HTMX response-header support for server-triggered toasts.
9. Build native-dialog confirmation and destructive-action patterns.
10. Build branded 403, 404, 500, CSRF/session, and offline/network failure states.
11. Add loading progress, skeletons, button spinners, and disabled-submit behaviour.
12. Add session timeout and unsaved-change warnings.
13. Add private-page cache headers and verify that sign-out does not expose stale private pages through browser history.

### Backend and data requirements

- Role and permission names must be available to the template context.
- The server must return consistent error status codes and HTMX response headers.
- Session-expiry and CSRF failures must have identifiable responses.
- Navigation items must have a single permission source rather than separate template rules.

### Acceptance criteria

- A user sees only permitted menu items.
- Detail and edit pages highlight the correct parent section.
- The mobile drawer is fully keyboard and screen-reader usable.
- Toasts do not cover sticky mobile action bars.
- Every error page provides a clear next action.
- A failed HTMX request restores the control and explains what happened.
- Session expiry and CSRF errors do not silently discard work.

### Risks and mitigations

- **Risk:** Permission rules become duplicated in templates. **Mitigation:** centralise navigation visibility and test it per role.
- **Risk:** Overlays conflict with one another. **Mitigation:** define one overlay manager and test focus restoration.

## Phase 2: Sign in and onboarding

**Estimate:** 3–4 days  
**Depends on:** Phases 0–1  
**Primary users:** All users; Admin during setup  
**Screens:** S-01 Sign in, S-02 Password reset/change, S-95 Setup checklist

### Goal

Provide a secure, understandable entry flow and guide a new Admin through the minimum setup needed to operate the system.

### Build activities

1. Build sign-in with correct autocomplete, password visibility, caps-lock feedback, generic authentication errors, inactivity messaging, and return-to-requested-page behaviour.
2. Build password-reset request, email-sent, new-password, success, expired-link, and used-link states.
3. Show password requirements before entry and validate them without blocking paste or password-manager use.
4. Build change-password and forced-change flows.
5. Create responsive HTML and plain-text invitation and password-reset email templates.
6. Build the Admin setup checklist for company details, logo, tax data, numbering, rates, categories, units, templates, and first users.
7. Add disabled-account and missing-role states.
8. Prepare optional two-factor screens as a decision-controlled extension.

### Backend and data requirements

- Authentication, reset-token, expiry, and forced-password-change contracts.
- Setup completion status by checklist item.
- Account-state and role-assignment status.
- Email-template preview data.

### Acceptance criteria

- The flow does not reveal whether an account exists.
- Password managers work without unusual field names or blocked paste.
- The sign-in button remains usable above the mobile keyboard.
- Reset links clearly state their expiry time.
- The setup checklist is non-blocking except where a business rule explicitly requires setup.
- A user with no role receives an actionable explanation.

### Risks and mitigations

- **Risk:** Security messaging exposes account existence. **Mitigation:** use identical request responses and generic wording.
- **Risk:** Setup checklist becomes an unbounded settings project. **Mitigation:** define the minimum launch checklist and defer optional configuration.

## Phase 3: Shared UI kit and data patterns

**Estimate:** 6–9 days  
**Depends on:** Phases 0–1  
**Primary users:** All users; developers and QA  
**Screens:** Style guide and component sample pages

### Goal

Build the reusable interaction and data-display system so later features can be assembled consistently and quickly.

### Build activities

1. Build field wrappers, labels, hints, errors, required states, and screen-reader relationships.
2. Build text, textarea, select, checkbox, radio, switch, date, search, money, quantity, and percentage inputs.
3. Build file/photo input with preview, size limits, accepted types, and phone camera hints.
4. Build accessible HTMX comboboxes with keyboard navigation, recent results, and create-new behaviour.
5. Build responsive data tables with sorting, row actions, totals, links, captions, and mobile card views.
6. Build pagination, filter bars, URL-persisted state, removable filter chips, and announced result counts.
7. Build URL-driven tabs with mobile scrolling and correct keyboard behaviour.
8. Build dialogs, drawers, dropdowns, tooltips, hint patterns, chips, badges, detail lists, timelines, avatars, breadcrumbs, and banners.
9. Build button variants with loading, disabled, and disabled-reason states.
10. Build empty states and sticky mobile action bars with safe-area support.
11. Assemble full form and full-list sample pages in the style guide.
12. Add rendering tests for every component state.

### Backend and data requirements

- Shared formatting helpers for money, quantity, dates, percentages, file sizes, and status labels.
- Consistent error payloads for field and form-level errors.
- Pagination and filter parameter conventions.

### Acceptance criteria

- Every component appears in the style guide with default, hover, focus, disabled, loading, error, empty, and long-content states where relevant.
- All fields have usable labels and error associations.
- Native controls remain available on mobile where they provide better usability.
- Table and form patterns pass keyboard and screen-reader checks.
- Component tests prevent accidental style or behaviour regressions.

## Phase 4: Dashboard

**Estimate:** 3–4 days  
**Depends on:** Phases 0–3  
**Primary users:** Admin, Manager, Accountant, Engineer  
**Screen:** S-10

### Goal

Give each role a calm, fast overview of current performance and the work that needs attention.

### Build activities

1. Define KPI meanings, calculation windows, permissions, and empty-state behaviour with the product owner.
2. Build role-specific dashboard variants.
3. Build responsive KPI cards linked to filtered source lists.
4. Build the attention strip for overdue invoices, follow-ups, pending expenses, expiring quotes, and tax deadlines.
5. Build the cash chart with token-based colours, labelled units, full-value tooltips, a table view, and empty states.
6. Build project-phase progress and recent-expense sections.
7. Add period selector and URL-persisted HTMX updates.
8. Add freshness timestamp and refresh action.
9. Test large, negative, zero, missing, and permission-limited values.

### Acceptance criteria

- A 390 px first view shows the KPIs and the beginning of the chart without horizontal scrolling.
- Each KPI has a written definition and an appropriate destination.
- A manager without projects sees a useful empty state.
- Every monetary value includes currency context.
- The chart does not delay meaningful paint or cause layout shift.
- The accessible table view contains the same information as the visual chart.

## Phase 5: Leads, clients, and public enquiry form

**Estimate:** 5–7 days  
**Depends on:** Phases 1–4 and approved client/lead schema  
**Primary users:** Admin, Manager, sales or office staff, public enquirer  
**Screens:** S-20 to S-25

### Goal

Capture new enquiries, convert qualified leads into clients and projects, and make follow-up ownership visible.

### Build activities

1. Build lead list with search, status, owner, source, date, and follow-up filters.
2. Build lead detail with contact information, enquiry summary, timeline, notes, next action, and owner.
3. Build create/edit lead form with duplicate warnings and validation.
4. Build client list, client detail, contact history, and linked projects.
5. Build lead-to-client and lead-to-project conversion flows.
6. Build public enquiry form with confirmation, validation, privacy consent, spam protection, and failure handling.
7. Add follow-up status, due date, reminders, and overdue indicators.
8. Define archive and deletion rules for personal information.

### Data and integration requirements

- Lead source, status, owner, consent, and next-action fields.
- Duplicate matching rules for email, phone, and client name.
- Public-form rate limiting and notification destination.
- Permission rules for contact data.

### Acceptance criteria

- A new enquiry can be submitted without exposing internal fields.
- Duplicate contacts are flagged before a second record is created.
- A lead can be assigned, followed up, converted, archived, and found again.
- Personal data is not visible to roles without permission.
- Public submission failure does not create a misleading success message.

## Phase 6: Projects

**Estimate:** 5–6 days  
**Depends on:** Phases 3–5 and project schema  
**Primary users:** Admin, Manager, Engineer, Accountant  
**Screens:** S-30, S-31

### Goal

Create a dependable project workspace that connects client, scope, team, phases, commercial records, and activity.

### Build activities

1. Build project list with status, client, manager, dates, value, and progress filters.
2. Build project creation and editing with client selection, project code, address, dates, status, budget, and team.
3. Build project detail with summary, phase progress, linked BOQ, quotes, invoices, expenses, documents, and activity timeline.
4. Add project status transitions and confirmation for archive or closure.
5. Add permission-aware project membership.
6. Add empty and incomplete-project states.
7. Define project deletion, archive, and reopen behaviour.

### Acceptance criteria

- Project detail highlights the Projects navigation item.
- A project can be created from a lead or independently.
- Linked commercial records are clearly separated from unavailable or empty areas.
- Closed and archived projects cannot be edited without an explicit action.
- Activity history identifies who made important changes.

## Phase 7: Rate library

**Estimate:** 3–4 days  
**Depends on:** Phase 3 and approved rate/unit schema  
**Primary users:** Admin, Manager, estimator, Engineer

### Goal

Provide a reusable and controlled source of rates, units, categories, and pricing information for BOQs and quotes.

### Build activities

1. Build rate list with category, unit, active status, and search/filter controls.
2. Build create/edit rate form with description, unit, labour, materials, overhead, and total rate rules.
3. Add versioning or effective-date behaviour for changed rates.
4. Add archive/deactivate behaviour without breaking historical BOQs.
5. Add import/export if approved by the product owner.
6. Add usage information showing where a rate is used.
7. Add duplicate-name and duplicate-code handling.

### Acceptance criteria

- Historical documents retain the rate values used at the time.
- Inactive rates cannot be selected for new work unless explicitly allowed.
- Rate changes show who changed them and when.
- Unit and currency formatting is consistent across library, BOQ, and quote screens.

## Phase 8: BOQ builder

**Estimate:** 15–22 days  
**Depends on:** Phases 3, 6, and 7; approved calculation rules  
**Primary users:** Manager, estimator, Engineer, Accountant  
**Screens:** S-51, S-52

### Goal

Deliver the central quantity and cost-planning workflow, with reliable calculations, manageable large tables, and clear document status.

### Build activities

1. Build BOQ list by project with status, version, total, owner, and updated date.
2. Build BOQ creation flow from a project or template.
3. Build line-item table with sections, items, descriptions, units, quantities, rates, adjustments, subtotals, and totals.
4. Add rate-library selection and create-new-rate flow.
5. Add add, edit, duplicate, delete, reorder, bulk-edit, and section-management actions.
6. Define calculation rules for quantity, unit rate, waste, markup, tax, rounding, and total presentation.
7. Build draft, submitted, approved, locked, rejected, and revised states.
8. Add autosave or explicit-save behaviour with unsaved-change protection.
9. Add validation for missing units, invalid quantities, negative values, and incomplete rows.
10. Add version history and comparison if required by the PRD.
11. Add large-table performance behaviour, sticky totals, mobile card or focused-row mode, and keyboard shortcuts where useful.
12. Add concurrency and stale-data handling.
13. Add print/PDF entry points after Phase 14 integration is available.

### Data and integration requirements

- Authoritative calculation service; the browser must not be the only source of truth.
- Draft and version identifiers.
- Locking and approval permissions.
- Server-side validation matching the client-side rules.
- Clear recalculation response and error contract.

### Acceptance criteria

- The same input always produces the same server-approved total.
- A locked or issued BOQ cannot be silently changed.
- Users can recover from a failed save without losing entered data.
- Large BOQs remain usable on desktop and provide an intentional mobile experience.
- Changes to rates or tax rules do not rewrite historical approved totals.
- A user understands whether the displayed total is draft, approved, or locked.

### Risk gate

Run a BOQ usability and calculation review before beginning Quotes. This is the highest-risk product phase and should receive a separate product-owner sign-off.

## Phase 9: Quotes

**Estimate:** 4–6 days  
**Depends on:** Phases 3, 6, 8, and approved document requirements  
**Primary users:** Manager, estimator, client-facing staff

### Goal

Turn approved BOQ content into a clear, versioned, reviewable quote.

### Build activities

1. Build quote list with project, client, status, total, expiry, and owner.
2. Build quote creation from a BOQ or template.
3. Build quote editing with exclusions, assumptions, validity period, notes, terms, and tax presentation.
4. Build draft, sent, viewed, accepted, rejected, expired, withdrawn, and revised states.
5. Add approval and issue confirmation.
6. Add revision/version history and relationship to the source BOQ.
7. Add client-facing review or download path if included in scope.
8. Add clear warnings when the underlying BOQ changes after quote preparation.

### Acceptance criteria

- A quote identifies its source BOQ and version.
- Issued quotes cannot be silently edited.
- Expiry and acceptance states are visible and understandable.
- The quote total, tax, exclusions, and validity period are clear before issue.
- Revisions preserve historical versions.

## Phase 10: Invoices and payments

**Estimate:** 6–8 days  
**Depends on:** Phases 3, 6, 8, 9, and approved numbering/tax rules  
**Primary users:** Admin, Accountant, Manager

### Goal

Support accurate invoice creation, issuing, tracking, and payment recording without ambiguity about document status.

### Build activities

1. Build invoice list with status, client, project, due date, total, amount paid, and balance.
2. Build invoice creation from a quote, project, milestone, or manual entry as approved.
3. Build invoice form with line items, tax, discounts, notes, terms, due date, and numbering.
4. Build draft, issued, partially paid, paid, overdue, voided, and credited states.
5. Build payment recording for full and partial payments with date, method, reference, and notes.
6. Build payment history and balance calculation.
7. Add overdue and due-soon indicators.
8. Add issue/void confirmation and permissions.
9. Add receipt/download/print entry points.
10. Add invoice detail activity history.
11. Define rounding and currency rules for invoice totals and payments.

### Acceptance criteria

- Invoice numbering is unique and follows the approved sequence.
- Issued invoices cannot be edited without a controlled adjustment or void flow.
- Partial payments calculate the remaining balance correctly.
- Overdue status is date-aware and tested around boundary dates.
- Every financial action records actor, timestamp, and reason where required.
- Tax and totals agree with the authoritative backend calculation.

## Phase 11: Expenses and suppliers

**Estimate:** 5–7 days  
**Depends on:** Phases 3, 6, and approved expense/approval schema  
**Primary users:** All operational users; Accountant and Manager for approval  
**Screens:** S-70 to S-75

### Goal

Capture project and company expenses efficiently, link them to suppliers and projects, and provide a controlled approval workflow.

### Build activities

1. Build expense list with date, supplier, project, category, amount, status, and owner filters.
2. Build expense creation with supplier, project, category, tax, amount, date, payment method, notes, and receipt.
3. Build camera/file receipt upload with preview, file validation, retry, and removal.
4. Build supplier list, create/edit form, detail, and linked expense history.
5. Build submitted, approved, rejected, reimbursed, and locked states.
6. Add rejection reason and resubmission flow.
7. Add duplicate-expense warning based on configurable fields.
8. Add approval queue and bulk review where appropriate.
9. Add project and period locking behaviour.

### Acceptance criteria

- Users know whether an expense is saved, submitted, approved, or rejected.
- Rejected expenses explain what must be corrected.
- Receipt uploads show progress and recover from network failure.
- Approved or locked expenses cannot be altered without a controlled process.
- Supplier and project permissions are enforced.

## Phase 12: Site upload and offline PWA

**Estimate:** 6–9 days  
**Depends on:** Phases 3, 6, 11, and approved service-worker strategy  
**Primary users:** Engineers, site staff, Managers  
**Screens:** S-40, S-41

### Goal

Allow field users to capture and upload site information despite unreliable connectivity, while making sync status and conflicts understandable.

### Build activities

1. Define offline-supported actions and explicitly exclude unsupported actions.
2. Build photo/file capture with compression, metadata, preview, and size limits.
3. Build upload queue showing pending, uploading, uploaded, failed, and conflicted items.
4. Add retry and remove-from-queue behaviour.
5. Add offline banner and last-synced timestamp.
6. Build sync-on-reconnect behaviour with progress and failure reporting.
7. Define conflict handling for edits made on multiple devices.
8. Add storage quota and cleanup messaging.
9. Test interrupted uploads, browser termination, duplicate submissions, and expired sessions.
10. Add installability and safe update behaviour if PWA installation is in scope.

### Acceptance criteria

- Users can tell what is stored locally and what has reached the server.
- Failed uploads are recoverable and do not create duplicate records.
- Offline actions are limited to the documented supported set.
- Conflicts are surfaced for a human decision rather than silently overwritten.
- Sensitive local data is cleared or protected according to the security decision.

## Phase 13: Tax and reports

**Estimate:** 8–12 days  
**Depends on:** Phases 6, 8, 9, 10, 11, and approved tax rules  
**Primary users:** Admin, Accountant, Manager  
**Screens:** S-80 to S-86

### Goal

Provide trustworthy tax-period workflows and management reports using consistent definitions and authoritative calculations.

### Build activities

1. Define the report catalogue, audience, purpose, filters, and source data for every report.
2. Build tax configuration and rate display using the approved setup model.
3. Build tax-period list and period detail.
4. Build open, reviewed, filed, and locked period states.
5. Build tax summary and transaction-detail views.
6. Build reports for sales, invoices, expenses, payments, project profitability, and outstanding balances as approved.
7. Add date-range, project, client, supplier, status, and tax filters.
8. Add table and chart views where they improve comprehension.
9. Add CSV/PDF export entry points with permission checks.
10. Add report definitions and “last updated” information.
11. Test rounding, date boundaries, voids, credits, partial payments, and locked periods.

### Acceptance criteria

- Every report has a documented definition and source.
- Report totals reconcile to the underlying records.
- Locked periods cannot be changed through ordinary screens.
- Exported data respects the same filters and permissions as the screen.
- Users can distinguish estimated, draft, and final figures.

## Phase 14: Documents and print layouts

**Estimate:** 5–7 days  
**Depends on:** Phases 8–13 and approved brand/document templates  
**Primary users:** Admin, Manager, Accountant, clients

### Goal

Produce consistent, readable, professional documents for quotes, invoices, receipts, reports, BOQs, and project records.

### Build activities

1. Define supported document types and output formats.
2. Build reusable document header, footer, branding, contact, tax, and numbering blocks.
3. Build quote, invoice, receipt, BOQ, report, and expense-summary layouts.
4. Define page sizes, margins, page breaks, table overflow, repeated headers, and long-name behaviour.
5. Add print stylesheet and PDF generation entry points.
6. Add preview before download or print.
7. Add stable file naming and document metadata.
8. Test missing logos, long descriptions, large tables, multiple pages, currency values, and tax summaries.
9. Add document permission and access rules.

### Acceptance criteria

- Documents are readable at normal print size and on screen.
- Tables do not clip, overlap, or lose totals across page breaks.
- Issued documents preserve their original version.
- Downloads use predictable names and correct file types.
- Print and PDF content matches the screen's approved data.

## Phase 15: Notifications, settings, and administration

**Estimate:** 6–8 days  
**Depends on:** Phases 1–14 and approved administration model  
**Primary users:** Admin, Managers, all users for preferences  
**Screens:** S-90 to S-96

### Goal

Give authorised users control over company settings, users, roles, notifications, numbering, templates, and audit information.

### Build activities

1. Build user list, invite, edit, deactivate, reactivate, and role-assignment flows.
2. Build user detail with status, role, last activity, and access summary.
3. Build company profile, logo, contact, currency, numbering, tax, categories, units, and template settings.
4. Build notification centre with unread/read states, grouping, timestamps, and destination links.
5. Build notification preferences by user and event type.
6. Build audit-log list and detail with filters and permission controls.
7. Add confirmation and reason requirements for sensitive changes.
8. Add settings validation and warnings for changes that affect future documents only versus existing documents.
9. Add admin empty, permission, and setup-incomplete states.

### Acceptance criteria

- Only authorised Admin users can reach administrative screens.
- Deactivation does not delete historical ownership or audit information.
- Notifications link to the relevant record and respect permissions.
- Settings clearly state whether changes affect existing or future records.
- Sensitive actions record actor, timestamp, old value, new value, and reason where required.

## Phase 16: Search and productivity

**Estimate:** 3–5 days  
**Depends on:** Phases 5–15 and approved search scope  
**Primary users:** All authenticated users

### Goal

Help users reach permitted records quickly without replacing the structure of the application.

### Build activities

1. Define searchable entities, fields, ranking, result limits, and permission rules.
2. Build global search entry point and responsive search experience.
3. Build keyboard shortcut and focus behaviour.
4. Group results by record type with clear labels and metadata.
5. Add recent searches or recent records only if they provide clear value.
6. Build no-results, partial-match, loading, error, and permission-filtered states.
7. Preserve search in the URL where the result view is shareable.
8. Add direct actions only when their permission and destination are unambiguous.

### Acceptance criteria

- Search never reveals records a user cannot access.
- Results identify record type, status, owner, and relevant date or project context.
- Search works with keyboard and on small screens.
- Empty results explain how to broaden the search.
- Search does not become a dead control or show unsupported entity types.

## Phase 17: Hardening and quality assurance

**Estimate:** 6–10 days  
**Depends on:** Phases 1–16  
**Primary users:** All users; QA and support teams

### Goal

Turn the completed feature set into a stable release candidate with known performance, accessibility, security, and browser behaviour.

### Workstreams

#### Functional QA

- Execute the end-to-end workflows from lead through project, BOQ, quote, invoice, payment, expense, report, and document.
- Test draft, approved, locked, rejected, archived, voided, and reopened states.
- Test normal page loads and enhanced HTMX paths.
- Test browser back, refresh, direct URLs, expired sessions, and duplicate submissions.

#### Responsive and browser QA

- Test the agreed browser matrix on Android, iOS, desktop Chromium, Firefox, and Safari where supported.
- Test 360, 390, 768, 1024, and 1440 px widths.
- Test keyboard-only navigation and touch interactions.
- Test slow network, offline mode, rotation, zoom, and mobile keyboard behaviour.

#### Accessibility QA

- Run automated checks for structure, labels, contrast, landmarks, names, roles, and values.
- Perform manual keyboard and screen-reader checks on representative workflows.
- Confirm focus after navigation, modal close, HTMX swaps, validation errors, and failed saves.
- Confirm colour is not the only state indicator.

#### Performance QA

- Record page weight and key timing budgets.
- Check layout shift, chart loading, font loading, table performance, and image sizes.
- Test representative large datasets rather than only sample-sized data.

#### Security and privacy QA

- Test object-level permissions for every record type.
- Check that direct URLs cannot bypass role restrictions.
- Test file access, session handling, CSRF, password reset, rate limits, and public enquiry protection.
- Verify that private content is not cached or exposed through exports and documents.

#### Visual regression

- Capture approved screenshots for all key screens at 390 and 1440 px.
- Review intentional differences and reject accidental layout or token changes.

### Exit criteria

- No open blocker or critical defect.
- High-severity defects have an accepted fix date or release decision.
- Browser, accessibility, security, and performance results are recorded.
- Production configuration has been tested in a staging-like environment.
- The release candidate is tagged and reproducible from a clean checkout.

## Phase 18: Handover and launch preparation

**Estimate:** 3–4 days  
**Depends on:** Phase 17 and production infrastructure readiness  
**Primary users:** Admin, support team, developers, project owner

### Goal

Prepare the application, users, documentation, and support process for a controlled production launch.

### Build activities

1. Create a production deployment checklist.
2. Verify environment variables, secrets, static files, media storage, email, domain, HTTPS, and cache behaviour.
3. Prepare migration and seed-data procedures.
4. Verify backups, restore procedure, and rollback plan.
5. Create a short Admin guide covering setup, users, rates, tax, templates, approvals, and reports.
6. Create user guides for common Manager, Accountant, Engineer, and field workflows.
7. Prepare a known-issues and limitations list.
8. Prepare support escalation and incident-response instructions.
9. Train the initial users using representative data and tasks.
10. Run a go/no-go review with product, technical, and operational owners.
11. Launch using a staged rollout if risk or user count justifies it.
12. Schedule a post-launch review after the first meaningful usage period.

### Launch acceptance criteria

- Production deployment succeeds from documented steps.
- A backup can be restored in a test environment.
- Admin and representative users can complete their core workflows.
- Monitoring and error reporting are active.
- Support contacts and escalation ownership are clear.
- Rollback criteria and decision-maker are documented.
- Product owner signs the launch decision.

---

# 8. Cross-project requirements

## 8.1 Accessibility

The application must meet the accessibility targets defined in the Design Brief and universal checklist. In addition:

- Use semantic HTML before ARIA.
- Keep keyboard focus visible and logical.
- Announce dynamic updates without excessive interruption.
- Provide a table alternative for charts.
- Keep error messages specific and actionable.
- Do not rely on colour, hover, or drag-only interactions.
- Test with at least one desktop and one mobile screen reader.

## 8.2 Content and microcopy

Create a shared copy inventory for:

- Button labels
- Empty states
- Validation errors
- Permission messages
- Confirmation messages
- Toasts
- Offline and sync states
- Locked-record explanations
- Tax and financial terminology

Copy must state what happened, why it happened where useful, and what the user can do next.

## 8.3 Data and formatting

Define centrally:

- UGX and any additional currency formats
- Decimal and rounding rules
- Date and time-zone rules
- Negative and zero-value presentation
- Large-number abbreviation rules
- Tax display rules
- File-size and upload limits
- Status names and colour semantics

## 8.4 Analytics and feedback

If analytics are approved, measure only useful product events, such as:

- Sign-in success/failure
- Setup completion
- Lead conversion
- BOQ save or failure
- Quote issue and acceptance
- Invoice payment recording
- Upload failure and sync conflict
- Report export
- Search with no results

Do not collect sensitive financial or personal content in analytics events.

## 8.5 Change control

Any change that affects scope, estimates, calculations, permissions, data contracts, or release dates must be recorded with:

- Date
- Decision owner
- Description of change
- Reason
- Affected phases
- Estimate impact
- Risk impact
- Approval status

# 9. Required project registers

Maintain these files alongside the implementation:

- `docs/ui-decisions.md`
- `docs/open-questions.md`
- `docs/risks-and-dependencies.md`
- `docs/role-permissions.md`
- `docs/data-contracts.md`
- `docs/browser-and-device-matrix.md`
- `docs/test-plan.md`
- `docs/release-checklist.md`
- `docs/known-issues.md`

# 10. Immediate next actions

1. Confirm the MVP release boundary and whether Phase 16 is excluded from MVP.
2. Approve the role-permission matrix.
3. Confirm BOQ calculation, locking, versioning, and approval rules.
4. Confirm tax, invoice numbering, payment, and document requirements.
5. Assign an owner and target date to every `[Open]` and `[Decision]` item.
6. Write the missing backend data contracts for Phases 5–13.
7. Select the actual browser, phone, and assistive-technology test matrix.
8. Agree on the staging environment and production deployment approach.
9. Begin Phase 1 only after Phase 0 exit criteria are recorded as passed.

# 11. Final definition of project completion

The front end is complete for launch only when:

- All approved MVP workflows are implemented end to end.
- Every screen passes the universal checklist or has an accepted documented exception.
- Role permissions are tested server-side and in the interface.
- Financial and tax calculations reconcile with the backend.
- Offline and upload behaviour is understood and recoverable.
- Documents and reports are approved on realistic data.
- Accessibility, responsive, browser, security, and performance checks are recorded.
- Production deployment, backup, rollback, monitoring, support, and training are ready.
- The product owner signs the release decision.
