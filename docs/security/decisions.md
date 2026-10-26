# Security Decisions Log

Record of all security-related architectural, configuration, and implementation decisions made during the build.
Each entry is one line with the decision and the reason.

| Date | Phase | Decision | Rationale |
|---|---|---|---|
| 2026-10-26 | Phase 0 | Retain auth.User as AUTH_USER_MODEL | Database contains applied auth migrations 0001-0012 and 4 existing user accounts; swapping user models after migration is unsafe. Extended attributes will use OneToOne UserProfile. |
| 2026-10-26 | Phase 0 | Classify models into 4 distinct security tiers | Separates financial records (immutable, no hard delete) from operational, identity, and system records. |
