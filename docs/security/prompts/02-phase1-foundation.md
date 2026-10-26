# Phase 1: Foundation and Hardening

Read `CLAUDE.md` first. **Prerequisite:** `docs/security/approvals/gate1.md` exists and its first line is `APPROVED`. If not, stop.

## Goal

Make the project safe to build on: correct secret handling, strict production settings, a decided user model, safe headers, a controlled admin, and a way to check the security state with one command.

## Tasks

### 1. Settings and secrets
- All secrets and environment-specific values come from `os.environ`. Do not add `python-dotenv` or `django-environ` unless already present. Document local setup in `docs/security/local-setup.md` using `export` lines, never real values.
- `SECRET_KEY` has no default. If missing, raise `ImproperlyConfigured` so the app refuses to start. If Phase 0 found a key ever committed to git, state that it is compromised and must be rotated.
- `DEBUG` reads an environment value and **defaults to False**. Only an explicit "true" enables it.
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` come from environment variables. No wildcard.
- `USE_TZ = True`, `TIME_ZONE = "Africa/Kampala"`.
- Support `SECRET_KEY_FALLBACKS` from an environment variable, so the key can be rotated without signing everyone out. Verify in the installed Django docs that it exists and what it covers.
- Add missing entries to `.gitignore` (`.env`, `*.sqlite3`, media, backups, key files). Do not delete tracked files. Report any tracked file that should not be tracked.

### 2. Production-only security settings (when `DEBUG` is false)
```python
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 300          # staged: raised later in the runbook
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
```
- **`SECURE_SSL_REDIRECT` and `SECURE_PROXY_SSL_HEADER`:** do not set `SECURE_PROXY_SSL_HEADER` unless Phase 0 proved the host's proxy sets and cleans that header (a wrong value lets attackers fake HTTPS). A missing proxy header with `SECURE_SSL_REDIRECT = True` behind a TLS-terminating proxy causes an endless redirect loop. If the correct setup is unknown, make redirect an environment switch that defaults to on in production, and document exactly what the human must verify on staging first.
- Add a small middleware that sets `Cache-Control: no-store, private` on every response to an authenticated request and on all login, logout, password and two-factor pages, so the back button cannot reveal data after logout. Static files are not affected.
- Run `python manage.py check --deploy` with production-like variables and resolve each warning, or document why not.

### 3. User model
- Follow Phase 0. If the project is fresh, create a minimal `accounts.User(AbstractUser)` with no extra fields before the first migration, set `AUTH_USER_MODEL`, and make email unique and case-insensitive. If `auth.User` already holds data, **keep it**; do not swap.
- Ensure no code path creates a superuser (see Phase 2 test).

### 4. Admin
- `ENABLE_ADMIN` environment switch, default off. When off, the admin URLs are not registered at all. When on, the path comes from `DJANGO_ADMIN_PATH` and must not be `admin/` outside local development. Two-factor protection of the admin is added in Phase 4.

### 5. Logging
- Configure `django.security` and `django.request` loggers to write to a file outside any web-served directory, with rotation. No request bodies, passwords, tokens or cookies. Path comes from an environment variable.

### 6. `security_status` command
Create `python manage.py security_status`. It prints PASS, WARN or FAIL for each item and exits non-zero on any FAIL. In this phase it checks: `DEBUG` off, secret key set, allowed hosts set, cookie flags, HSTS value (WARN while under one year, with the number), admin enabled or not, number of superusers (FAIL if above zero), and the admin path (FAIL if default while the admin is enabled in production). Later phases add checks to it.

### 7. Exposure check script
Write `scripts/exposure_check.sh` using only `curl`. Given a base URL it requests, with GET, these paths: `/.git/config`, `/.env`, `/db.sqlite3`, `/manage.py`, `/requirements.txt`, `/media/`, `/static/../settings.py`, `/admin/`, `/robots.txt`. It prints each status code and flags anything other than 403 or 404 (except `robots.txt`). It reads only; it sends no credentials. The human runs it against staging and production.

## Tests

- With `DEBUG` false and required variables set, the production settings above have the expected values.
- With `SECRET_KEY` missing, the app refuses to start.
- The no-store header is present on an authenticated response and on the login page, and absent on static files.
- When `ENABLE_ADMIN` is off, the admin URL returns 404.
- `security_status` returns a non-zero exit code when a superuser exists.

## Done when

All tests pass, `check --deploy` is clean or each remaining warning is explained, and the report is printed. Commit.
