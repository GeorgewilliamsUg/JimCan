# Jimcan Operations Dashboard: Responsive & Cross-Device Specification

**Document:** `docs/design/responsive.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Design Brief.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`accessibility.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/accessibility.md)

---

## 1. Supported Viewports & Breakpoint Strategy

The Jimcan Dashboard supports three distinct operational device classes:
1. **Field Mobile (360px – 480px):** Site Engineers and Foremen on mid-range Android and iOS smartphones on active building sites. Focus: quick photo capture, phase progression, expense submission.
2. **Site Office Tablet (768px – 1024px):** Project Managers reviewing drawings, approving expenses, and inspecting site progress.
3. **Office Desktop / Laptop (1280px – 1920px):** Directors, Quantity Surveyors, and Accountants handling detailed BOQ generation, progress invoicing, tax filing, and financial statements.

### 1.1 Tailwind Breakpoints
| Breakpoint | Minimum Width | Typical Hardware Target | Layout Characteristics |
|---|---|---|---|
| `base` | 360px | Mobile Phone (Portrait) | Single-column, off-canvas nav, sticky bottom actions |
| `sm` | 640px | Large Phone (Landscape) | 2-column grid, compact table view |
| `md` | 768px | iPad / Android Tablet (Portrait) | 2-column forms, collapsible sidebar, multi-stat cards |
| `lg` | 1024px | iPad Pro / Small Laptop | Persistent sidebar option, full data tables |
| `xl` | 1280px | Standard Laptop (13"–15") | Fixed 260px sidebar, 4-card metric rows, side-by-side BOQ |
| `2xl` | 1536px+ | Large Desktop Monitor | Max container width 1600px centered with balanced gutters |

---

## 2. Shell & Layout Transformations

### 2.1 Desktop Shell (`lg` and above)
- **Sidebar:** Fixed 260px width, `bg-charcoal`, 100vh height, `overflow-y-auto`.
- **Top Utility Bar:** 64px height, contains global search, sync indicator, notification bell, and user profile chip.
- **Main Canvas:** `flex-1`, padding 32px (`p-8`), `bg-bone`.

### 2.2 Mobile Shell (below `lg`)
- **Top Bar:** 56px height, sticky top (`sticky top-0 z-40 bg-charcoal text-white px-4`), containing hamburger menu button (44×44px target), Jimcan wordmark, and current page title.
- **Off-Canvas Navigation Drawer:** Slides in from left using Alpine.js (`x-show="openSidebar"`), with a high-contrast dark overlay (`bg-charcoal/80 backdrop-blur-sm`). Focus is trapped within drawer while open; `Escape` or tapping backdrop dismisses drawer.
- **Canvas Padding:** 16px horizontal padding (`px-4 py-6`) on `bg-bone`.

---

## 3. Component & Layout Responsive Patterns

### 3.1 Data Tables vs Mobile Card Lists
Large construction data tables (e.g., Invoices, Leads, Rate Items) become illegible if simply shrunk. Two responsive transformations are enforced:

1. **Card List Transformation (Leads `S-20`, Expenses `S-75`):**
   - *Desktop:* 7-column table with right-aligned currencies.
   - *Mobile (`< md`):* Hidden `<table>`; rendered as stacked cards:
     ```html
     <div class="block md:hidden space-y-3">
       <div class="bg-white border border-line rounded-lg p-4">
         <div class="flex justify-between items-start">
           <span class="font-bold text-charcoal">Munyonyo Villa</span>
           <span class="badge-go text-xs">Won</span>
         </div>
         <p class="text-xs text-muted mt-1">Residential Build • Kampala</p>
         <div class="mt-3 flex justify-between items-center text-sm font-mono">
           <span class="text-muted text-xs">ESTIMATE</span>
           <span class="font-bold text-charcoal">UGX 450,000,000</span>
         </div>
       </div>
     </div>
     ```

2. **Horizontal Table Scroll with Sticky Primary Column (BOQ `S-60`, Tax `S-86`):**
   - Tables that require multi-column cross-calculation maintain horizontal scroll (`overflow-x-auto`) with the item description column sticky on the left:
     ```css
     .sticky-col { position: sticky; left: 0; background-color: #FFFFFF; z-index: 10; }
     ```

### 3.2 Form Grid Layouts
- **Desktop:** Multi-column structured grids (e.g. `grid grid-cols-12 gap-6`). Labels on top, inputs spanning 4 to 6 columns.
- **Mobile:** All fields collapse strictly to full-width single column (`w-full`), field height minimum 44px for touch ergonomics.

### 3.3 Sticky Mobile Action Bar
On complex capture screens (`S-76` Expense Entry, `S-47` Photo Upload), the primary affirmative action button sticks to the bottom of the viewport with safe-area padding:
```html
<div class="fixed bottom-0 left-0 right-0 bg-white border-t border-line p-4 md:hidden z-30 pb-[max(1rem,env(safe-area-inset-bottom))]">
  <button type="submit" class="w-full h-12 bg-safety text-white font-bold rounded-md flex items-center justify-center">
    Submit Expense
  </button>
</div>
```

### 3.4 Modal Dialogs vs Mobile Bottom Sheets
- **Desktop:** Centered dialog window (max-w-lg, 12px radius, centered via flex).
- **Mobile (`< sm`):** Transitions into a **Bottom Sheet** anchored to the bottom of the screen (`fixed bottom-0 inset-x-0 rounded-t-xl max-h-[90vh] overflow-y-auto`), facilitating one-handed thumb interaction.

### 3.5 Horizontal Scroll Tabs
On mobile devices, navigation tabs (`S-41` Project Tabs) do not wrap into messy multi-lines; they scroll horizontally with touch momentum and hidden scrollbars:
```css
.tabs-scroll { display: flex; overflow-x: auto; white-space: nowrap; -webkit-overflow-scrolling: touch; }
```

---

## 4. Charts & Financial Visualizations

Chart.js canvas containers dynamically adapt their aspect ratios:
- **Desktop:** Fixed 320px height with fluid width (aspect ratio ~ 3:1).
- **Mobile Phone:** Aspect ratio 16:9 (height ~ 200px) with reduced gridlines and simplified date axis labels (e.g. `Jan`, `Feb`, instead of `January 2026`).

---

## 5. Responsive Review Checklist

Before signing off on any template implementation:
- [ ] No horizontal viewport scrolling occurs on a 360px wide screen.
- [ ] All touch targets (buttons, links, form inputs) are ≥ 44 × 44px on mobile.
- [ ] Sticky bottom action bars respect `env(safe-area-inset-bottom)` on iOS.
- [ ] Desktop sidebar collapses cleanly into an accessible slide-over drawer on screens < 1024px.
- [ ] Large monetary figures line wrap cleanly or scale font size without clipping container boundaries.

---

## 6. Open Questions Relevant to Responsive
1. `[OQ-12]`: Determine whether Site Engineers require an app-like Home Screen PWA manifest icon for one-tap mobile browser launching.

---

## 7. Change Log
- **24 October 2026 (v0.1):** Responsive layout rules, breakpoints, and mobile transformation patterns compiled.

*Unresolved items must not be treated as approved requirements.*
