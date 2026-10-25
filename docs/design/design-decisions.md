# Jimcan Operations Dashboard: Architectural & Design Decision Records (ADR)

**Document:** `docs/design/design-decisions.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Design Brief.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`open-questions.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/open-questions.md)

---

## 1. Decision Authority & Status Conventions

Every record in this registry is tagged with its formal status:
- **`[Approved]`**: Formally accepted by the project owner/lead and confirmed in foundational project documents.
- **`[Proposed]`**: Recommended design choice currently under review. Must not be treated as final.
- **`[Unknown]`**: Under exploration; pending discovery interview or technical spike.

---

## 2. Architectural & Design Decisions

### `D-01`: Technology Architecture: Django Monolith on Shared Hosting
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** The system must run within strict cost constraints: Namecheap cPanel shared hosting (Passenger + Apache), zero ongoing SaaS subscriptions, managed by a single developer.
- **Decision:** Build a single Django 5.2 LTS monolith utilizing Django templates, WhiteNoise for static files, MySQL (InnoDB) database, HTMX 2 for dynamic fragment swaps, Alpine.js 3 for micro-interactions, and local Tailwind CSS.
- **Alternatives Rejected:** Next.js + Supabase + Vercel (rejected due to subscription costs at scale and unnecessary multi-tier complexity per TRD Section 4).
- **Reason:** Simplest, most reliable stack with built-in security, ORM, and admin batteries.
- **Affected Files:** TRD Section 4, all templates.
- **Revisit Condition:** If Namecheap hosting limits (cPanel Passenger memory/process quotas) fail spike verification (TRD Section 17), migrate code to a basic low-cost Linux VPS.

---

### `D-02`: Brand Identity & Color Palette: Charcoal, Safety Orange & Brass
- **Status:** `[Proposed]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** The starter project introduced Charcoal (`#16181C`), Safety Orange (`#F26A1B`), and Brass (`#B8914A`).
- **Proposal:** Adopt this palette as the semantic color system: Charcoal for structure/text, Safety Orange for primary actions/progress, Brass for secondary accents/caution, and Bone (`#F4F1EA`) for background.
- **Alternatives:** Neutral monochrome with blue corporate accents; standard construction yellow.
- **Reason:** Provides immediate high contrast, visual warmth, and outdoor visibility under direct sunlight on building sites.
- **Affected Files:** `design-system.md`, `tailwind.config.js`.
- **Revisit Condition:** Must be reconciled with Jimcan's actual logo and live website (`jimcanconstruction.site`) during discovery.

---

### `D-03`: Typography: Big Shoulders Bold, Instrument Sans, Geist Mono
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** Construction data requires high visual distinction between marketing headings, interface controls, and financial figures.
- **Decision:** Use Big Shoulders Bold for screen headings (`h1`), Instrument Sans for body text and navigation, and Geist Mono with `tabular-nums` for all currencies, quantities, and dates.
- **Alternatives:** Inter across all elements; system fonts only.
- **Reason:** Monospaced tabular figures prevent column jitter in financial tables and make large numbers in UGX instantly scanable.
- **Affected Files:** `design-system.md`, all templates.

---

### `D-04`: Navigation Model: Fixed Desktop Sidebar & Mobile Off-Canvas Drawer
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** Desktop users need fast multi-domain jumping between BOQs, Invoices, and Leads; mobile users need maximum screen real estate for site photos and forms.
- **Decision:** Desktop displays a persistent 260px fixed dark sidebar (`bg-charcoal`). Mobile displays a 56px sticky top bar with a slide-in off-canvas drawer controlled via Alpine.js.
- **Alternatives:** Horizontal top menu on desktop; bottom tab bar on mobile.
- **Reason:** Bottom tab bars cannot accommodate 10 domain links cleanly. Drawer provides scalable navigation.
- **Affected Files:** `responsive.md`, `templates/base.html`.

---

### `D-05`: Immutability of Issued Financial Records & Soft Deletion
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** In commercial construction, quotes and invoices are legal and tax documents. Rewriting history or dropping rows creates legal liability and tax penalty risks.
- **Decision:** 
  1. No hard deletes. Records implement soft deletion via `is_deleted` flags and `django-simple-history`.
  2. When an invoice or quote is issued, or a BOQ version is locked, all rates, totals, and client text are snapshotted onto the record. The record becomes read-only (`is_locked = true`).
  3. Corrections require an explicit revision (`BOQ v1.1`), a formal credit note, or an Admin void with recorded reason.
- **Alternatives:** In-place row editing with audit logs.
- **Reason:** Guarantees total financial auditability and compliance with Uganda Revenue Authority (URA) tax audit requirements.
- **Affected Files:** `Backend Schema Document.md`, `screens.md`, `data-contracts.md`.

---

### `D-06`: Client-Side Offline Queue for Site Engineers
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** Mobile internet signal is notoriously intermittent on Ugandan construction job sites.
- **Decision:** Implement a lightweight client-side offline queue using browser `IndexedDB` and Alpine.js. When offline, photos and expense drafts are stored locally. A background worker retries uploads when `navigator.onLine` fires.
- **Alternatives:** Full service worker PWA with complex caching; requiring engineers to wait for signal.
- **Reason:** Service worker offline caching on shared hosting adds significant complexity. Lightweight IndexedDB queue solves the 90% use case (uploading photos and field expenses) safely.
- **Affected Files:** `flows.md`, `screens.md`, `templates/projects/files.html`.

---

### `D-07`: Pure Python PDF Generation via ReportLab
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** Quotes, tax invoices, and payment receipts must be generated as downloadable PDFs on the server.
- **Decision:** Use ReportLab (pure Python) for primary PDF compilation.
- **Alternatives:** WeasyPrint (rejected because it requires shared C-libraries like Cairo and Pango which shared cPanel hosting often disallows per TRD Section 4).
- **Reason:** ReportLab installs cleanly in any Python virtualenv without root access or system library dependencies.
- **Affected Files:** TRD Section 4, `quotes/services.py`, `invoices/services.py`.

---

### `D-08`: Four-Tier Role-Based Access Control (RBAC) Model
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** Staff have drastically different responsibilities and information access needs.
- **Decision:** Implement four distinct internal roles (`Admin`, `Manager`, `Site Engineer`, `Accountant`) with server-side enforcement. Site Engineers are explicitly blocked from financial margins and statements.
- **Alternatives:** Flat permissions; 2-role system (Admin vs Staff).
- **Reason:** Prevents sensitive pricing, contractor margins, and profit data from being viewed by field labor or unauthorized staff.
- **Affected Files:** `roles-permissions.md`, `PRD Section 5`.

---

### `D-09`: Single Currency Representation (UGX Whole Shillings) for MVP
- **Status:** `[Approved]`
- **Date:** 24 October 2026
- **Owner:** George
- **Context:** Most domestic construction contracts in Uganda operate in Ugandan Shillings (UGX).
- **Decision:** Restrict the MVP to UGX represented as whole shillings in database and templates. Multi-currency (USD) is deferred to Phase 2 unless discovery confirms active USD billing.
- **Alternatives:** Multi-currency table schema from day one.
- **Reason:** Eliminates exchange rate volatility calculations, conversion rounding errors, and UI clutter in the initial release.
- **Affected Files:** `data-contracts.md`, `design-system.md`.

---

## 3. Open Questions Relevant to Decisions
1. `[OQ-01]`: Confirmation from Jimcan management on whether `[Proposed]` brand palette D-02 is officially approved.

---

## 4. Change Log
- **24 October 2026 (v0.1):** Architectural & design decision records compiled from TRD, PRD, and Design Brief.

*Unresolved items must not be treated as approved requirements.*
