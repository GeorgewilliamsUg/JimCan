# Jimcan Operations Dashboard: Engineering Handoff & Implementation Guide

**Document:** `docs/design/handoff.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`flows.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/flows.md)
- [`data-contracts.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/data-contracts.md)
- [`qa-checklist.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/qa-checklist.md)

---

## 1. Engineering Handoff Principles

1. **Strict Fidelity to Design Specifications:** Engineers must implement templates, styles, and interactions matching the tokens, states, and responsive rules defined in this documentation system.
2. **HTML Over The Wire Architecture:** Keep business logic in Python/Django services. Front-end code consists of semantic Django templates, Tailwind utility classes, HTMX attributes, and targeted Alpine.js scripts.
3. **Never Guess Unspecified Behavior:** If an edge case, tax calculation, or error condition is unaddressed, log it as an issue referencing [`open-questions.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/open-questions.md).

---

## 2. Template Structure & Naming Conventions

### 2.1 Directory Organization
Templates follow a strict modular layout:

```
templates/
├── base.html                      # Root HTML shell, meta tags, fonts, asset links
├── layouts/
│   ├── app_shell.html             # Authenticated shell (desktop sidebar + mobile top bar)
│   └── auth_shell.html            # Minimal unauthenticated shell (login, reset)
├── components/                    # Reusable atomic UI partials
│   ├── _button.html
│   ├── _input.html
│   ├── _status_chip.html
│   ├── _kpi_card.html
│   ├── _modal.html
│   ├── _field_errors.html
│   └── _table_empty.html
├── leads/
│   ├── list.html                  # S-20: Full page view
│   ├── detail.html                # S-21: Full page view
│   └── partials/
│       ├── _lead_table.html       # HTMX swappable table
│       ├── _lead_row.html         # HTMX swappable individual row
│       └── _activity_feed.html
├── projects/
│   ├── list.html                  # S-40
│   ├── detail.html                # S-41
│   └── tabs/
│       ├── _overview_tab.html
│       ├── _boq_tab.html
│       └── _files_tab.html
├── invoices/
├── expenses/
└── tax/
```

### 2.2 Template Inclusion Conventions
- **Full Views:** Extend the appropriate layout: `{% extends "layouts/app_shell.html" %}`.
- **Partials:** File names must be prefixed with an underscore `_` (e.g. `_lead_row.html`).
- **Context Passing:** Always pass explicit arguments to reusable component includes:
  ```html
  {% include "components/_button.html" with label="Add Lead" variant="primary" icon="plus" %}
  ```

---

## 3. Tailwind CSS & Token Consumption Rules

1. **Forbidden Practices:**
   - No raw hex codes (e.g. `style="background: #16181C"`).
   - No arbitrary Tailwind bracket values where a token exists (e.g. avoid `bg-[#F26A1B]`; write `bg-safety`).
2. **Standard Class Mapping:**
   - Backgrounds: `bg-bone` (canvas), `bg-white` (card), `bg-charcoal` (sidebar/dark), `bg-safety` (primary action).
   - Borders: `border border-line` (standard containers).
   - Typography: `font-display` (Big Shoulders), `font-sans` (Instrument Sans), `font-mono` (Geist Mono).
   - Figures: `font-mono tabular-nums text-right`.

---

## 4. HTMX Integration Best Practices

### 4.1 Safe Request Targeting
Every HTMX request must explicitly declare its target and swap mode:
```html
<form hx-post="{% url 'expenses:create' %}"
      hx-target="#expense-form-container"
      hx-swap="outerHTML"
      hx-indicator="#saving-spinner">
  {% csrf_token %}
  ...
  <button type="submit" class="bg-safety text-white ...">
    <span id="saving-spinner" class="htmx-indicator spinner-sm mr-2"></span>
    Submit Expense
  </button>
</form>
```

### 4.2 Handling Validation Failures
- On invalid form POST, Django view returns HTTP 422 with the re-rendered form partial.
- Configure HTMX globally in `base.html` to swap on HTTP 422:
  ```html
  <script>
    document.body.addEventListener('htmx:beforeSwap', function(evt) {
      if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
      }
    });
  </script>
  ```

---

## 5. Alpine.js Boundary Rules

Alpine.js is strictly reserved for client-side DOM toggles:
- **Permitted Uses:** Modal open/close state (`x-data="{ open: false }"`), mobile sidebar drawer open/close, dropdown menus, and local offline `IndexedDB` photo queue handling.
- **Forbidden Uses:** Performing server data mutations, parsing complex business logic, or replacing Django forms. If an action needs server data, use HTMX.

---

## 6. Accessibility & Keyboard Implementation Checklist

- [ ] Every form input has an associated `<label for="[id]">`.
- [ ] Modals implement focus trapping and restore focus on close.
- [ ] Keyboard navigation displays visible focus ring: `focus-visible:ring-2 focus-visible:ring-safety focus-visible:ring-offset-2`.
- [ ] Toast alerts and table fragment swaps announce via `aria-live="polite"`.
- [ ] Touch targets are at least 44 × 44px on mobile viewports.

---

## 7. Developer Pre-Pull Request Checklist

Before submitting a pull request, the developer must verify:
- [ ] Tests pass: `python manage.py test`.
- [ ] Code coverage is maintained or increased.
- [ ] No unformatted numbers: all monetary values use the `money` filter (yielding Geist Mono tabular numerals with `UGX` prefix).
- [ ] Negative amounts formatted with brackets: `(UGX 500,000)`.
- [ ] Double-submission is prevented on all buttons.
- [ ] No new console errors in browser developer tools.
- [ ] Responsive behavior verified on both 360px mobile viewport and 1440px desktop.

---

## 8. Change Log
- **24 October 2026 (v0.1):** Engineering handoff guide compiled covering Django templates, Tailwind tokens, HTMX, Alpine, and PR checklists.

*Unresolved items must not be treated as approved requirements.*
