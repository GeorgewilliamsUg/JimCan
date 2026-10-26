# Phase 3: Audit Core and Owner Alerts

Read `CLAUDE.md` first. **Prerequisite:** Phase 2 is committed.

## Goal

A tamper-evident record of security events, a separate prunable log for noisy events, and a way to tell Owners when something important happens. **Financial model auditing is added later (Phase 6), after Gate 2.** If an audit log page or model already exists (Phase 0 item 14), extend it rather than building a second system.

## Design rules

- **Two tables, on purpose.**
  - `AuditEvent`: important events. Chained, append-only, never pruned.
  - `SecurityNoise`: high-volume events (failed logins, permission denied). Not chained, deduplicated, and prunable after 90 days. This stops attackers from filling your database or breaking the chain by pruning.
- **Keyed chain.** Each `AuditEvent` stores a sequence number, `prev_hash` and `entry_hash`. The hash is HMAC-SHA256 over a canonical serialisation of the event plus `prev_hash`, using a key from the environment variable `AUDIT_HMAC_KEY` (a different secret from `SECRET_KEY`). The app refuses to start in production without it. A plain unkeyed hash can be recomputed by anyone who can write to the database; a keyed one cannot.
- **Same transaction.** For events about a data change, the audit row and the change are written in the same database transaction. If the audit write fails, the change fails too. For read-only events (such as a failed login) a failure to write is logged to the security log file and the request continues; do not turn a logging hiccup into an outage.
- **No forks.** Two simultaneous requests must not create two events with the same sequence number. Use a single-row chain-head table locked with `select_for_update()` where the engine supports it. For SQLite, use whichever mechanism the installed Django documents to take the write lock before reading the head. Prove it with a concurrency test using threads. **If you cannot guarantee serial writes on this engine, say so and do not ship a chain that can fork.**
- **Never recorded:** passwords, hashes, OTP secrets, backup codes, session keys, reset tokens. Keep an explicit field-name denylist applied to every `changes` diff. For failed logins, record the attempted username only if it matches an existing account; otherwise store `[unknown account]` (people sometimes type their password into the username box).

## Tasks

1. Models: `AuditEvent` (sequence, UTC timestamp, actor FK nullable plus a stored copy of the username, client IP, truncated user agent, event type, target model, target object id and readable label, JSON `changes`, request id, `alert` flag, `prev_hash`, `entry_hash`), `AuditChainHead`, and `SecurityNoise` (type, ip, path, count, first seen, last seen).
2. One function is the only way to write: `record_event(...)`. Everything else calls it. Replace the Phase 2 `security_event()` hook with calls to it.
3. Context middleware using `contextvars` to hold the current user, IP and request id. Code with no request records the actor as "system". Place it in the documented middleware order and update `docs/security/middleware-order.md` and its test.
4. Append-only enforcement: `save()` permits inserts only; instance `delete()` and queryset `update()` and `delete()` raise. No role, including Owner, gets change or delete permission on audit events. If the admin is enabled, make the model read-only there.
5. Events to record now (all in `AuditEvent` unless marked noise): login success, logout, session expiry, account locked, password changed, password reset requested and completed, owner bootstrapped, setup link issued, user created, deactivated, reactivated, role changed. Noise table: failed logins and permission denied (403). Cap noise inserts: deduplicate by (type, ip, path) per minute, and if more than a set number of new noise rows appear in an hour, stop inserting and write one summary line to the log file.
6. **Commands:**
   - `verify_audit_chain`: recomputes the chain and reports the first bad sequence number, and separately reports a gap in sequence numbers.
   - `audit_anchor`: prints the latest sequence number, the head hash and the time. The human emails or stores this weekly outside the server (cron plus email). It is what makes **deleting the newest rows** detectable.
   - `prune_noise`: deletes `SecurityNoise` rows older than 90 days. It never touches `AuditEvent`.
7. **Owner alerts.** `notify_owners(subject, event)` emails all active Owners. It must never raise or block the request: wrap it, and log failures. Content includes the event type, user and time, and never any secret or link. Send an alert for: account locked, new authenticator registered, backup code used, two-factor reset, role changed, user created, chain verification failure, and a burst of failed logins. Also mark these events `alert=True` so a "Security notices" list shows them to Owners even when email is down.
8. **Audit log page** (Owner only, requires `view_audit_log`, wired in Phase 5): filter by user, event type and date, paginated, read-only, times in `Africa/Kampala`. A "Security notices" tab lists `alert=True` events.
9. Extend `security_status`: chain verifies, count of unreviewed alerts, `AUDIT_HMAC_KEY` set, last anchor time if recorded.

## Tests

- Each event type above creates a row with the correct actor, IP and type.
- Denylisted fields never appear in `changes`. An unknown failed-login username is stored as `[unknown account]`.
- The chain verifies. Editing any stored row (field change, using raw update in the test) makes verification fail at that row. Deleting a middle row shows a gap. 
- `save()` on an existing event, instance `delete()`, queryset `update()` and `delete()` all raise.
- Concurrent writers (threads) produce a gap-free, non-forked chain.
- A failure inside the audit write for a data change rolls the change back. A failure for a read-only event does not break the request.
- `notify_owners` never raises, even with a broken mail backend.
- Noise deduplication and the hourly cap work.
- Production start fails without `AUDIT_HMAC_KEY`.

## Done when

Tests pass, commands documented in `docs/security/`, report printed. Commit.
