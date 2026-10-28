# Security Decisions Log

Record of all security-related architectural, configuration, and implementation decisions made during the build.
Each entry is one line with the decision and the reason.

| Date | Phase | Decision | Rationale |
|---|---|---|---|
| 2026-10-26 | Phase 0 | Retain auth.User as AUTH_USER_MODEL | Database contains applied auth migrations 0001-0012 and 4 existing user accounts; swapping user models after migration is unsafe. Extended attributes will use OneToOne UserProfile. |
| 2026-10-26 | Phase 0 | Classify models into 4 distinct security tiers | Separates financial records (immutable, no hard delete) from operational, identity, and system records. |
| 2026-10-26 | Phase 1 | Enforce strict SECRET_KEY with SECRET_KEY_FALLBACKS | Raises ImproperlyConfigured if missing, preventing startup with insecure defaults; fallbacks enable zero-downtime key rotation. |
| 2026-10-26 | Phase 1 | Default DEBUG to False with strict host validation | Prevents accidental information exposure; ALLOWED_HOSTS rejects wildcards in production. |
| 2026-10-26 | Phase 1 | Stage HSTS at 300 seconds without subdomains or preload | Protects against persistent lockouts during initial rollout while enforcing HTTPS. |
| 2026-10-26 | Phase 1 | Omit SECURE_PROXY_SSL_HEADER and make SSL redirect switchable | Namecheap proxy header behavior is unverified; avoids redirect loops or spoofed HTTPS. |
| 2026-10-26 | Phase 1 | Disable Django Admin by default on non-default path | Attack surface reduction; admin is conditionally mounted and rejects 'admin/' in production. |
| 2026-10-26 | Phase 1 | Enforce no-store cache headers on authenticated/auth pages | Prevents back-button browser cache disclosure of sensitive financial/auth data without impacting static assets. |
| 2026-10-26 | Phase 1 | Configure rotating file logger outside web-served root | Captures django.security and django.request events (5MB x 5 backups) without exposing logs to HTTP GET requests. |
| 2026-10-26 | Phase 2 | Custom JimcanArgon2PasswordHasher (memory_cost=19456, time_cost=2, parallelism=1) | Tuned for cPanel shared hosting 1GB RAM budget (~19MB RAM footprint, 45.7ms execution vs PBKDF2 623ms and default Argon2 124ms). |
| 2026-10-26 | Phase 2 | Set minimum password length to 12 with 1-hour reset token timeout | Eliminates weak/dictionary passwords while bounding token exposure window without introducing complex character puzzles. |
| 2026-10-26 | Phase 2 | Disallow public registration and route user provisioning via bootstrap_owner and one-time setup tokens | Enforces Owner-only account creation; bootstrap_owner refuses to run if any account exists; tokens are single-use and emailed/printed to console. |
| 2026-10-26 | Phase 2 | Standardize authentication failure messages to 'Incorrect username or password.' | Mitigates user enumeration across login and password reset boundaries. |
| 2026-10-26 | Phase 2 | Enforce 30-minute idle inactivity timeout and 8-hour absolute session ceiling | Database-backed sessions expire automatically on inactivity or duration; throttled at 60s intervals to minimize DB overhead. |
| 2026-10-26 | Phase 2 | Terminate secondary sessions upon password change via sign_out_everywhere | Preserves the active user's session while revoking stolen or stale sessions across other devices. |
| 2026-10-26 | Phase 2 | Configure django-axes with 5-failure threshold and 30-minute cooloff per username+IP | Mitigates brute-force credential stuffing attacks using REMOTE_ADDR client tracking with automated security event emission. |
| 2026-10-26 | Phase 2 | Enable LoginRequiredMiddleware with explicit public URL allowlist | Implements deny-by-default access control where all internal views require authentication unless decorated with @login_not_required. |
| 2026-10-26 | Phase 2 | Step-up re-authentication requirement (@require_recent_auth) within 10 minutes for high-risk actions | Prevents session hijacking from unattended workstations during sensitive operations. |
| 2026-10-26 | Phase 2 | Enforce zero superusers across database and test suite | Demotes superusers to Owner group with explicit permissions; Django is_superuser flag treated as dead code. |
| 2026-10-26 | Phase 3 | Split audit architecture into AuditEvent and SecurityNoise tables | Separates immutable, cryptographically chained governance events from noisy, prunable high-volume records (403s, bad logins) to prevent DB exhaustion and chain breakage. |
| 2026-10-26 | Phase 3 | Keyed HMAC-SHA256 audit chaining using AUDIT_HMAC_KEY | Secret HMAC key prevents attackers with direct database write access from recomputing valid hashes after tampering with stored rows. |
| 2026-10-26 | Phase 3 | AuditChainHead table with select_for_update() and thread locking | Guarantees monotonic sequence ordering (1, 2, 3...) and prevents sequence forks during concurrent multi-threaded requests. |
| 2026-10-26 | Phase 3 | Hardcoded DENYLIST_FIELDS for audit changes diffs | Automatically scrubs passwords, tokens, session keys, and secrets from audit change payloads before persistence. |
| 2026-10-26 | Phase 3 | Redact unknown login failure usernames to '[unknown account]' | Protects credentials when users accidentally type their password into the username field. |
| 2026-10-26 | Phase 3 | AuditContextMiddleware using Python contextvars at middleware position 10 | Captures ambient user, client IP, and request UUID across asynchronous and decoupled code paths without manual argument passing. |
| 2026-10-26 | Phase 3 | Non-blocking notify_owners alert dispatcher | Delivers critical security alerts (lockouts, alerts) via email without blocking the HTTP request or raising unhandled exceptions. |
| 2026-10-26 | Phase 4 | Enforce TOTP and static backup recovery tokens only (no SMS or phone plugins) | Mitigates SIM-swapping and SS7 interception risks while eliminating third-party telephony costs. |
| 2026-10-26 | Phase 4 | Show 10 static backup recovery codes once upon enrollment | Prevents account lockout if phone is lost while keeping tokens out of persistent session storage. |
| 2026-10-26 | Phase 4 | Enable exponential throttling on TOTP and static codes via OTP_TOTP_THROTTLE_FACTOR=1 | Mitigates brute-force guessing attacks against 6-digit codes and static tokens with exponential delays. |
| 2026-10-26 | Phase 4 | Place OTPMiddleware at position 7 and MFAEnforcementMiddleware at position 12 | Attaches OTP verification status immediately after auth; enforces deny-by-default MFA redirects before view rendering. |
| 2026-10-26 | Phase 4 | Staged rollout controlled via MFA_ENFORCEMENT switch ('off' -> 'owners' -> 'all') | Prevents administrative lockout during deployment; defaults to fail-secure 'all' in production. |
| 2026-10-26 | Phase 4 | Record mfa_enforcement_mode audit event at application startup | Makes any silent or unauthorized downgrade of MFA enforcement mode immediately visible in the immutable audit log. |
| 2026-10-26 | Phase 4 | Enforce step-up re-authentication on authenticator changes and recovery resets | Protects high-risk MFA device configuration and user management from hijacked sessions. |
| 2026-10-26 | Phase 4 | Automatic deactivation of accounts pending MFA enrollment after 72 hours | Closes the vulnerability window where an intercepted setup link can be abused before enrollment. |
| 2026-10-26 | Phase 4 | Prohibit self-service MFA reset by Owners through the web UI | Mitigates malicious takeovers; forces recovery through backup codes, a second Owner, or SSH server command. |
| 2026-10-26 | Phase 4 | Mandate encrypted database backups due to recoverable TOTP secret storage | Discloses that django-otp stores TOTP keys in plain hex, requiring GPG/AES-256 encryption on all DB backups. |
| 2026-10-27 | Phase 5 | Define three canonical roles (Owner, Finance, Site staff) in accounts/roles.py as single source of truth | Centralizes RBAC definition; setup_roles management command idempotently creates groups and synchronizes exact permission sets matching approved matrix. |
| 2026-10-27 | Phase 5 | Zero superusers rule enforced across all roles and user management views | Owners are standard accounts whose group holds explicit permissions. The is_superuser attribute is strictly prohibited and stripped server-side on any save. |
| 2026-10-27 | Phase 5 | Custom permissions declared on unmanaged AppPermission model (managed=False, default_permissions=()) | Cleanly attaches non-model permissions (view_financials, view_tax_reports, manage_users, etc.) without creating unneeded database tables. |
| 2026-10-27 | Phase 5 | Server-side financial data scoping for users without view_financials | Financial figures (contract value, site cost, invoiced gross, balances, money flow) are scrubbed in Python view logic before context/JSON creation, not merely hidden with template if-tags. |
| 2026-10-27 | Phase 5 | Site staff see all projects in dashboard overview (FLAGGED) | Phase 0 audit confirmed no ProjectMember or assignment concept exists in current database schema. Scoping to assigned builds is deferred until project models are migrated in future phase. |
| 2026-10-27 | Phase 5 | User deletion permanently disabled in UI and Django Admin | Users are deactivated, never deleted from database, preserving audit history and referential integrity (has_delete_permission=False). |
| 2026-10-27 | Phase 5 | Mandatory step-up re-authentication and session revocation for user management mutations | User provisioning, role demotions/promotions, deactivations, and MFA resets require recent auth (<10 min); role changes and deactivations call sign_out_everywhere(). |
| 2026-10-27 | Phase 5 | Last active Owner protection on deactivation and role demotion | Server-side validation refuses deactivation or demotion if active Owner count would drop below 1, preventing permanent system lockout. |
| 2026-10-27 | Phase 5 | Restrict styleguide and shell demo views to DEBUG mode only | Returns 404 in production to eliminate development showroom surface area outside debugging environments. |
| 2026-10-28 | Phase 4/Ops | Configurable TOTP clock drift tolerance via OTP_TOTP_TOLERANCE (default 2, +/- 60s) | Compensates for NTP time drift on shared hosting (cPanel/Namecheap) and client mobile devices during 2FA enrollment and verification while preserving exponential throttling. |


