# Two-Factor Authentication (MFA) Staged Rollout Plan

This document details the three-stage operational rollout strategy for Two-Factor Authentication (MFA) on the Jimcan Operations Dashboard.
The rollout prevents account lockouts and validates recovery mechanisms before broad enforcement.

---

## 1. Rollout Overview & Control Switch

MFA enforcement is governed by the environment variable:

```bash
MFA_ENFORCEMENT=off|owners|all
```

- **Default in Production:** `all` (fail-secure).
- **Default in Local Development:** `off`.
- **Startup Visibility:** The active mode is evaluated and recorded into the append-only cryptographic audit chain on every application initialization with event `mfa_enforcement_mode`. Any unauthorized or quiet downgrade is permanently recorded.
- **Verification:** Run `python manage.py security_status`. In production (`DEBUG=False`), it outputs `[WARN]` unless the mode is `all`.

---

## 2. The Three Rollout Stages

```
   ┌───────────────────────┐
   │ Stage 1: Optional     │ MFA_ENFORCEMENT=off
   │ Setup live & opt-in   │
   └──────────┬────────────┘
              │ Verified staging enrollment & recovery
              ▼
   ┌───────────────────────┐
   │ Stage 2: Owners       │ MFA_ENFORCEMENT=owners
   │ Required for Owners   │
   └──────────┬────────────┘
              │ Both active Owners test login & recovery
              ▼
   ┌───────────────────────┐
   │ Stage 3: Everyone     │ MFA_ENFORCEMENT=all
   │ Universal enforcement │
   └───────────────────────┘
```

### Stage 1: Setup Pages Live & Optional (`MFA_ENFORCEMENT=off`)
- **Objective:** Deploy two-factor endpoints (`/two_factor/setup/`, `/login/`, backup recovery codes) without blocking unverified users.
- **User Experience:**
  - Users continue logging in with their password normally.
  - Users can voluntarily navigate to their Account Security profile (`/two_factor/`) to pair an authenticator app (e.g., Google Authenticator, Aegis) and generate 10 static backup recovery codes.
- **Prerequisites to Exit Stage 1:**
  1. Both active Owners pair their authenticators and verify successful TOTP code validation.
  2. Both active Owners store their 10 static backup recovery codes in a secure password manager.
  3. Staging drills confirm that login, backup token consumption, and device resets work as intended.

---

### Stage 2: Mandatory for Owners (`MFA_ENFORCEMENT=owners`)
- **Objective:** Enforce MFA on high-privilege administrative accounts (`Owner` group) before enforcing on field staff.
- **Configuration:** Set `MFA_ENFORCEMENT=owners` in the server environment and restart the application.
- **User Experience:**
  - Any user in the `Owner` group who signs in must verify a 6-digit TOTP code or backup code.
  - If an Owner attempts to browse any dashboard route without a verified factor, `MFAEnforcementMiddleware` redirects them immediately to 2FA enrollment or verification.
  - Non-owner roles (Project Managers, Engineers, Accountants) remain on standard authentication during this stage.
- **Prerequisites to Exit Stage 2:**
  1. At least two active Owner accounts exist and have tested independent recovery.
  2. One Owner tests resetting another user's device via `ResetUserMFAView` (requiring step-up re-authentication).
  3. Server command `python manage.py reset_mfa <username>` is verified by operations staff in terminal/SSH.
  4. Both Owners sign off that no workflow disruption or lockout occurred for 7 consecutive days.

---

### Stage 3: Universal Mandatory Enforcement (`MFA_ENFORCEMENT=all`)
- **Objective:** Full production state. Every authenticated user must verify with a password and an authenticator code.
- **Configuration:** Set `MFA_ENFORCEMENT=all` (or omit to accept production default).
- **User Experience:**
  - All users (Owners, Managers, Engineers, Accountants) must provide a 6-digit authenticator code or single-use backup token upon login.
  - Any authenticated user without an enrolled device is redirected to `/two_factor/setup/`.
  - Brand new accounts setting their password via one-time link are redirected immediately to 2FA enrollment.
  - Accounts pending enrollment for > 72 hours are automatically deactivated by `python manage.py expire_pending_accounts`.
- **Compliance:**
  - `python manage.py security_status` reports `[PASS]` for MFA enforcement.
  - Django Admin (if enabled via `ENABLE_ADMIN=True`) is protected behind `AdminSiteOTPRequiredMixin` and unreachable without a verified second factor.

---

## 3. Account Recovery & Contingency Runbook

1. **Lost Authenticator Device (Normal User):**
   - The user contacts an Owner.
   - The Owner performs step-up re-authentication in the user management interface and triggers `ResetUserMFAView`.
   - All active sessions for the user are immediately terminated, and the user enrolls a new device on next login.
2. **Lost Authenticator Device (Owner):**
   - **Primary Path:** Use one of the 10 static backup recovery codes saved during enrollment.
   - **Secondary Path:** Another active Owner resets the device via user management. (Hence the strict rule: at least two active Owners must exist).
   - **Emergency Path:** Operator with SSH access runs `python manage.py reset_mfa <username>`.
3. **Emergency Rollback:**
   - If an unexpected critical bug blocks authentication across the company, change `MFA_ENFORCEMENT=off` in the environment and restart the application.
   - This deployment action records `mfa_enforcement_mode: off` in the tamper-evident audit log and alerts all Owners.
