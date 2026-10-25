# Jimcan Operations Dashboard: Accessibility Specification (WCAG 2.1 AA)

**Document:** `docs/design/accessibility.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Design Brief.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`responsive.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/responsive.md)
- [`qa-checklist.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/qa-checklist.md)

---

## 1. Conformance Target & Scope

The **Jimcan Operations Dashboard** commits to achieving **WCAG 2.1 Level AA** compliance across all responsive viewports (360px to 1920px). Construction operations software must remain fully accessible to individuals with visual impairments, motor challenges, and low-contrast conditions encountered on bright, outdoor building sites.

---

## 2. Semantic HTML & Landmark Architecture

Every template must utilize native HTML5 structural landmarks:

```html
<div class="min-h-screen bg-bone">
  <!-- Desktop / Mobile Header Landmark -->
  <header role="banner" class="bg-charcoal text-white"> ... </header>

  <div class="flex">
    <!-- Navigation Landmark -->
    <nav role="navigation" aria-label="Main Navigation" class="w-64 bg-charcoal"> ... </nav>

    <!-- Main Content Landmark -->
    <main role="main" id="main-content" class="flex-1 p-8" tabindex="-1">
      <header class="mb-6">
        <h1 class="text-4xl font-display font-bold text-charcoal">Projects Overview</h1>
      </header>
      <!-- Content Sections -->
    </main>
  </div>
</div>
```

### 2.1 Heading Hierarchy Rules
- Strictly one `<h1>` element per page, containing the primary screen title.
- Section cards use `<h2>`; interior card groups use `<h3>`. Skipping heading levels (e.g. `<h1>` followed by `<h4>`) is forbidden.
- Skip to Content link is the very first focusable element on every page:
  ```html
  <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-safety focus:text-white focus:rounded-md">
    Skip to main content
  </a>
  ```

---

## 3. Keyboard Navigation & Focus Management

All features operable by mouse must be 100% operable via keyboard alone.

### 3.1 Focus Visibility
- Default browser outlines are removed only when replaced with the standardized focus ring:
  ```css
  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-safety focus-visible:ring-offset-2
  ```
- Contrast of the focus indicator against both dark charcoal and light bone backgrounds is guaranteed.

### 3.2 Focus Trapping & Restoration in Modals
When opening dialogs (e.g., `S-73` Payment Modal, `S-22` New Lead Modal):
1. Focus is captured and transferred to the first focusable element inside the dialog.
2. Keyboard `Tab` and `Shift+Tab` loop exclusively within the modal container.
3. Pressing `Escape` closes the modal immediately.
4. On close, focus is programmatically restored to the trigger button that launched the modal.

---

## 4. Forms, Labels & Error Announcements

1. **Explicit Label Association:** Every input, select, and textarea must have a linked `<label for="[id]">`. Using `placeholder` as a label substitute is prohibited.
2. **Help Text Linking:** Explanatory copy must link via `aria-describedby`:
   ```html
   <label for="wht-rate" class="block text-sm font-semibold text-charcoal">Withholding Tax (%)</label>
   <input id="wht-rate" type="text" aria-describedby="wht-hint wht-error" aria-invalid="true" class="border-danger ..." />
   <p id="wht-hint" class="text-xs text-muted">Standard rate in Uganda is 6% for designated agents.</p>
   <p id="wht-error" class="text-xs text-danger" role="alert">Enter a numeric percentage between 0 and 100.</p>
   ```
3. **Form Error Summary:** Forms with multiple errors render a high-contrast alert box at the top with clickable anchor links focusing each invalid field.

---

## 5. Live Regions & HTMX Announcements

Because the system relies on HTMX for dynamic fragment updates without full page reloads, screen reader users must be notified of asynchronous events.

### 5.1 Toast & Flash Alerts
```html
<div id="toast-container" aria-live="polite" aria-atomic="true" class="fixed top-4 right-4 z-50">
  <!-- Swapped HTMX toast renders here -->
  <div role="status" class="bg-go text-white px-4 py-3 rounded-md shadow-sm">
    Lead converted to Project #JC-PRJ-2026-012 successfully.
  </div>
</div>
```

### 5.2 Filter & Table Swaps
When an HTMX filter swaps table rows (`hx-target="#leads-table"`), an invisible live region announces:
```html
<div class="sr-only" aria-live="polite" id="table-announcer">
  Filter applied. Showing 14 matching leads.
</div>
```

---

## 6. Accessible Data Visualizations & Charts

Chart.js canvas elements (`<canvas>`) are inherently inaccessible to screen readers. For every chart:

1. The canvas element receives `role="img"` and an informative `aria-label`:
   ```html
   <canvas id="cashflow-chart" role="img" aria-label="Monthly Cash Flow bar chart for 2026. Money in: UGX 420M, Money out: UGX 310M. Net positive: UGX 110M."></canvas>
   ```
2. A companion accessible HTML table is provided immediately following the canvas or accessible via an accordion toggle:
   ```html
   <details class="mt-2 text-xs text-muted">
     <summary class="cursor-pointer hover:underline">View cash flow data as table</summary>
     <table class="w-full mt-2 text-left"> ... </table>
   </details>
   ```

---

## 7. Color Independence & Contrast Guarantees

1. **Color Independence:** Statuses and badges never convey meaning by color alone. Every badge pairs a background color with an explicit textual label and an SVG icon:
   - *Paid:* Green background + text "PAID" + checkmark icon.
   - *Overdue:* Red background + text "OVERDUE" + exclamation icon.
   - *Draft:* Bone background + text "DRAFT" + pencil icon.
2. **High-Contrast Targets:**
   - Body copy (Charcoal on White/Bone): ≥ **15.7 : 1** (Exceeds WCAG AAA).
   - Secondary labels (Muted on White): ≥ **4.6 : 1** (Passes WCAG AA).
   - Large buttons & headings: ≥ **3.2 : 1** (Passes WCAG AA large text).

---

## 8. Mobile Accessibility & Touch Ergonomics

- **Minimum Touch Target:** All interactive controls, table row action buttons, and pagination triggers must have a minimum bounding box of **44 × 44 CSS pixels**.
- **Input Mode Optimization:** Form inputs trigger native mobile keypads:
  - Money fields: `inputmode="decimal"` or `inputmode="numeric"`.
  - Phone fields: `type="tel" inputmode="tel"`.
  - Email fields: `type="email"`.
- **Zoom & Scalability:** Viewport metadata explicitly allows pinch-to-zoom up to 300% without horizontal scroll clipping:
  `<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">`.

---

## 9. Reduced Motion

For users with vestibular disorders or motion sensitivity, all transitions and animations are suppressed:
```css
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 10. Automated & Manual QA Verification Process

1. **Automated Audits:** Playwright test suite executes `@axe-core/playwright` on all 47 screens; zero critical or serious accessibility violations permitted.
2. **Keyboard Traversal Test:** Tab navigation tested end-to-end through every workflow without mouse intervention.
3. **Screen Reader Testing:** Tested with NVDA (Windows) and VoiceOver (macOS / iOS Safari) to verify reading order, table announcements, and live-region alerts.

---

## 11. Open Questions Relevant to Accessibility
1. `[OQ-11]`: Confirmation of outdoor tablet screen brightness settings vs high-contrast theme toggle requirement.

---

## 12. Change Log
- **24 October 2026 (v0.1):** Initial WCAG 2.1 AA accessibility specification compiled.

*Unresolved items must not be treated as approved requirements.*
