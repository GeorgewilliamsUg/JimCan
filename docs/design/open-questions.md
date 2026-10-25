# Jimcan Operations Dashboard: Open Questions & Decisions Registry

**Document:** `docs/design/open-questions.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Design Brief.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Product Requirements Document %28PRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Product%20Requirements%20Document%20%28PRD%29.md)
- [`design-decisions.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-decisions.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)

---

## 1. Purpose & Registry Guidelines

This document tracks all unresolved commercial, technical, visual, and operational decisions for the Jimcan Operations Dashboard. No feature marked with an open question may be treated as final or implemented without resolving its blocking status.

---

## 2. Canonical Open Questions

### `[OQ-01]`: Official Brand Palette & Logo Assets Reconciliation
- **Category:** Brand & Visual Identity
- **Question:** Does Jimcan Construction approve the proposed Charcoal (`#16181C`), Safety Orange (`#F26A1B`), and Brass (`#B8914A`) color system, or does their existing website/brand guide require alternate hex values?
- **Why It Matters:** Design tokens, CSS variables, and PDF templates depend on this. Design Brief Section 1 explicitly marked the palette as an unverified proposal from an inspiration board.
- **Affected Screens / Files:** `design-system.md`, `design-decisions.md` (D-02), all PDF document templates.
- **Options:**
  - *Option A (Recommended):* Keep proposed Charcoal/Safety Orange palette if it aligns with construction visibility.
  - *Option B:* Re-sample exact brand colors from `jimcanconstruction.site` production assets.
- **Decision Owner:** Jimcan Director / George
- **Due Date:** Phase 0 (Design Tokens Gate)
- **Blocking Status:** Non-blocking for layout structure; blocking for final CSS freeze.
- **Current Status:** Open / Proposed.

---

### `[OQ-02]`: Namecheap Shared Hosting Python Environment & MySQL Driver Limits
- **Category:** Infrastructure & Hosting
- **Question:** Does the Namecheap shared hosting cPanel environment support Python 3.10+, and can `PyMySQL` / `mysqlclient` compile cleanly in the virtual environment?
- **Why It Matters:** TRD Section 5.1 marks this as **VERIFY Spike 1**. If shared hosting memory limits or C-compiler restrictions break the app, the hosting architecture must pivot to a low-cost VPS.
- **Affected Screens / Files:** TRD Section 17, `settings.py`.
- **Options:**
  - *Option A:* Confirm shared hosting Passenger deployment via hello-world spike.
  - *Option B:* Pivot immediately to a $6/month Hetzner or DigitalOcean Linux VPS.
- **Recommendation:** Run the Spike 1 deployment test before writing business models.
- **Decision Owner:** George
- **Due Date:** Week 1 / Spike 1
- **Blocking Status:** Blocking for production deployment setup.
- **Current Status:** Open / Pending Spike.

---

### `[OQ-03]`: Multi-Currency Requirement (USD vs UGX)
- **Category:** Financial & Commercial Rules
- **Question:** Does Jimcan quote, bill, or procure any materials in United States Dollars (USD), or are 100% of transactions denominated in Ugandan Shillings (UGX)?
- **Why It Matters:** PRD Section 6 assumes UGX only for MVP. If USD is required for specific commercial contracts or imported materials, currency fields and exchange-rate tracking must be added to `Backend Schema Document.md`.
- **Affected Screens / Files:** `S-60` (BOQ), `S-70` (Invoices), `Backend Schema Document.md`.
- **Options:**
  - *Option A (Recommended for MVP):* Enforce single currency (UGX whole shillings).
  - *Option B:* Add currency dropdown with manual exchange-rate conversion on quotes.
- **Decision Owner:** Jimcan Management
- **Due Date:** Discovery Interview
- **Blocking Status:** Non-blocking for MVP unless USD billing is an active reality.
- **Current Status:** Assumed UGX Only / Open for Confirmation.

---

### `[OQ-04]`: Withholding Tax (WHT) Deductions Application Rules
- **Category:** Uganda Tax Compliance
- **Question:** Are all client invoices subject to 6% Withholding Tax deduction, or only designated large corporate/government clients?
- **Why It Matters:** Affects the invoice payment recording modal (`S-73`) and accounts receivable aging. If WHT is optional per client, a `is_wht_designated` flag must exist on `Client`.
- **Affected Screens / Files:** `S-71`, `S-73`, `S-88` (Tax Summary).
- **Options:**
  - *Option A (Recommended):* Include a per-payment WHT toggle with 6% default and manual override.
  - *Option B:* Set WHT status at the Client profile level.
- **Decision Owner:** Jimcan Accountant / Director
- **Due Date:** Phase 8 (Invoicing)
- **Blocking Status:** Non-blocking for base invoice creation.
- **Current Status:** Open / Proposed.

---

### `[OQ-05]`: Digital Client Acceptance of Quotations
- **Category:** Workflow & Legal
- **Question:** How does Jimcan formally record client acceptance of a Quote? Does it require a client digital signature pad, an email confirmation upload, or a simple manual status toggle by the Manager?
- **Why It Matters:** Affects `S-62` Quote Detail screen complexity and client interaction flows.
- **Options:**
  - *Option A (Recommended):* Simple manual status toggle: `Mark Accepted` with file upload for signed contract PDF.
  - *Option B:* Public web link where clients sign via touchscreen.
- **Decision Owner:** George / Jimcan Management
- **Due Date:** Phase 6 (Quotes)
- **Blocking Status:** Non-blocking.
- **Current Status:** Proposed Option A.

---

### `[OQ-06]`: Site Photo Storage Volume & Quota Management
- **Category:** Storage & Performance
- **Question:** What is the anticipated monthly volume of high-resolution site progress photos and CAD drawings, and does it fit within Namecheap's disk quota?
- **Why It Matters:** Shared hosting disk quotas range from 20GB to unmetered with strict file count (inode) limits. Unchecked 12-megapixel phone photo uploads will exhaust quotas rapidly.
- **Affected Screens / Files:** `S-47`, `S-90`, TRD Section 11.
- **Options:**
  - *Option A (Recommended):* Enforce aggressive Pillow compression (max 2000px, quality 85%, strip EXIF) bringing image size to ~400KB.
  - *Option B:* Offload media storage to an external S3-compatible bucket (e.g. Cloudflare R2 / Backblaze B2).
- **Decision Owner:** George
- **Due Date:** Week 2 (Storage Setup)
- **Blocking Status:** Non-blocking initially; crucial before field rollout.
- **Current Status:** Proposed Option A.

---

### `[OQ-07]`: Standard Document Numbering Taxonomy
- **Category:** Operational Standards
- **Question:** What is Jimcan's preferred document numbering structure for invoices, quotes, and projects?
- **Why It Matters:** Affects database auto-numbering sequences (`S-95`).
- **Options:**
  - *Option A (Proposed):* `JC-INV-YYYY-XXXX` (e.g., `JC-INV-2026-0001`), `JC-QUO-YYYY-XXXX`, `JC-PRJ-XXXX`.
  - *Option B:* Simple integer counters: `INV-1001`, `QUO-1001`.
- **Decision Owner:** Jimcan Management
- **Due Date:** Discovery
- **Blocking Status:** Non-blocking.
- **Current Status:** Proposed Option A.

---

### `[OQ-08]`: Namecheap SMTP Hourly Sending Limits
- **Category:** Email & Notifications
- **Question:** What are the exact hourly and daily SMTP sending limits on the Namecheap hosting account?
- **Why It Matters:** Outbox notifications for leads, overdue invoice reminders, and password resets must not exceed host limits to prevent email blacklisting.
- **Affected Screens / Files:** TRD Section 12, `outbox/models.py`.
- **Recommendation:** Implement a database outbox queue that throttles dispatch to max 30 emails per hour.
- **Decision Owner:** George
- **Due Date:** Week 1 Spike
- **Blocking Status:** Non-blocking for local dev.
- **Current Status:** Pending Host Verification.

---

## 3. Change Log
- **24 October 2026 (v0.1):** Canonical open questions registry created across brand, hosting, tax, multi-currency, and storage.

*Unresolved items must not be treated as approved requirements.*
