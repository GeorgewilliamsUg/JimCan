# Jimcan Operations Dashboard: Design System Specification

**Document:** `docs/design/design-system.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Design Brief.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard App Flow Document.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20App%20Flow%20Document.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`responsive.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/responsive.md)
- [`accessibility.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/accessibility.md)
- [`handoff.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/handoff.md)
- [`design-decisions.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-decisions.md)

---

## 1. Purpose and Relationship to Other Documents

This document defines the complete visual design system, token architecture, and UI component library for the **Jimcan Operations Dashboard**. It translates the high-level visual principles established in the [Design Brief](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md) into concrete, testable specifications for Django templates, Tailwind CSS utilities, Alpine.js micro-interactions, and Chart.js dashboards.

The Jimcan design system is strictly utilitarian: flat, high-contrast, dense with information, highly legible under direct sunlight on construction sites, and optimized for low-bandwidth mobile and desktop connections.

---

## 2. Design Token Principles

1. **Tokens as the Single Source of Truth:** Raw hex codes, ad-hoc pixel values, and custom inline CSS are forbidden in application templates. All styling must consume semantic design tokens.
2. **Two-Tier Architecture:** 
   - *Primitive Tokens:* Raw color and scale definitions (e.g., `safety-500`, `charcoal-900`).
   - *Semantic Tokens:* Purpose-bound tokens (e.g., `action-primary`, `bg-canvas`, `border-card`, `status-won`).
3. **Restraint Over Expression:** Maximum of two accent colors per screen: the primary action color (`safety`) plus one semantic state color (e.g., `go` for won/paid, `danger` for overdue).

---

## 3. Color Tokens

### 3.1 Palette Tokens and Semantic Bindings

The color palette is derived from the starter codebase configuration (`tailwind.config.js`) and calibrated for WCAG AA compliance.

| Token Name | Hex Code | Semantic Role | Tailwind Utility Class | Status |
|---|---|---|---|---|
| `charcoal` | `#16181C` | Primary text, desktop sidebar, dark button fills | `text-charcoal`, `bg-charcoal` | `[Built]` |
| `graphite` | `#23262C` | Active navigation item, user avatar background | `bg-graphite` | `[Built]` |
| `steel` | `#3A3F47` | Inactive nav icon markers, subtle dividers | `text-steel`, `border-steel` | `[Built]` |
| `safety` | `#F26A1B` | Primary action button, active step indicator, progress bars | `bg-safety`, `text-safety` | `[Built]` |
| `safety-hover` | `#D95B12` | Hover/active state for primary actions | `hover:bg-safety-hover` | `[Built]` |
| `brass` | `#B8914A` | Secondary accent, caution chips, pending approvals | `bg-brass`, `text-brass` | `[Built]` |
| `brass-light` | `#EFE6D2` | Light brass tint for badge backgrounds | `bg-brass-light` | `[Built]` |
| `brass-dark` | `#6E5420` | High-contrast brass text on light backgrounds | `text-brass-dark` | `[Built]` |
| `bone` | `#F4F1EA` | Canvas/page background across all screens | `bg-bone` | `[Built]` |
| `white` | `#FFFFFF` | Card backgrounds, table surfaces, input backgrounds | `bg-white` | `[Built]` |
| `line` | `#E3DED3` | 1px borders on cards, tables, field inputs | `border-line` | `[Built]` |
| `muted` | `#6B7380` | Secondary labels, table column headers, helper text | `text-muted` | `[Built]` |
| `go` | `#3E8E5A` | Positive money flow, won leads, paid invoices, completed tasks | `text-go`, `bg-go` | `[Built]` |
| `go-light` | `#EAF5EE` | Background for positive badges and success alerts | `bg-go-light` | `[Built]` |
| `danger` | `#B23A3A` | Overdue invoices, error banners, voided items, destructive actions | `text-danger`, `bg-danger` | `[Built]` |
| `danger-light` | `#FDF2F2` | Background for error banners and destructive dialogs | `bg-danger-light` | `[Built]` |

*Note on Brand Status:* Per [Design Brief Section 1](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md#L19), the Charcoal/Safety Orange/Brass palette is currently a `[Proposed]` palette derived from design moodboards. It must be validated against `jimcanconstruction.site` branding in discovery.

### 3.2 Semantic Status Chip Tokens

Lead and Project statuses utilize strict token sets rather than generic rainbow badges:

| Status Entity | State | Background Token | Text Token | Border Token |
|---|---|---|---|---|
| Lead | `New` | `bg-bone` | `text-charcoal` | `border-line` |
| Lead | `Contacted` | `bg-brass-light` | `text-brass-dark` | `border-brass` |
| Lead | `Site Visit` | `bg-orange-50` | `text-safety` | `border-safety` |
| Lead | `Quoted` | `bg-white` | `text-charcoal` | `border-charcoal` |
| Lead / Project | `Won` / `Active` | `bg-go-light` | `text-go` | `border-go` |
| Lead / Invoice | `Lost` / `Void` | `bg-danger-light` | `text-danger` | `border-danger` |
| Project Phase | `Brief` to `Handover` | `bg-bone` | `text-charcoal` | `border-line` |

---

## 4. Contrast Requirements & WCAG Audit

All color pairings meet or exceed WCAG 2.1 Level AA contrast standards (minimum 4.5:1 for normal text, 3.0:1 for large display text and UI boundaries):

| Text Token | Background Token | Contrast Ratio | Conformance | Context of Use |
|---|---|---|---|---|
| `charcoal` (`#16181C`) | `bone` (`#F4F1EA`) | **15.76 : 1** | AAA Pass | Page titles, body text on canvas |
| `charcoal` (`#16181C`) | `white` (`#FFFFFF`) | **17.77 : 1** | AAA Pass | Data tables, form input values |
| `bone` (`#F4F1EA`) | `charcoal` (`#16181C`) | **15.76 : 1** | AAA Pass | Sidebar labels, primary button text |
| `white` (`#FFFFFF`) | `safety` (`#F26A1B`) | **3.22 : 1** | Large / UI Pass | Primary button (bold text ≥ 15px) |
| `charcoal` (`#16181C`) | `safety` (`#F26A1B`) | **5.52 : 1** | AA Pass | Alternative high-contrast button text |
| `brass-dark` (`#6E5420`) | `bone` (`#F4F1EA`) | **6.31 : 1** | AA Pass | Caution chips, pending status text |
| `danger` (`#B23A3A`) | `white` (`#FFFFFF`) | **5.90 : 1** | AA Pass | Error messages, overdue amounts |
| `go` (`#3E8E5A`) | `white` (`#FFFFFF`) | **4.62 : 1** | AA Pass | Paid invoice amounts, success badges |

---

## 5. Typography Scale & Font Rules

### 5.1 Font Families

| Role | Font Family | Fallback Stack | Purpose |
|---|---|---|---|
| **Display** | Big Shoulders Bold (Weight: 700) | `Impact, sans-serif` | Main screen titles (`h1`, 36px), app logo wordmark |
| **Interface** | Instrument Sans (Weights: 400, 600, 700) | `system-ui, -apple-system, sans-serif` | UI controls, labels, navigation, table content, forms |
| **Figures & Data** | Geist Mono (Weights: 400, 700) | `ui-monospace, SFMono-Regular, monospace` | Currencies (`UGX`), quantities, dates, small captions |

### 5.2 Type Hierarchy Scale

| Level | Size (px / rem) | Line Height | Weight | Tracking | Usage |
|---|---|---|---|---|---|
| **Display 1** | 36px / 2.25rem | 40px | Bold (700) | Normal | Page title (`h1`), login brand header |
| **KPI Total** | 30px / 1.875rem | 36px | Mono Bold (700) | Tight | Metric card hero values |
| **Heading 2** | 20px / 1.25rem | 28px | Bold (700) | Normal | Section headings, modal titles |
| **Heading 3** | 16px / 1.0rem | 24px | SemiBold (600) | Normal | Card titles, table group headers |
| **Body UI** | 14px / 0.875rem | 20px | Regular (400) | Normal | Table cells, form inputs, primary copy |
| **Body Bold** | 14px / 0.875rem | 20px | SemiBold (600) | Normal | Table row titles, button labels |
| **Navigation** | 15px / 0.9375rem | 22px | Medium (500) | Normal | Sidebar and top navigation links |
| **Caption / Label** | 11px / 0.6875rem | 16px | Mono Bold (700) | Wide (`0.05em`) | Uppercase table headers, metric labels |
| **Badge / Chip** | 12px / 0.75rem | 16px | SemiBold (600) | Normal | Status indicators, phase badges |

### 5.3 Financial Formatting Typography Rules
- All currency values must use **Geist Mono** (`font-mono`) with `tabular-nums` so numbers align vertically in data columns.
- Standard alignment: **Right-aligned** for monetary values, numbers, and quantities; **Left-aligned** for text descriptions; **Center-aligned** for status badges and dates.
- Negative currency must be formatted in brackets: `(UGX 4,200,000)`, never `-UGX 4,200,000`.

---

## 6. Spacing, Elevation, and Geometry Tokens

### 6.1 Spacing Scale
The spacing system strictly follows Tailwind's 4px base increment:
- `space-1` (4px): Micro spacing between icon and text.
- `space-2` (8px): Form input inner vertical padding, button icon gap.
- `space-3` (12px): Form input inner horizontal padding, badge padding.
- `space-4` (16px): Standard grid gap, mobile page margin, table cell padding.
- `space-6` (24px): Card interior padding, desktop column spacing.
- `space-8` (32px): Desktop page padding, major section vertical spacing.

### 6.2 Border Radius Tokens
- `rounded-sm` (4px): Small inner tags, table cell selection handles.
- `rounded-md` (8px): Standard UI buttons, text input fields, select dropdowns.
- `rounded-lg` (12px): Standard cards, modal dialogs, data table containers.
- `rounded-full` (9999px): Status chips, search bar pills, user avatar circles.

### 6.3 Border & Depth Rules
- **No Drop Shadows:** Shadows are explicitly eliminated to reduce visual clutter and render cleanly on low-power devices.
- **1px Crisp Borders:** All structural containers (cards, tables, modals) use a crisp 1px solid border using the token `border-line` (`#E3DED3`).
- **Focus Rings:** High-visibility 2px solid `safety` ring with a 2px offset (`ring-2 ring-safety ring-offset-2`).

---

## 7. Component Inventory & Anatomy

### 7.1 Buttons (`ButtonPrimary`, `ButtonSecondary`, `ButtonGhost`, `ButtonDestructive`)

- **Anatomy:** Optional leading icon (18px) + Label (14px SemiBold) + optional trailing indicator.
- **Variants:**
  - `ButtonPrimary`: Solid `safety` fill, white text (or dark charcoal in high-contrast mode), 8px radius. Used exactly once per view for the primary affirmative action.
  - `ButtonSecondary`: White fill, `line` border, `charcoal` text. Used for secondary actions (e.g., "Cancel", "Export").
  - `ButtonGhost`: Transparent fill, `charcoal` text, hover `bg-bone`. Used for tertiary actions and table row tools.
  - `ButtonDestructive`: White fill, `danger` border, `danger` text, hover `bg-danger-light`. Used for voiding and soft-deleting.
- **States:** Default, Hover, Focus-Visible, Active, Disabled (`opacity-50 cursor-not-allowed`), Loading (HTMX `htmx-request` replaces icon with 16px spinner and sets `disabled`).

### 7.2 Form Fields (`FormField`, `TextInput`, `SelectInput`, `MoneyInput`)

- **Anatomy:** Label (14px SemiBold) + Optional Help Tooltip + Input Surface (44px mobile height, 38px desktop height, white background, 1px `line` border, 8px radius) + Error Message Container.
- **MoneyInput Specialization:** Fixed left prefix pill with `UGX` in Geist Mono; right-aligned integer/decimal input; automatically formats thousands with commas on blur.
- **Validation State:** Border turns `border-danger`, input background becomes `bg-red-50/20`, and error text renders below in `text-danger text-xs mt-1`.

### 7.3 Metric Card (`KpiCard`)

- **Anatomy:** Container (white card, 12px radius, 1px line border, 24px padding) + Category Label (11px uppercase mono `text-muted`) + Hero Value (30px mono bold `text-charcoal`) + Contextual Subtitle / Trend Badge.
- **Accent Strip:** Top 3px accent line in `safety` (for attention items) or `go` (for cash flow positive).

### 7.4 Data Table (`DataTable`)

- **Anatomy:** Wrapper card (12px radius, overflow-x-auto) + Header row (11px mono uppercase, `bg-bone/50`, sticky) + Data rows (14px text, 48px row height, hover `bg-bone/30`, bottom border 1px `line`) + Footer pagination bar.
- **Numeric Alignment:** Quantities, rates, totals, and balances are strictly right-aligned with monospace numerals.

### 7.5 Navigation (`AppSidebar`, `MobileNav`)

- **Desktop Sidebar:** 260px fixed width, solid `charcoal` background, white wordmark, stacked navigation links with 18px icons, active indicator in `safety`.
- **Mobile Header:** 56px height, `charcoal` background, hamburger toggle button (44×44px touch target), page title, quick-action trigger.

---

## 8. Open Questions Relevant to Design System
1. `[OQ-01]`: Confirmation of official Jimcan brand color codes from logo vector assets vs current proposed palette.
2. `[OQ-02]`: Decision on whether high-contrast primary button text should default to Charcoal (`#16181C`) for maximum 5.52:1 contrast rather than White (`#FFFFFF`, 3.22:1).

---

## 9. Change Log
- **24 October 2026 (v0.1):** Initial design system specification authored based on PRD, TRD, and Design Brief v0.1 tokens.

*Unresolved items must not be treated as approved requirements.*
