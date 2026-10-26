# Phase 2: Authentication

Read `CLAUDE.md` first. **Prerequisite:** Phase 1 is committed and `docs/security/approvals/gate1.md` exists and begins with `APPROVED`.

## Goal

Strong passwords, a safe login flow, no public sign-up, safe session lifetimes, lockout against guessing, a deny-by-default site, and a re-authentication helper for sensitive actions. The audit log does not exist yet (Phase 3), so where an event should be recorded, call a small `security_event()` hook that for now writes to the security log file. Phase 3 will connect it to the audit log.

## Tasks

### 1. Password hashing (measure first)
- Install `argon2-cffi` after printing the dependency dry run.
- Django's default Argon2 setting uses around 100 MB of memory per hash, which can crash a shared hosting account under load. Write `scripts/hash_benchmark.py` that measures time and peak memory of one hash for each candidate: Django's default PBKDF2, default Argon2, and a custom subclass of `Argon2PasswordHasher` with `memory_cost = 19456`, `time_cost = 2`, `parallelism = 1`.
- Use the custom Argon2 subclass only if one hash takes roughly 150 to 600 ms and uses modest memory on the machine you test. Otherwise keep Django's default PBKDF2. Either way, keep PBKDF2 hashers in the list after the first one so existing hashes still verify and upgrade at next login.
- Record the benchmark result in `docs/security/decisions.md` and add a manual step: the human must run the same benchmark on the real hosting before release.

### 2. Password rules
- `AUTH_PASSWORD_VALIDATORS`: user attribute similarity, minimum length **12**, common password, numeric only. No forced symbol or capital rules.
- `PASSWORD_RESET_TIMEOUT = 3600`.
- A change-password page that asks for the current password. After a change, all of that user's other sessions end (use Django's supported mechanism and prove it with a test).
- No "remember me", no password hints, no security questions.

### 3. No public sign-up
- Confirm no registration page or route exists. Add a test that fails if one appears.

### 4. First Owner and later accounts
- `bootstrap_owner` management command: refuses to run if any user exists. Prompts interactively for username, email and password (hidden input, checked by the validators). Creates the account **active, not staff, not superuser**, in the group `Owner` (create the group if missing; permissions are attached in Phase 5). The password is never an argument or environment variable. Calls `security_event("owner_bootstrapped")`.
- New accounts (created by an Owner in Phase 5) have an **unusable password** and receive a one-time set-password link using Django's token mechanism with the one-hour limit. Build the reusable function now: `send_setup_link(user)`.
- `issue_setup_link <username>` management command for use when email does not work: prints a one-time link to the console only. It never prints or stores a password.
- A deactivated user can never log in or complete a reset.

### 5. Login behaviour
- One generic failure message: "Incorrect username or password." The reset form responds identically whether or not the email exists.
- Login, logout, password change and reset are CSRF protected. Logout is POST only.
- Redirects after login accept only same-host paths (use `url_has_allowed_host_and_scheme`).
- If the design tokens from the dashboard redesign exist, style these pages with them. Do not block on this.

### 6. Sessions
- Database sessions. No signed-cookie sessions.
- Idle timeout **30 minutes**, absolute timeout **8 hours**, as named constants. Implement as a small middleware storing `session_started_at` and `last_activity` in the session. Update `last_activity` at most once per minute. When either limit passes, log the user out and show "Your session expired."
- `sign_out_everywhere(user)` helper that deletes all of a user's sessions. It is used on deactivation, role change and two-factor reset. At this scale, scanning the session table is acceptable.
- Document a scheduled `clearsessions` job in the runbook notes.

### 7. Lockout with `django-axes`
- Install after the dry run. Read the **installed** package's documentation and source for exact setting names; do not use memory.
- Target: lock after 5 failures, cool-off 30 minutes, reset the counter on success, lock on the combination of username and IP address.
- **Client IP rule:** confirm the real client IP is visible to the app (Phase 0 item 10). Configure IP detection exactly as the axes documentation says, and never trust `X-Forwarded-For` except from a known proxy. **If the real IP cannot be established, do not fall back to username-only lockout** (that lets anyone lock the Owner out forever). Stop, report, and ask.
- Axes must sit where its documentation says in the middleware list (it normally must be last).
- Provide and document a way for an Owner to unlock an account.
- When a lockout happens call `security_event("account_locked", ...)`.

### 8. Deny by default
- Django 5.1 or newer: enable the built-in `LoginRequiredMiddleware` and mark only genuinely public views with `login_not_required` (login, logout, password reset, set-password pages, and anything Phase 0 listed). Older Django: write an equivalent middleware with an explicit allowlist of URL names.
- Third-party views (the two-factor login views, added in Phase 4) cannot be edited, so exempt them by wrapping them in your URL configuration with `login_not_required(view)`. Prove it works with a test.
- Keep the allowlist in one file: `accounts/public_urls.py`.

### 9. Re-authentication ("step-up") helper
- `@require_recent_auth(minutes=10)` decorator and a matching mixin. If the user has not re-entered their password (and, once Phase 4 exists, a fresh code) within the window, redirect to a re-auth page and return to the original action after success. Store `reauth_at` in the session. Used in Phase 5 and later for: creating or changing users, role changes, two-factor resets, voiding, exports of tax data, and settings changes.

### 10. Middleware order
- Decide the order using the installed packages' documentation. A sensible starting point (verify and adjust): Security, Session, Common, CSRF, Authentication, (OTP in Phase 4), LoginRequired, session timeout, (two-factor enforcement in Phase 4), (audit context in Phase 3), Messages, Clickjacking, no-store, Axes last.
- Write the final order and the reason for each position to `docs/security/middleware-order.md`, and add a test that asserts `settings.MIDDLEWARE` equals the documented list, so a change is always deliberate.

### 11. `security_status` additions
Password hasher in use, validator minimum length, session limits, axes configured, `LoginRequiredMiddleware` present.

## Tests

- Wrong password five times, then the correct password: rejected during lockout. After the cool-off (use a time override), accepted.
- Session key differs before and after login.
- Idle timeout and absolute timeout both log the user out.
- Changing a password ends the user's other sessions.
- A deactivated user cannot log in and cannot complete a reset.
- Reset form gives identical responses for existing and non-existing emails.
- Every URL pattern (see the route-test rule in Phase 5) returns a redirect to login or 403 for an anonymous user, except the public allowlist.
- `bootstrap_owner` refuses when a user exists; the created account is not superuser and not staff.
- Safe redirect: an external `next` URL is ignored.
- The re-authentication decorator blocks when `reauth_at` is old and allows when recent.
- `settings.MIDDLEWARE` equals the documented order.
- No account with `is_superuser=True` exists after any of the above.

## Done when

Tests pass, benchmark recorded, order documented, report printed. Commit.
