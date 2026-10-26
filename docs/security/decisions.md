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



