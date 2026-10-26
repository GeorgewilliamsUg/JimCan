# Decisions Needed for Gate 1 Approval
**Jimcan Operations Dashboard**
**Date:** 2026-10-26  
**Auditor:** Senior Django Security Engineer (Antigravity)

---

## Instructions for the Human Reviewer

Before Phase 1 can begin, you must create the approval file at:
`docs/security/approvals/gate1.md`

Its **very first line** must be:
```text
APPROVED
```
Below the first line, provide your answers to each of the questions below.

---

## Required Questions & Recommended Answers

### 1. Are invoices submitted to URA EFRIS?
- **Context:** Under Uganda Revenue Authority EFRIS regulations, issued fiscalised tax invoices cannot simply be marked "void" or deleted locally in an internal database; they require an official Credit Note / Reversal document with URA fiscal referencing.
- **Recommended Answer:** **No direct EFRIS API integration for MVP, but follow statutory credit note procedure.** Even without direct API submission, once an invoice is issued to a client, it must be locked. Corrections must be handled by issuing an official Credit Note or reversal record rather than modifying or deleting the original invoice.

### 2. Should Finance see Leads?
- **Context:** The permission matrix currently assumes Finance has view and create/edit rights on Leads to track upcoming pipeline revenue and assist with commercial cost estimation.
- **Recommended Answer:** **Yes (View only).** Finance should be able to view leads for cash-flow forecasting and budget planning, but creating and managing pipeline stages should belong to Owner / Manager roles.

### 3. Is there any concept of staff being assigned to projects?
- **Context:** If staff are assigned to specific construction builds, Site Staff should only see their assigned projects. If no assignment model exists, Site Staff would see all company projects.
- **Recommended Answer:** **Yes, staff are assigned to projects.** The backend schema includes `ProjectMember (project, user, role_on_project)`. Site Staff permissions must be strictly scoped to projects where they are assigned as active members.

### 4. How many Owner accounts will exist?
- **Context:** A single Owner account creates a single point of failure (account lockout, lost phone/2FA, illness).
- **Recommended Answer:** **Two Owner accounts.** Exactly two trusted Owner accounts should be provisioned. Both hold administrative group privileges, ensuring redundancy if one loses their 2FA device or backup codes.

### 5. Is there a terminal on the server (SSH or cPanel Terminal)?
- **Context:** Required for running management commands, applying database migrations, and checking server environment variables.
- **Recommended Answer:** **Yes, cPanel Terminal is available.** Confirm that cPanel Terminal (under the "Advanced" menu in cPanel) or SSH access is active on your Namecheap hosting account.

### 6. Can the hosting send email, and from which domain?
- **Context:** Email delivery is required for password setup links, password resets, and critical Owner security alerts.
- **Recommended Answer:** **Yes, via Namecheap cPanel Webmail SMTP.** Sending domain should match the production website (e.g., `notifications@jimcanconstruction.site` or `mail.jimcanconstruction.site`). Confirm that SPF, DKIM, and DMARC records are configured in cPanel Zone Editor to ensure mail delivers reliably to inboxes.

### 7. Can a staging copy be set up (subdomain, separate database)?
- **Context:** Security Rule #2 mandates: *Never touch production or real data.* A separate staging environment is needed to verify Phase 1–8 changes before live deployment.
- **Recommended Answer:** **Yes.** Create a subdomain in cPanel (e.g. `staging.jimcanconstruction.site`) pointing to a separate directory (e.g. `/home/username/jimcan-staging`), with a separate MySQL database (e.g. `username_jimcan_staging`).

### 8. Is the Django admin used for daily work?
- **Context:** If the Django admin is used for day-to-day work, it presents a larger attack surface. Project rules state: *No account is a superuser. Admin is disabled in production by default.*
- **Recommended Answer:** **No.** All day-to-day operations (projects, invoices, rates, expenses) will take place through the custom dashboard. The Django admin should remain disabled in production via an environment toggle (`ENABLE_DJANGO_ADMIN=False`), and if ever enabled, placed on a secret non-default URL (e.g. `/management-portal-secure/`) behind 2FA.

### 9. How long must financial records be kept, according to the accountant?
- **Context:** Sets data retention and archiving requirements for financial invoices, expenses, tax filings, and audit trail logs.
- **Recommended Answer:** **7 years.** Section 15 of the Uganda Tax Procedures Code Act mandates that business and tax records be preserved for a minimum of 7 years. Financial records and audit logs must never be purged or deleted before this period.

### 10. Who is the Owner, who is Finance, and who is Site staff?
- **Context:** To ensure the 3 proposed roles map cleanly to real people without storing actual names in the repository.
- **Recommended Answer:**
  - **Owner:** Managing Director / Principal Partners (full oversight, user provisioning, void approvals, system settings).
  - **Finance:** Company Accountant (invoicing, expense verification, tax filings, rate updates).
  - **Site Staff:** Site Engineers / Field Supervisors (field logs, progress photos, personal expense submissions, assigned build viewing).

---

## Additional Technical Decisions Identified in Phase 0 Audit

### 11. Tailwind CSS Build: Compile to Static CSS vs Play CDN?
- **Context:** Currently, `templates/base.html` loads Tailwind via `https://cdn.tailwindcss.com` (an unversioned development CDN script). This introduces external runtime dependencies, prevents strict Content-Security-Policy (CSP) headers, and fails if the client has no internet access to the CDN.
- **Recommended Answer:** **Compile to static CSS.** Use the standalone Tailwind CLI or pre-build process to output an optimized, self-hosted `static/css/tailwind.min.css` and remove the external script.

### 12. Immediate Git Cleanup for `.env`?
- **Context:** `.env` is currently tracked in git.
- **Recommended Answer:** **Yes, remove `.env` from git tracking in Phase 1.** Run `git rm --cached .env`, add `.env` and `.env.*` (excluding `.env.example`) to `.gitignore`, and ensure production credentials are never committed.

### 13. Fix Port 465 SSL vs TLS Settings?
- **Context:** `.env` specifies port 465 and `EMAIL_USE_SSL=True`, but `settings.py` only inspects `EMAIL_USE_TLS`.
- **Recommended Answer:** **Yes.** Update `settings.py` in Phase 1 to properly support both `EMAIL_USE_SSL` (for port 465) and `EMAIL_USE_TLS` (for port 587) as mutually exclusive configuration options.

### 14. Server-Side Data Filtering for Dashboard Tabs?
- **Context:** Currently, `overview_view` sends all projects, invoices, leads, and rates to the browser in a single HTML response, toggled with Alpine `x-show`. A Site Staff user can inspect the page source to view company finances.
- **Recommended Answer:** **Yes, refactor in Phase 2/5.** The server must enforce role-based queryset filtering before data is rendered into the template context. Data the user is not authorized to see must never be included in the HTTP response.
