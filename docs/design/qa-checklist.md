# Jimcan Operations Dashboard: Quality Assurance & Release Gate Checklist

**Document:** `docs/design/qa-checklist.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Product Requirements Document %28PRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Product%20Requirements%20Document%20%28PRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`states.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/states.md)
- [`accessibility.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/accessibility.md)

---

## 1. Quality Gates & Definitions of Done

### 1.1 Definition of Design Complete
A feature or screen design is signed off as complete only when:
1. Canonical Screen ID (`S-xx`) and responsive layout (mobile & desktop) are fully specified.
2. All 20 UI states (loading, empty, error, offline, locked, extreme numbers) are accounted for.
3. Contrast ratios meet WCAG 2.1 Level AA (≥ 4.5:1 normal text, ≥ 3.0:1 UI boundaries).
4. Data contracts and permissions are defined without backend speculation.
5. All open questions are logged and linked in [`open-questions.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/open-questions.md).

### 1.2 Definition of Implementation Complete
A feature slice is accepted into production only when:
1. Playwright automated end-to-end smoke tests pass without failure.
2. All financial calculations (BOQ markups, VAT 18%, WHT 6%, invoice balances) match source truth to the exact shilling.
3. Django permissions strictly forbid unauthorized URL access with HTTP 403.
4. Mobile usability verified on a physical smartphone (touch targets ≥ 44px, offline photo queue functions).
5. Code coverage meets or exceeds 80% across business and calculation services.

---

## 2. Release Verification Checklists

### 2.1 Visual Design & Token Fidelity
- [ ] No raw hex values exist in templates; all styles consume Tailwind semantic tokens (`charcoal`, `safety`, `brass`, `bone`, `line`, `go`, `danger`).
- [ ] Exactly one primary affirmative button (`bg-safety`) appears per screen canvas.
- [ ] Cards have 1px borders in `line` (`#E3DED3`) and zero drop shadows.
- [ ] Card corners are 12px (`rounded-lg`); button and input corners are 8px (`rounded-md`).
- [ ] Big Shoulders Bold is used for `h1` titles; Instrument Sans for UI copy; Geist Mono for all currencies and dates.

### 2.2 Financial Calculation & Math Reconciliation
- [ ] **Currency Uniformity:** Every money value is prefixed with `UGX` in Geist Mono with `tabular-nums`.
- [ ] **Negative Formatting:** Negative values render in brackets `(UGX 1,500,000)`, never with a minus sign.
- [ ] **BOQ Math:** Section totals strictly equal the sum of line items; Grand Total equals Net Subtotal + Overheads + Profit + VAT (18%).
- [ ] **Invoice Balance:** Balance Due = Gross Invoice Amount - Cumulative Payments - WHT Deducted.
- [ ] **VAT Calculation:** Exactly 18% applied to net taxable supplies; zero rounding discrepancies across invoice lines.
- [ ] **WHT Calculation:** Exactly 6% deducted at source on client payments where applicable.

### 2.3 Responsive & Hardware Viewports
- [ ] **360px Mobile (Portrait):** No horizontal layout overflow; off-canvas navigation functions smoothly.
- [ ] **44px Touch Targets:** Every button, table action, and input meets the 44×44px minimum bounding box.
- [ ] **Tablet (768px):** Two-column card grids collapse cleanly without text clipping.
- [ ] **Desktop (1280px+):** Fixed 260px sidebar is persistent; main canvas padding is 32px.
- [ ] **iOS Safe Area:** Fixed bottom action bars respect `env(safe-area-inset-bottom)`.

### 2.4 Accessibility & WCAG AA Verification
- [ ] Page passes automated `@axe-core/playwright` audit with zero violations.
- [ ] Skip to Main Content link is first focusable element on every page.
- [ ] Visible focus ring (`ring-2 ring-safety ring-offset-2`) appears on all keyboard-focused controls.
- [ ] Modal dialogs trap focus and close upon pressing `Escape`; focus restores to trigger on close.
- [ ] All inputs have associated `<label for="...">` and error descriptions via `aria-describedby`.
- [ ] Chart.js visualizations provide accessible fallback data tables via `<details>` accordion.

### 2.5 Security, RBAC & State Robustness
- [ ] Navigating to unauthorized URLs as `Site Engineer` or `Accountant` returns clean HTTP 403 (`S-03`).
- [ ] Site Engineers cannot inspect client pricing, project profit margins, or company financial statements.
- [ ] CSRF tokens (`{% csrf_token %}`) are present on every mutating form.
- [ ] Double-submitting forms is physically impossible; buttons disable immediately upon click.
- [ ] Soft-deleted records are hidden from standard queries and flagged with `is_deleted = true`.
- [ ] Issued invoices and locked BOQs cannot be edited; fields are read-only.

### 2.6 Performance & Offline Behavior
- [ ] Initial HTML page payload < 100 KB gzipped.
- [ ] HTMX partial fragment swaps complete in < 300ms on simulated 3G connection.
- [ ] Disconnecting internet displays top amber offline banner without crashing active forms.
- [ ] Site progress photos captured offline queue locally in `IndexedDB` and sync automatically upon reconnection.
- [ ] Large uploaded images are auto-compressed via Pillow (stripping EXIF metadata, max width 2000px).

---

## 3. Defect Classification & Severity Rules

| Severity Level | Definition | Release Blocking? | Remediation SLA |
|---|---|---|---|
| **Blocker (P0)** | Financial calculation error, tax discrepancy, security bypass, data corruption, or crash on primary path. | **YES** | Fix immediately; stop release. |
| **Major (P1)** | Broken workflow without workaround, failed offline sync, missing permission check, critical layout collapse. | **YES** | Fix before production deployment. |
| **Minor (P2)** | Cosmetic misalignment, microcopy typo, minor chart legend glitch, non-critical accessibility warning. | NO | Fix in subsequent patch sprint. |
| **Cosmetic (P3)**| Minor whitespace variance, subtle hover state color discrepancy. | NO | Track in product backlog. |

---

## 4. Evidence Recording Template

```markdown
### QA Verification Record: [Feature / Slice Name]
- **Date:** [YYYY-MM-DD]
- **Tester / Agent:** [Name]
- **Commit SHA / Version:** [Hash]
- **Test Environment:** Local / Staging

#### Results Summary:
- [x] Visual tokens verified against design-system.md
- [x] Math reconciled to exact shilling
- [x] Mobile 360px viewport tested
- [x] Keyboard navigation and screen reader checked
- [x] Role permission boundaries tested (Admin, Manager, Engineer, Accountant)
- [x] Axe-core accessibility audit: 0 violations

#### Defects Discovered:
- None. Ready for production gate.
```

---

## 5. Open Questions Relevant to QA
1. `[OQ-15]`: Confirm whether automated cross-browser testing in CI should include WebKit / Safari via Playwright or Chromium only.

---

## 6. Change Log
- **24 October 2026 (v0.1):** Initial release gate and QA verification matrix compiled based on PRD Section 4 and TRD Section 13.

*Unresolved items must not be treated as approved requirements.*
