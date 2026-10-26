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

