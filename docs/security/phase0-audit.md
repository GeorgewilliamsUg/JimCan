# Phase 0: Read-Only Audit Report
**Jimcan Operations Dashboard**
**Date:** 2026-10-26  
**Auditor:** Senior Django Security Engineer (Antigravity)  
**Status:** Complete — No application code modified.

---

## Executive Summary & Top Findings

1. **CRITICAL — Production `.env` Tracked in Git Repository:**  
   The `.env` file is actively tracked by git (`git ls-files .env` returns `.env`) and `.env` is omitted from `.gitignore`. While currently containing placeholder values, any developer or deployment commit containing real credentials will be committed to git history.
2. **HIGH — Authentication & Role Impersonation Bypass:**  
   In `dashboard/views.py` and `dashboard/context_processors.py`, any unauthenticated user can append `?role=admin` to any URL to bypass `_require_auth()` and receive full administrative view rights. Furthermore, `/shell-demo/` is explicitly open to unauthenticated users.
3. **HIGH — Client-Side Sensitive Data Exposure:**  
   The `overview_view` fetches all project valuations, cumulative costs, client invoices, balance dues, commercial leads, and rate cards, serializing them into HTML and `feed_items_json`. Tabs are toggled client-side via Alpine.js (`x-show`), violating Principle 3 ("The server decides").
4. **HIGH — Potential XSS in `status_badge` Filter:**  
   `dashboard/templatetags/dashboard_tags.py` invokes `mark_safe` on an f-string without escaping the `label` parameter for unknown status strings.
5. **MEDIUM — External CDN Script Execution:**  
   `templates/base.html` loads unpinned Tailwind Play CDN (`https://cdn.tailwindcss.com`), HTMX (`https://unpkg.com/htmx.org@2.0.4`), and Alpine.js (`https://unpkg.com/alpinejs@3.14.8`) from third-party CDNs, preventing the implementation of a strict Content-Security-Policy (CSP) and introducing supply-chain risks.
6. **MEDIUM — Insecure Default Settings:**  
   `DEBUG` defaults to `True`, `ALLOWED_HOSTS` defaults to `['*']`, and `SECRET_KEY` falls back to a hardcoded insecure development key if environment variables are absent.

---

## 1. Versions & Support Status

| Component | Pinned / Runtime Version | Release Line | Support Status |
|---|---|---|---|
| **Python** | `3.14.8` (local runtime GCC 15.3.0) / `3.11-3.12` (cPanel target) | Python 3.14 (Development) | Active. **Note for cPanel:** Namecheap CloudLinux runs Python 3.11 / 3.12. |
| **Django** | `5.2.18` (in requirements: `Django>=5.2,<5.3`) | Django 5.2 LTS | **Supported.** Django 5.2 LTS was released April 2025 and receives official security fixes through April 2028. |
| **Tailwind CSS** | Unpinned runtime CDN (`https://cdn.tailwindcss.com`) | Tailwind CSS v3 (schema in `tailwind.config.js`) | **Flagged:** Delivered via browser-executed Play CDN script. Not installed via npm or compiled into static assets. |
| **Other Packages** | `django-htmx==1.21.0`, `whitenoise==6.9.0`, `pymysql==1.1.1`, `pillow==11.1.0`, `openpyxl==3.1.5`, `reportlab==4.4.1` | Various | All active and maintained. |

---

## 2. Database Configuration & User Model State

- **Engine Configuration:**  
  Configured in `jimcan/settings.py` (lines 81–111). If both `DB_NAME` and `DB_USER` environment variables are present, it dynamically loads `pymysql` and connects to `django.db.backends.mysql` (port 3306, utf8mb4). Otherwise, it falls back to `django.db.backends.sqlite3` located at `BASE_DIR / 'db.sqlite3'`.
- **User Table Migrations:**  
  Running `showmigrations` reveals that `django.contrib.auth` migrations `0001_initial` through `0012_alter_user_first_name_max_length` have already been executed against `db.sqlite3`.
- **Existing Users in Database:**  
  Inspecting `auth.User` in `db.sqlite3` reveals **4 existing user accounts**:
  1. `ADMIN` (`is_staff=True`, `is_superuser=True`)
  2. `George` (`is_staff=True`, `is_superuser=True`)
  3. `admin_boss` (`is_staff=True`, `is_superuser=True`)
  4. `admin` (`is_staff=False`, `is_superuser=False`)
- **AUTH_USER_MODEL Status:**  
  `AUTH_USER_MODEL` is not defined in `settings.py` (defaults to `auth.User`). Because `auth.User` already has applied migrations and live user records, **`AUTH_USER_MODEL` must NOT be swapped.** Extended attributes (job title, phone, must_change_password) must be implemented via a OneToOne profile model (`UserProfile`), and roles must be implemented via Django Groups per project rules.

---

## 3. Settings and Secrets

- **Settings Structure:** Single file `jimcan/settings.py`. Uses `python-dotenv` to load `.env` at startup.
- **Environment Fallbacks:**
  - `SECRET_KEY`: Uses `os.environ.get('SECRET_KEY', 'jimcan-dev-insecure-key-2026-phase-0-scaffolding')`. Insecure hardcoded fallback present.
  - `DEBUG`: Evaluates `os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')`. Defaults to `True` if missing!
  - `ALLOWED_HOSTS`: Defaults to `['*']` if `ALLOWED_HOSTS` is missing or `'*'`.
- **Git Tracking & Gitignore Audit:**
  - **Tracked files that should NOT be tracked:**
    - `.env` is currently committed and tracked (`git ls-files .env`).
  - `.gitignore` contents:
    - Correctly ignores: `db.sqlite3`, `db.sqlite3-journal`, `staticfiles/`, `media/`, `*.log`, `venv/`, `__pycache__/`.
    - **Missing from `.gitignore`:** `.env`, `.env.*` (except `.env.example`).
- **Git History Secrets Search:**
  - Running `git log -p -S "SECRET_KEY"` reveals that `.env` and `.env.example` were introduced in commit `56ca14b` and `e7d8983`.
  - Both files contained placeholder values (`generate-a-strong-random-50-character-string-here`, `your_email_password`).
  - No active production passwords or keys were detected in the committed history.

---

## 4. Middleware and Authentication Backends

### Middleware Pipeline (in order of execution)
1. `django.middleware.security.SecurityMiddleware` (Standard Django security headers)
2. `whitenoise.middleware.WhiteNoiseMiddleware` (Static asset caching & delivery)
3. `django.contrib.sessions.middleware.SessionMiddleware` (Cookie-based session store)
4. `django.middleware.common.CommonMiddleware` (URL normalization)
5. `django.middleware.csrf.CsrfViewMiddleware` (CSRF token enforcement)
6. `django.contrib.auth.middleware.AuthenticationMiddleware` (Associates user with request)
7. `django.contrib.messages.middleware.MessageMiddleware` (Flash messages)
8. `django.middleware.clickjacking.XFrameOptionsMiddleware` (DENY/SAMEORIGIN framing)
9. `django_htmx.middleware.HtmxMiddleware` (Inspects HTMX headers)
10. `jimcan.middleware.HtmxAuthRedirectMiddleware` (Injects `HX-Redirect` on 401/403 or login redirects)
11. `jimcan.middleware.PrivateCacheControlMiddleware` (Applies `no-cache, no-store, must-revalidate, private` to HTML responses)

### Authentication Backends
- `AUTHENTICATION_BACKENDS` is not explicitly declared in `settings.py`.
- Defaults to: `['django.contrib.auth.backends.ModelBackend']`.
- `PASSWORD_HASHERS` is not explicitly declared; defaults to PBKDF2 (`django.contrib.auth.hashers.PBKDF2PasswordHasher`). Argon2 is not yet configured.

---

## 5. URLs and View Protections

| URL Pattern | View Name / Handler | Current Protection Mechanism | Security Assessment |
|---|---|---|---|
| `admin/` | `admin.site.urls` | Django Admin (`is_staff` check) | **Exposed on default URL.** No rate limiting or 2FA yet. |
| `/` | `WelcomeLoginView` | Public (LoginView) | Public landing / redirects authenticated users. |
| `login/` | `WelcomeLoginView` | Public (LoginView) | Public login endpoint. |
| `logout/` | `LogoutView` | POST required (CSRF protected) | Standard auth endpoint. |
| `password_change/` | `PasswordChangeView` | Django Built-in `LoginRequired` | Authenticated users only. |
| `password_change/done/` | `PasswordChangeDoneView` | Django Built-in `LoginRequired` | Authenticated users only. |
| `password_reset/` | `PasswordResetView` | Public | Public account recovery initiation. |
| `password_reset/done/` | `PasswordResetDoneView` | Public | Informational confirmation. |
| `reset/<uidb64>/<token>/`| `PasswordResetConfirmView`| Public (token validated) | Public one-time token reset. |
| `reset/done/` | `PasswordResetCompleteView`| Public | Informational confirmation. |
| `overview/` | `views.overview_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `dashboard/` | `views.overview_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `leads/` | `views.leads_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `projects/` | `views.projects_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `rates/` | `views.rates_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `invoices/` | `views.invoices_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `expenses/` | `views.expenses_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `tax/` | `views.tax_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `files/` | `views.files_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `styleguide/` | `views.styleguide_view` | Custom `_require_auth` | **VULNERABLE:** Accessible in production without DEBUG check. |
| `shell-demo/` | `views.shell_demo_view` | Bypassed in `_require_auth` | **UNPROTECTED:** Publicly accessible to unauthenticated visitors. |
| `settings/` | `views.settings_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `setup/` | `views.setup_checklist_view`| Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `audit/` | `views.audit_view` | Custom `_require_auth` + `_check_permission` | **VULNERABLE:** Bypassed via `?role=admin`. |
| `api/heartbeat/` | `views.api_heartbeat_view` | **None** | **UNPROTECTED:** Returns `{status: alive, authenticated: True}` to anyone. |
| `api/test-toast/` | `views.api_test_toast_view`| **None (`@csrf_exempt`)** | **UNPROTECTED:** Development endpoint left open. |
| `api/test-htmx-401/` | `views.api_test_htmx_401` | **None (`@csrf_exempt`)** | **UNPROTECTED:** Test endpoint left open. |
| `api/test-htmx-403/` | `views.api_test_htmx_403` | **None (`@csrf_exempt`)** | **UNPROTECTED:** Test endpoint left open. |
| `test-403/` | `views.test_403_view` | **None** | Public error preview. |
| `test-404/` | `views.test_404_view` | **None** | Public error preview. |
| `test-500/` | `views.test_500_view` | **None** | Public error preview. |
| `test-400/` | `views.test_400_view` | **None** | Public error preview. |

---

## 6. Models & Schema State

- **Current Database Models in Code:**  
  Zero custom application models exist in Python code today (`dashboard` has no `models.py`). Only Django built-in models exist (`auth.User`, `auth.Group`, `auth.Permission`, `contenttypes.ContentType`, `sessions.Session`, `admin.LogEntry`).
- **Planned Schema Models (from TRD & Backend Schema Document):**  
  See `docs/security/model-classification.md` for full classification across Financial, Operational, Identity, and System classes.
- **EFRIS Compliance Note:**  
  `dashboard/views.py` contains mock field `'URA FISCAL STATUS': 'EFRIS COMPLIANT'`. In the backend schema, `CompanyProfile` includes `tin`, `vat_number`, `vat_registered`. Specific EFRIS fiscal fields (`fiscal_receipt_number`, `qr_code`, `verification_url`, `efris_status`) are not yet formally defined in models.

---

## 7. Data Exposure Findings

1. **Role Simulation Parameter Bypass:**  
   In `dashboard/views.py`:
   ```python
   def _require_auth(request):
       if not request.user.is_authenticated:
           if request.GET.get('role') or request.session.get('active_role') or request.path.startswith('/shell-demo'):
               return None
           return redirect(f"{reverse('login')}?next={request.path}")
       return None
   ```
   An anonymous user passing `?role=admin` bypasses all authentication, sets `request.session['active_role'] = 'admin'`, and gains access to every view.
2. **DOM-Level Tab Hiding in Overview View:**  
   `templates/dashboard/overview.html` loads all project valuations, invoices, leads, and BOQ rates simultaneously into the DOM and toggles visibility via `x-show="activeTab === 'invoices'"`. Any user with view access to the dashboard page can inspect HTML or JavaScript state (`feed_items_json`) to read financial and commercial data.
3. **Session Heartbeat False Affirmation:**  
   `api/heartbeat/` returns `{'status': 'alive', 'authenticated': True}` even when the requester possesses no active session.

---

## 8. Dangerous Code Patterns

| Search Pattern | Occurrences Found | Location & Impact |
|---|---|---|
| `|safe` | 0 | None. |
| `mark_safe` | 5 | `dashboard/templatetags/dashboard_tags.py` (lines 38, 62, 224, 250). Line 250 evaluates `mark_safe(f'...{label}...')` without HTML escaping on arbitrary status strings. **Remediation required.** |
| `.raw(`, `.extra(`, `RawSQL` | 0 | None. |
| `cursor.execute` | 0 | None. |
| `eval(`, `exec(`, `pickle` | 0 | None. |
| `yaml.load` | 0 | None. |
| `subprocess`, `os.system`| 0 | None. |
| `csrf_exempt` | 4 | `dashboard/views.py` (lines 447, 454, 469, 474). Applied to test API endpoints. Must be removed in production. |
| `innerHTML` | 0 | None in templates or static scripts. |
| `.delete()` on financial models | 0 | No business models built yet. |

---

## 9. Uploads and Downloads

- **Current Storage Configuration:**  
  `MEDIA_ROOT` and `MEDIA_URL` are completely unconfigured in `settings.py`.
- **Upload Views:**  
  `/files/` is currently a placeholder template. No file upload views, models, or processing pipelines exist.
- **Handling Dependencies:**  
  `pillow>=10.0` is installed. No EXIF metadata scrubbing (GPS removal) is implemented.
- **Download Protection:**  
  No private media serving or signed URL mechanism exists.

---

## 10. Deployment & Hosting (Namecheap cPanel)

- **WSGI / Passenger Bridge:**  
  `passenger_wsgi.py` exists in repo root, exposing `from jimcan.wsgi import application`.
- **Client IP & SSL Header Verification:** **UNKNOWN**  
  - It cannot be proven from repository code whether Phusion Passenger on Namecheap passes client IP in `REMOTE_ADDR` or sets `HTTP_X_FORWARDED_FOR`.
  - `SECURE_PROXY_SSL_HEADER` is not set in `settings.py`.
  - **Required Action for Human on Server:** Run a test script in cPanel to inspect `request.META['REMOTE_ADDR']`, `request.META.get('HTTP_X_FORWARDED_PROTO')`, and `request.is_secure()`.

---

## 11. Exposure of Sensitive Files

- **Repo Layout Assessment:**  
  `docs/NAMECHEAP_DEPLOYMENT_GUIDE.md` specifies cloning into `/home/<username>/jimcan`.
- **Risk Evaluation:** **UNKNOWN / HIGH**  
  If the application root is misconfigured to reside within `public_html`, Apache will directly serve `.env`, `.git/`, and `db.sqlite3` to any web visitor because no `.htaccess` file exists in the repository.
  - **Required Action for Human on Server:** Ensure the repo directory is strictly outside `public_html` (e.g. `~/jimcan`), and install an `.htaccess` rule blocking direct access to `.env`, `.git`, and `*.sqlite3`.

---

## 12. Email System Configuration

- **Configuration in `settings.py`:**  
  Configured to use `console.EmailBackend` if `DEBUG` is true, otherwise `smtp.EmailBackend`. Reads `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.
- **Bug Identified:**  
  In `settings.py`, `EMAIL_USE_SSL` is never inspected. In `.env`, `EMAIL_PORT=465` and `EMAIL_USE_SSL=True` are declared. Connecting to port 465 with `EMAIL_USE_TLS=True` will fail.
- **Sending Domain & DNS Records (SPF/DKIM):** **UNKNOWN**  
  Mentioned in TRD, but no DNS records or sending domains are configured in the repo.

---

## 13. Django Admin Usage

- **Current State:**  
  `django.contrib.admin` is enabled at `/admin/`. No custom models are registered.
- **Usage:**  
  Currently only a development leftover. As per project rules, Django admin must be disabled in production by default, and if enabled, must sit on a non-default secret path behind 2FA.

---

## 14. Existing Audit Logging

- **Current State:**  
  Only Django's built-in `admin.LogEntry` table exists in `db.sqlite3`.
- **Application Level:**  
  No audit logging middleware, model, or event handler exists. `/audit/` renders a placeholder.

---

## 15. Public Pages

### Intentionally Public
- `/` and `/login/` (Welcome and login card)
- `/password_reset/`
- `/password_reset/done/`
- `/reset/<uidb64>/<token>/`
- `/reset/done/`

### Unintentionally Exposed (Must be locked down in Phase 2)
- `/shell-demo/`
- `/api/heartbeat/`
- `/api/test-toast/`, `/api/test-htmx-401/`, `/api/test-htmx-403/`
- `/test-403/`, `/test-404/`, `/test-500/`, `/test-400/`
- All dashboard sections via `?role=admin` query parameter bypass

---

## 16. Test Suite Baseline

- **Test Suite Location:** `tests/test_phase1_shell.py`, `tests/test_phase2_auth.py`.
- **Execution Command:** `./venv/bin/python manage.py test tests`
- **Result:**
  ```text
  Ran 37 tests in 10.815s
  OK
  ```
- **Baseline:** 37 passing tests, 0 failures, 0 errors.
