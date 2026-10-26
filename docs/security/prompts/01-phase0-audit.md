# Phase 0: Read-Only Audit

Read `CLAUDE.md` first. **In this phase you change no application code.** You only read, run read-only commands, and write documents under `docs/security/`.

## Goal

Learn exactly what exists, mark everything you cannot determine as **UNKNOWN** (never guess), and prepare the questions the human must answer at Gate 1.

## Tasks

Write findings to `docs/security/phase0-audit.md`, covering every item:

1. **Versions.** Python, Django and Tailwind, exact. Is the Django release line still receiving security fixes? Check it against the project's own pinned version and any offline information available. If you cannot verify support status, mark UNKNOWN. If Django or Python is clearly out of support, flag it as the top finding and stop after the audit.
2. **Database.** The engine and how it is configured. Whether the user table has ever been migrated (`showmigrations`, migration files, any existing `AUTH_USER_MODEL`). If the project already uses `auth.User` with applied migrations or data, record that it must NOT be swapped.
3. **Settings and secrets.** How settings are organised. How `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, database and email credentials are set. Whether any secret is in the repo or its git history (search history with `git log -p -S "SECRET_KEY"` and for common credential patterns). Whether `.env`, `*.sqlite3`, media and backup files are ignored by git. List tracked files that should not be tracked.
4. **Middleware.** The current `MIDDLEWARE` list in order, and the `AUTHENTICATION_BACKENDS`.
5. **URLs.** Every URL pattern, its view, and its current protection (none, login required, mixin, permission check). Include parameterised routes. Present as a table.
6. **Models.** Every model, proposed as **financial** (invoices, expenses, BOQ rates and lines, payments, tax records, budgets), **operational** (projects, leads, site uploads), **identity**, or **other**. Note any field that looks like an EFRIS fiscal number, QR code, or submission status.
7. **Data exposure.** Views, templates, exports or JSON responses that return data without checking the requester's rights, and any template that hides in the browser what the server still sends.
8. **Dangerous code patterns.** Search for and list: `|safe`, `mark_safe`, `.raw(`, `.extra(`, `RawSQL`, `cursor.execute` with string formatting, `eval(`, `exec(`, `pickle`, `yaml.load`, `subprocess` with `shell=True`, `os.system`, `csrf_exempt`, `innerHTML` in JavaScript, and any `.delete()` or bulk update on a financial model.
9. **Uploads and downloads.** Where files are stored, whether they can be fetched by URL without logging in, how names and types are validated, whether images keep GPS metadata, and which dependencies handle them.
10. **Deployment.** Look for WSGI or Passenger files, `.htaccess`, cPanel hints. Whether the app can see the real client IP, and whether a proxy sets `X-Forwarded-Proto` or `X-Forwarded-For`. If not provable from the repo, mark UNKNOWN and say exactly what the human must check on the server.
11. **Exposure of sensitive files.** From the repo layout, could `.git`, `.env`, the database file, `manage.py` or `requirements.txt` end up inside a web-served directory? Mark UNKNOWN if not provable.
12. **Email.** Is it configured? TLS? Which sending domain? Are SPF and DKIM mentioned anywhere?
13. **Admin.** Is `django.contrib.admin` used for day-to-day data entry, or only a leftover?
14. **Existing audit log**, if any: model, page, what it records.
15. **Public pages.** Which pages (if any) are intentionally public.
16. **Test setup.** Does a test suite exist? Does it pass right now? Record the baseline result without changing anything.

## Deliverables

1. `docs/security/phase0-audit.md` (the findings above).
2. `docs/security/permission-matrix.md`: the proposed matrix below, adjusted to the real models and pages, with every change from the proposal highlighted.
3. `docs/security/decisions-needed.md`: the questions below, plus any others you found, each with your recommended answer.
4. `docs/security/model-classification.md`: every model and its proposed class (financial, operational, identity, other).

### Proposed permission matrix (starting point)

Key: V view, C create, E edit, X void (never a hard delete), blank means no access.

| Area | Owner | Finance | Site staff |
|---|---|---|---|
| Dashboard money-flow figures | V | V | |
| Dashboard (non-financial parts) | V | V | V |
| Projects | V C E X | V | V (assigned projects only, if an assignment concept already exists) |
| Leads | V C E X | V C E | |
| BOQ and rates | V C E X | V C E | V |
| Invoices | V C E X | V C E (drafts only; issued invoices are locked) | |
| Expenses | V C E X | V C E | C and V their own only; no edits after submit |
| Tax and reports (view, export) | V | V | |
| Site uploads | V C E X | V | V C |
| Users and roles | V C E (deactivate) | | |
| Settings | V E | | |
| Audit log | V | | |
| Style guide and shell pages | only when `DEBUG` is true | | |

### Questions that must appear in `decisions-needed.md`

1. Are invoices submitted to URA EFRIS? If yes, issued invoices must be corrected by a reversal document, not a local void.
2. Should Finance see Leads? (The matrix assumes yes.)
3. Is there any concept of staff being assigned to projects? If not, Site staff will see all projects.
4. How many Owner accounts will exist? (Two is strongly recommended.)
5. Is there a terminal on the server (SSH or cPanel Terminal)?
6. Can the hosting send email, and from which domain?
7. Can a staging copy be set up (subdomain, separate database)?
8. Is the Django admin used for daily work?
9. How long must financial records be kept, according to the accountant?
10. Who is the Owner, who is Finance, and who is Site staff? (Names are not stored in the repo; this is only to confirm the roles fit.)

## Done when

The four documents exist and are complete, every UNKNOWN is listed with how to resolve it, and no application file has changed. Print the report from `CLAUDE.md` and **stop**.

## GATE 1

The human reads the documents and creates `docs/security/approvals/gate1.md` with `APPROVED` on the first line and answers to every question below it. Phase 1 may not begin without it.
