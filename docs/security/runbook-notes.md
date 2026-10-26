# Security Operations Runbook Notes

This document provides operational procedures for maintaining the security guardrails of the Jimcan Operations Dashboard in production.

---

## 1. Scheduled Session Cleanup (`clearsessions`)

Django stores session data in the database (`django_session` table). Over time, expired sessions accumulate and must be purged to maintain optimal database performance and minimize storage overhead.

### Automated Cron Job (Namecheap cPanel)
In cPanel, navigate to **Cron Jobs** (under **Advanced**) and configure a daily maintenance job running at 03:00 UTC:

```bash
# Daily at 3:00 AM UTC
0 3 * * * cd /home/<cpanel_user>/jimcan && source /home/<cpanel_user>/virtualenv/jimcan/<python_version>/bin/activate && python manage.py clearsessions > /dev/null 2>&1
```

### Manual Purge via SSH / Terminal
```bash
python manage.py clearsessions
```

---

## 2. Unlocking Accounts After Brute-Force Lockout (`django-axes`)

When a user or IP address triggers 5 consecutive failed login attempts, `django-axes` enforces a 30-minute lockout. If an employee legitimately locked themselves out, an Owner can manually unlock them.

### Method A: Via Command Line (Recommended)
From the application root in cPanel Terminal / SSH:

1. **Unlock a specific username**:
   ```bash
   python manage.py axes_reset -u <username>
   ```

2. **Unlock a specific IP address**:
   ```bash
   python manage.py axes_reset -i <ip_address>
   ```

3. **Reset all active lockouts**:
   ```bash
   python manage.py axes_reset
   ```

### Method B: Via Admin Portal (When `ENABLE_ADMIN=True`)
1. Enable admin temporarily via environment variable: `ENABLE_ADMIN=True`.
2. Sign in to the custom admin path.
3. Navigate to **Axes > Access Attempts** or **Access Logs**.
4. Select the user's failed attempts and choose **Delete selected access attempts**.
5. Once complete, revert `ENABLE_ADMIN=False`.

---

## 3. Pre-Release Password Hasher Verification

Before opening the production system to real users on Namecheap:

1. SSH into the Namecheap server.
2. Run the hashing benchmark script in the production virtual environment:
   ```bash
   python scripts/hash_benchmark.py
   ```
3. Verify that:
   - Peak memory per hash stays under **25 MB** (well within Namecheap's 1GB process limit).
   - Compute duration per hash is between **150 ms and 600 ms**.

---

## 4. Audit Chain Operations & Maintenance (Phase 3)

### 4.1 Verifying Cryptographic Chain Integrity
To recompute HMAC-SHA256 hashes across all audit rows and detect any unauthorized SQL updates or gaps:

```bash
python manage.py verify_audit_chain
```
- If the chain is clean, returns exit code 0.
- If tampering or a deleted row is detected, prints the exact sequence number and immediately sends an alert email to all active Owners.

### 4.2 Weekly Off-Site Audit Anchor (`audit_anchor`)
To detect unauthorized deletion of the newest audit rows, take a weekly snapshot of the latest sequence number and head hash:

```bash
python manage.py audit_anchor
```
**Recommended Cron Setup (cPanel):**
Configure a weekly cron job (e.g., Sundays at 04:00 UTC) that runs this command and emails the output to the Owner outside the server:
```bash
0 4 * * 0 cd /home/<cpanel_user>/jimcan && source /home/<cpanel_user>/virtualenv/jimcan/<python_version>/bin/activate && python manage.py audit_anchor
```

### 4.3 Pruning Noisy Events (`prune_noise`)
To prune high-volume `SecurityNoise` records (failed logins and 403 permission denied) older than 90 days without touching the immutable `AuditEvent` table:

```bash
# Prune entries older than 90 days (default)
python manage.py prune_noise

# Prune entries older than 60 days
python manage.py prune_noise --days=60
```
**Recommended Cron Setup:**
Schedule quarterly or monthly cleanup in cPanel Cron:
```bash
0 2 1 * * cd /home/<cpanel_user>/jimcan && source /home/<cpanel_user>/virtualenv/jimcan/<python_version>/bin/activate && python manage.py prune_noise > /dev/null 2>&1
```

