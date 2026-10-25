# Jimcan Operations Dashboard: Design Brief

Version 0.1 (draft for review) | 24 October 2026 | Author: George | Companion to PRD, TRD and App Flow v0.1

## 1. Purpose, and how to trust this brief

This brief defines how the dashboard looks, feels and behaves: minimal, intentional, quick, and complete enough to run a construction business from a phone or a desk.

Every statement is labelled so nothing is guessed:

- **\[Built\]** exists in the starter project and was checked in the code or in a rendered screenshot (desktop 1500 px wide, phone 390 px wide).
- **\[Measured\]** a number I calculated or measured from the actual files.
- **\[Decision\]** a design choice proposed here that needs your or Jimcan's approval.
- **\[Not built\]** specified here, not yet in the starter, and therefore not tested.
- **\[Open\]** unknown. Needs an answer from Jimcan before it is final.

**What has not been verified:** the BOQ builder, forms other than the filter bar, modals, PDFs and print output, behaviour on a real phone outdoors, and any real Jimcan brand material. The starter has only a dashboard, an expenses list, a login page and placeholder pages.

**One correction up front \[Open\]:** the orange, charcoal and brass palette comes from my inspiration board. I did not check it against Jimcan's real logo or website. Section 4 treats it as a proposal until you confirm their brand colours.

## 2. Design in one page

1. **Numbers come first.** Money and quantities are the hero: big, mono, right aligned.
2. **One main action per screen,** in orange. Everything else is quiet.
3. **Colour carries meaning, not decoration.** Orange means act or progress, green means good, red means problem, brass means caution or secondary.
4. **Flat and light.** Thin borders, no shadows, no gradients, no icons that do not help.
5. **Fast is a feature.** Server rendered pages, small assets, no layout jumps, skeleton states.
6. **Same thing, same look, everywhere.** A shared component for every repeated pattern.
7. **Phone for capture, desktop for editing.** Photos, expenses and approvals are phone first. BOQ building and statements are desktop first, and still readable on a phone.

## 3. Experience goals and measurable "quick"

| Goal | How it is judged |
| --- | --- |
| Quick to learn | A new manager records an expense in under 2 minutes with no training |
| Quick to use | Most common tasks in 5 taps or clicks or fewer (App Flow checklist) |
| Quick to load | Under 4 seconds on 3G for main screens (PRD) |
| Calm | No more than one primary button and one accent colour block per screen area |
| Trustworthy | Every total can be traced, nothing important is hidden behind hover |

## 4. Visual language

### 4.1 Colour tokens \[Built\], values from tailwind.config.js

| Token | Hex | Used for |
| --- | --- | --- |
| charcoal | #16181C | Sidebar, primary text, login background |
| graphite | #23262C | Active nav item, user chip |
| steel | #3A3F47 | Inactive nav markers, dark buttons |
| safety (orange) | #F26A1B | Primary button, active marker, progress bars, KPI accent |
| brass | #B8914A, light #EFE6D2, dark #6E5420 | Secondary accent, caution states, avatar |
| bone | #F4F1EA | Page background |
| white | #FFFFFF | Cards and fields |
| line | #E3DED3 | Card and table borders |
| muted | #6B7380 | Secondary text, labels |
| go (green) | #3E8E5A | Positive, completed |
| danger (red) | #B23A3A | Overdue, errors |

**Rules**

- Maximum two accents on any one screen: orange plus one status colour.
- Raw hex never appears in templates. Only tokens do \[Built, except chart JS which repeats hex values and should read the tokens, Decision\].
- Lead pipeline chips currently use Tailwind's default sky, amber, violet colours \[Built\]. That adds colours outside the brand. **\[Decision\]** replace with a small semantic set: neutral (New), brass (Contacted), orange (Site visit), charcoal outline (Quoted), green (Won), red (Lost).

### 4.2 Typography \[Built\]

| Role | Family | Where |
| --- | --- | --- |
| Display | Big Shoulders Bold | Page titles (text-4xl), logo wordmark |
| Interface | Instrument Sans 400 and 700 | Everything readable: nav, tables, forms, buttons |
| Figures and labels | Geist Mono 400 and 700 | All money, dates in tables, small uppercase labels, KPI values |

Sizes in use \[Built\]: page title 36 px, KPI value 30 px mono bold, card title 16 px bold, body and table 14 px, nav 15 px, small labels 11 px mono uppercase with wide tracking, chips 12 px bold.

**Rules**

- Money is always mono, right aligned, with `tabular-nums`, so digits line up in columns.
- Negative money shows in brackets, for example (9,800,000) \[Built in the `money` filter\].
- Large totals use "UGX" as a smaller muted prefix, and millions as 184.2M on cards only. Tables and documents always show the full figure \[Built for cards, rule for tables is Decision\].
- Body text never goes below 14 px. The 11 px labels are for short uppercase captions only.

### 4.3 Spacing, shape, depth \[Built\]

- Spacing follows Tailwind's 4 px scale. Card padding 24 px, grid gaps 16 or 24 px, page padding 16 px on phone and 32 px from 640 px up.
- Corners: cards 12 px, buttons and fields 8 px, chips and search pill fully round.
- Depth: none. Borders are 1 px in the line colour. No shadows anywhere in the starter.
- Motion: only the sidebar slide on phones and colour changes on hover. **\[Decision\]** add `prefers-reduced-motion` handling and keep any future motion under 200 ms.

## 5. Accessibility and contrast audit \[Measured\]

Contrast ratios below were calculated from the exact hex values using the WCAG formula. Targets: 4.5 to 1 for normal text, 3 to 1 for large text and for the edges of controls and meaningful graphics.

| Pair (where used in the starter) | Ratio | Verdict |
| --- | --- | --- |
| Charcoal text on bone | 15.76 | Pass |
| Charcoal text on white | 17.77 | Pass |
| Bone text on charcoal | 15.76 | Pass |
| Nav text (slate-400) on charcoal | 6.93 | Pass |
| Brass dark on bone (brass chips) | 6.31 | Pass |
| Danger red on white / on bone | 5.90 / 5.23 | Pass |
| Muted on white (card subtitles, mono labels) | 4.78 | Pass |
| **Muted on bone** (page subtitle under the title) | **4.24** | **Fail** for normal text |
| **White text on orange** (primary buttons) | **3.06** | **Fail** at 14 px bold |
| **Orange text on white** ("View all" link) | **3.06** | **Fail** |
| **Orange text on bone** ("Due 15 Nov" chip) | **2.72** | **Fail** |
| **Green text on bone** ("+2 this quarter" chip) | **3.57** | **Fail** |
| Brass on white | 2.92 | Decoration only, never text |
| Field border (line colour) on white | 1.34 | **Fail** for control edges (needs 3) |
| Orange bar vs white (progress, KPI accent) | 3.06 | Pass for graphics |

### Proposed fixes \[Decision\], with their measured results

| Problem | Fix | New ratio |
| --- | --- | --- |
| Primary button text | Charcoal text on the brand orange (keeps the exact brand colour) | 5.80 (hover #EA580C: 4.99) |
| Orange used as text | New token `safety-text` #C2410C | 5.18 on white, 4.59 on bone |
| Green used as text | New token `go-text` #2F7A4A | 5.25 on white, 4.65 on bone |
| Muted text on bone | Darken muted to #5B6270 | 5.43 on bone, 6.13 on white |
| Field border | #8B8F96 for inputs and selects | 3.25 on white |
| Brass | Never used as text. Use brass dark for text | 6.31 |

Orange stays bright for bars, markers and filled areas. Only text and button labels change.

### Other accessibility gaps found by reading the code \[Built, gaps\]

- Present: visible focus rings on buttons and fields, `aria-current` on the active nav item, `role="progressbar"` with values, labelled search and menu button, `role="img"` and a label on the chart.
- Missing: a "skip to content" link, `aria-expanded` on the menu button, focus trapping and Escape to close in the phone sidebar, a text or table alternative for the chart, reduced motion support, and form error association (`aria-describedby`) for the forms not yet built.
- Status is never colour alone: chips and KPI notes always carry words. Keep this rule.

## 6. Layout system

### 6.1 Shell \[Built\]

- **Desktop (1024 px and up):** fixed 240 px charcoal sidebar, fluid content, title and actions in a top row, content in cards.
- **Phone and tablet (under 1024 px):** sidebar becomes a slide in drawer opened by a menu button, with a dimmed backdrop.
- Content width is fluid with no maximum. **\[Decision\]** cap reading heavy pages (forms, settings) at about 960 px, and let tables and reports use the full width.

### 6.2 Grids \[Built\]

| Element | Phone | 640 px and up | 1280 px and up |
| --- | --- | --- | --- |
| KPI cards | 1 column | 2 columns | 4 columns |
| Chart and phase card | Stacked | Stacked | 3 to 2 split |
| Tables | Scroll sideways inside the card | Same | Full width |

### 6.3 What the phone screenshot showed \[Measured from the 390 px render\]

- Four KPI cards stack in one column, each roughly 125 to 145 px tall, so they use about 600 px before any chart appears.
- The title wraps the date line onto two lines beside the orange button but remains readable.
- **\[Decision\]** On phones show KPI cards as a compact 2 by 2 grid with smaller value text, so the chart and attention items appear on the first screen.

### 6.4 Touch targets (calculated from class values, not yet measured in a browser)

- Buttons about 40 px tall, fields about 42 px, nav links about 46 px, menu button about 36 px.
- **\[Decision\]** raise every tappable control on phones to at least 44 px high. WCAG 2.2's minimum is 24 px, so the starter passes the minimum but misses the comfort target for gloved or outdoor use.

## 7. Component library

| Component | Status | Specification |
| --- | --- | --- |
| Sidebar and nav | Built | Charcoal, active item has graphite fill and an orange left bar |
| Top bar | Built | Title, one line subtitle, search pill (desktop wide only), one primary action |
| KPI card | Built | Label (mono caps), value (mono), note chip, coloured left bar |
| Card | Built | White, 1 px line border, 12 px radius |
| Progress bar | Built | 8 px high, orange, brass or green, with ARIA values |
| Data table | Built | Mono caps headers, row dividers, hover tint, totals row, numbers right aligned |
| Filter bar with live results | Built | Search plus select, results swap without reload |
| Buttons | Built | Primary (orange), outline (brass border), dark (steel) |
| Text field and select | Built | White, 8 px radius, orange focus ring |
| Status chip | Built | Pill, 12 px bold, colour plus word |
| Alert message | Built | Green success, red error, bold text |
| Login screen | Built | Charcoal page, one card, one button |
| Empty state | Built inside the table only | **\[Decision\]** make it a shared component: one sentence plus one action |
| Form field wrapper | Not built | Label, field, hint, error, all linked for screen readers |
| Modal and confirm dialog | Not built | Names the consequence, asks for a reason where the PRD requires, focus trapped |
| Toast | Not built | Bottom of screen, success auto hides in 4 seconds, errors stay |
| Pagination | Not built | 25 rows, previous and next, page count |
| Tabs (project hub) | Not built | Underlined tabs, scroll on phone, URL driven |
| Notification bell and list | Not built | Count badge, list with read state |
| Offline banner | Not built | Slim brass bar, text explains uploads will send later |
| File uploader with queue | Not built | Camera first, thumbnails with Waiting, Sending, Sent states |
| Date and number inputs | Not built | Native date input, numeric keypad for money on phones |
| BOQ grid | Not built | See 8.1 |
| Document preview (quote, invoice) | Not built | See 9 |
| Style guide page | Not built | **\[Decision\]** a `/styleguide/` page that renders every component, used as the living reference |

Button rules: one orange button per area. Destructive actions use a red outline, never orange. Disabled buttons look disabled and say why on hover or tap.

## 8. Key screen specifications \[Not built, proposals\]

### 8.1 BOQ builder (most important screen)

- **Header:** project name, BOQ name, version chip (Draft or Locked), actions: Save state, Lock version, Export. Totals stay visible in a sticky bar.
- **Body:** collapsible sections, each with a subtotal. Row columns: item number, description, unit, quantity, rate, amount. Numeric columns mono and right aligned, amount is read only.
- **Entering items:** a search box that finds rate library items as you type. Enter adds the item and moves the cursor to quantity. Tab moves across, Enter moves down, so a whole BOQ can be typed without the mouse.
- **Totals panel:** subtotal, contingency, overheads and profit, VAT, total, in the exact calculation order from the PRD, with each line clickable to change its percentage while drafting.
- **Views:** a toggle between Internal (cost and margin) and Client (prices only), clearly labelled so the wrong one is never sent by mistake.
- **Locked state:** orange to brass banner reading "Locked. Create a new version to edit", all inputs read only.
- **Phone:** review and approve only. Items appear as stacked cards with the amount large. Editing on phone is possible but not optimised.

### 8.2 Expense entry (phone first)

Camera or file first, then amount, supplier, project, category, payment method. Defaults filled (today, last used project). Save button fixed at the bottom within thumb reach. Large numeric keypad for amount.

### 8.3 Site photo upload (phone first)

Big capture tile, thumbnails below with a clear status per photo, a phase chip selector, caption, one Upload button, and a waiting counter that stays visible after leaving the screen.

### 8.4 Invoice and payment

Invoice detail shows status chip, balance in large mono, payments list with WHT lines, and the single next action (Issue, Record payment, or Send reminder).

### 8.5 Reports and statements

Period and basis selectors at top (cash or accrual shown on every report), table first, chart second. Every figure is a link to its source rows. Negative values in brackets, totals rows bold with a top border.

### 8.6 Tax summary

A data quality panel comes first (problems to fix), then the VAT and withholding summary, then export and Mark as filed. Filed periods show a locked banner.

### 8.7 Leads

List by default with status chips and an overdue marker. A board view is a later option. A lead page puts contact details and the next follow up at the top, activity log below.

## 9. Documents and print (PDF) \[Not built\]

- A4 portrait, 20 mm margins, page numbers, company logo and details from settings, TIN and VAT numbers in the header.
- Black and white friendly: no colour required to read it. Orange appears only as a thin accent line.
- Table style matches the app: mono figures right aligned, section rows shaded in brass light, total block at the bottom right.
- Fonts embedded in the PDF. Whether Big Shoulders is used for headings in PDFs is a **\[Decision\]**.
- Quote and invoice carry numbers, dates with the year, validity or due date, payment details, terms and a clear statement of tax treatment.
- Client view of a BOQ never contains cost or margin fields.
- Not tested yet: how ReportLab renders these on the Namecheap host (TRD spike 2).

## 10. Content and microcopy

- Plain and short. Verbs on buttons: "Issue invoice", "Record payment", "Lock version".
- Terms: use BOQ, VAT and WHT. Spell out the first use on a screen, and add a short hint on hover or tap.
- Errors say what happened and what to do: "Amount is higher than the invoice balance. Check the amount or mark it as an overpayment."
- Empty states say what the screen is for and offer the first action.
- Dates: tables show "22 Oct" \[Built\]. **\[Decision\]** anything that can span years (reports, exports, documents, history) shows the year.
- Money: "UGX 4,250,000" in text, bare figures in table columns with the currency in the header \[Built\].
- Tone: respectful and direct. No exclamation marks, no jokes in errors.

## 11. Responsiveness and device behaviour

| Task | Primary device | Notes |
| --- | --- | --- |
| Upload photos, update phase | Phone | Offline queue, big targets |
| Record expense, approve expense | Phone and desktop | Short forms, defaults |
| Review leads, follow ups | Phone and desktop | Call and email links are tappable |
| Build BOQ, quote, invoice | Desktop | Keyboard driven grid |
| Reports, tax, statements | Desktop | Wide tables, export |
| Settings, users | Desktop | Forms capped at readable width |

Tables on phones scroll sideways inside their card. Key columns (name and amount) stay first. **\[Decision\]** for lists used on phones (expenses, leads) switch to stacked cards below 640 px instead of sideways scrolling. Not yet tested on a real phone \[Open\].

Dark mode is **out of scope for the MVP**. Sites are used in bright sunlight, and one well tested light theme costs less to build and verify.

## 12. Performance design budget

### 12.1 What the starter weighs \[Measured\]

| Asset | Size | Compressed (gzip) |
| --- | --- | --- |
| CSS (all styles, minified) | 17.9 KB | 4.0 KB |
| HTMX | 50.9 KB | 16.4 KB |
| Alpine | 44.8 KB | 16.2 KB |
| Chart.js (dashboard only) | 205.6 KB | 69.6 KB |
| App script | 1.0 KB | 0.6 KB |
| Fonts, five TTF files together | 387 KB | not compressed |

Dashboard script and style transfer is about 107 KB gzipped, and non chart pages about 37 KB. This is inside the TRD budget of 150 KB, provided the files are actually compressed.

### 12.2 Things to fix to make it quick \[Decision\]

1. **Compression is not configured.** The starter uses WhiteNoise without its compressed storage setting, so files are probably sent uncompressed. Switch to WhiteNoise's compressed manifest storage, then re-measure.
2. **Fonts are the heaviest items.** Convert the five TTF files to WOFF2 and subset to Latin, then re-measure. Do not assume the saving, check it.
3. Keep preloading only Instrument Sans Regular \[Built\]. Load the bold and mono weights without preload.
4. Chart.js stays loaded only on pages with charts \[Built\]. For the dashboard, consider loading it after first paint.
5. Reserve space for charts and images so nothing jumps \[Built for the chart height\].
6. Photos: compress to about 1 MB before upload (TRD), show thumbnails not originals in galleries.

## 13. Brand and asset inputs needed from Jimcan \[Open\]

- Logo files (vector if possible) and any brand colours or fonts
- Screenshots or link of their current website, to match or intentionally differ
- Company details for documents: legal name, address, phone, TIN, VAT number, bank and mobile money details
- Two or three of their real past quotes, BOQs and invoices, to match layout and wording
- Standard terms, exclusions and payment terms
- Preferred document language and tone

Until these arrive, the palette and the "J" logo mark in the starter are placeholders.

## 14. Design deliverables and quality gates

1. Living style guide page with every component and state
2. Mockups only where the starter does not already show the pattern (BOQ builder, expense form, upload screen, statements, PDFs). Figma free tier or direct HTML
3. Screenshots at 390 px and 1440 px for each finished screen, stored in the repo
4. Contrast check re-run after the token changes in section 5
5. Real phone test on a throttled connection for J8 (App Flow)
6. Review with two real users (one manager, one engineer) before each module is called done

**Design definition of done:** uses only shared components and tokens, has all five states (loading, empty, error, no permission, offline), passes contrast, works at 390 px and 1440 px, and meets the touch target rule.

## 15. Open questions

1. Does Jimcan have a logo and brand colours? Does their website use the orange and charcoal palette?
2. Do you accept the proposed contrast fixes, mainly charcoal text on orange buttons?
3. Phone KPI cards: 2 by 2 compact grid, or keep one column?
4. Stacked cards on phones for lists, or sideways scrolling tables?
5. Should PDFs use Big Shoulders for headings or a plainer system look?
6. Should the pipeline use the reduced colour set in 4.1?
7. Is English the only interface language, or is Luganda needed later?
8. Who will test on real phones on site?

## 16. Approvals

| Name | Role | Decision | Date |
| --- | --- | --- | --- |
|  | Jimcan owner or director |  |  |
|  | Jimcan project manager |  |  |
| George | Developer and designer |  |  |
