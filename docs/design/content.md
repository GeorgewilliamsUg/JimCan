# Jimcan Operations Dashboard: Content, Microcopy & Terminology Standards

**Document:** `docs/design/content.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Design Brief.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Design%20Brief.md)
- [`design-system.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/design-system.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`states.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/states.md)

---

## 1. Voice and Tone Principles

The Jimcan Dashboard communicates with clarity, precision, and commercial realism. Users include construction directors, quantity surveyors, site foremen, and external accountants. The product interface must feel dependable, calm, and direct.

1. **Pragmatic & Unadorned:** State facts directly. Avoid marketing fluff, robotic jargon, and conversational filler (e.g., use *"Lead converted"* rather than *"Awesome! You successfully converted this lead!"*).
2. **Accountable & Unambiguous:** In commercial construction, every figure has legal and tax implications. Never obscure who made a change, when an action took effect, or why a calculation resolved to a specific total.
3. **Calm Under Pressure:** When errors, offline drops, or budget overruns occur, provide concise diagnostic explanations with clear, actionable remedies.

---

## 2. Capitalization & Typography Conventions

| Element | Rule | Example |
|---|---|---|
| **Document & Page Titles (`h1`)** | Title Case | *Projects Overview*, *Tax Calendar & Filings* |
| **Section Headings (`h2`, `h3`)** | Sentence case | *Recent activity*, *Invoice payment schedule* |
| **Buttons & Action Triggers** | Sentence case | *Add lead*, *Lock BOQ version*, *Record payment* |
| **Form Labels** | Sentence case | *Project location*, *Client phone number* |
| **Status Chips & Table Badges** | Title Case | *Site Visit*, *Partially Paid*, *In Progress* |
| **Table Header Captions** | ALL UPPERCASE (Mono) | `PROJECT CODE`, `NET AMOUNT (UGX)`, `STATUS` |
| **Currency & Tax Acronyms** | ALL UPPERCASE | `UGX`, `VAT`, `WHT`, `PAYE`, `NSSF`, `TIN`, `BOQ` |

---

## 3. Standardized Terminology Glossary

To prevent cognitive confusion across screens, the following commercial terms are strictly standardized:

| Concept | Approved Term | Deprecated / Rejected Synonyms | Definition |
|---|---|---|---|
| **Potential Client Opportunity** | `Lead` | Deal, Prospect, Opportunity, Enquiry | An inbound request for construction services prior to quotation. |
| **Customer Entity** | `Client` | Customer, Account, Buyer | An individual or company that has commissioned a project with Jimcan. |
| **Construction Job** | `Project` | Build, Job, Site, Contract | An active or completed construction undertaking with defined scope and budget. |
| **Bill of Quantities** | `BOQ` | Estimate, Cost Sheet, Quotation sheet | Detailed breakdown of items, quantities, and rates for construction works. |
| **Cost Catalog** | `Rate Library` | Price list, Cost book, Unit rates | Master repository of standard unit rates for labor, material, and plant. |
| **Formal Client Pricing** | `Quote` | Bid, Proposal, Estimate | Client-facing binding commercial offer derived from a locked BOQ. |
| **Billing Document** | `Invoice` | Bill, Demand note | Commercial demand for payment issued to a client. |
| **Statutory Tax Deducted** | `Withholding Tax (WHT)` | Retained tax, Advance tax | 6% income tax deducted at source by designated clients on invoice payments. |
| **Value Added Tax** | `VAT` | Sales tax, Consumption tax | 18% standard rate applied to taxable sales and claimable on business purchases. |
| **Physical Progress Stage** | `Phase` | Status, Step, Milestone | Sequential build stages: *Brief*, *Design*, *Foundation*, *Superstructure*, *Finishes*, *Handover*. |
| **Disbursement / Cost** | `Expense` | Expenditure, Outflow, Bill | Money spent on materials, site wages, plant hire, fuel, or permits. |
| **Trade Vendor** | `Supplier` | Vendor, Contractor, Seller | Company or individual supplying materials, equipment, or specialized trade work. |

---

## 4. Button & Action Label Standards

Action labels must begin with a strong, unambiguous verb:

- **Affirmative Creation:** `Add lead`, `New project`, `Create quote`, `Issue invoice`, `Record expense`.
- **Commitment & Immutability:** `Lock BOQ version`, `Issue quote`, `Issue invoice`, `Close tax period`.
- **Workflow Transitions:** `Submit for approval`, `Approve expense`, `Reject with notes`, `Convert to client`.
- **Payment & Reconciliation:** `Record payment`, `Allocate credit note`, `Reconcile WHT`.
- **Destructive & Voiding:** `Void invoice`, `Archive project`, `Soft-delete lead`. (Avoid the ambiguous word *"Delete"* without qualification).
- **Secondary Actions:** `Cancel`, `Save draft`, `Download PDF`, `Export Excel`, `Back to list`.

---

## 5. Microcopy: Alerts, Confirmations & Error Messages

### 5.1 Validation Error Messages
- *Required Field:* `[Field Name] is required.`
- *Phone Format:* `Enter a valid phone number (e.g., +256 700 000 000 or 0700 000 000).`
- *Currency Field:* `Enter a valid amount in whole Ugandan Shillings.`
- *Rate Discrepancy:* `Quantity must be greater than zero.`
- *Date Sequence:* `Target completion date cannot be earlier than project start date.`

### 5.2 Destructive Confirmation Dialogs
- **Voiding an Invoice:**  
  *Title:* `Void Invoice JC-INV-2026-004?`  
  *Body:* `This action is irreversible. The invoice will be marked Void, its balance will be reset to UGX 0, and a reversal entry will be written to the audit log. Issued document numbers cannot be reused.`  
  *Confirm Button:* `Confirm Void (Requires Reason)`  
  *Cancel Button:* `Keep Invoice Active`

- **Archiving a Project:**  
  *Title:* `Archive Project: Munyonyo Villa?`  
  *Body:* `Archived projects are hidden from active dashboards. Financial records, photos, and historical invoices remain fully intact and can be restored by an Admin at any time.`  
  *Confirm Button:* `Archive Project`

### 5.3 Offline & Sync Microcopy
- *Offline Banner:* `Working offline. Site photos and expense drafts are queued locally.`
- *Syncing:* `Syncing 3 queued items with Jimcan servers...`
- *Sync Success:* `All queued items uploaded successfully.`
- *Sync Failure:* `Could not upload 1 photo due to weak signal. Tap here to retry.`

### 5.4 Empty State Copy
- **Empty Leads (`S-20`):**  
  *Headline:* `No leads recorded yet`  
  *Body:* `Enquiries submitted on jimcanconstruction.site will appear here automatically. You can also manually record phone calls or walk-in clients.`  
  *Button:* `Add First Lead`

- **Empty BOQ Items (`S-60`):**  
  *Headline:* `This BOQ section has no line items`  
  *Body:* `Import standard items from the Rate Library or add custom materials and labor.`  
  *Button:* `Add Line Item`

---

## 6. Financial, Numerical & Date Formats

- **Currency Prefix:** Always prefix with `UGX` separated by a non-breaking space.
- **Whole Shillings:** Construction figures are tracked in whole shillings (e.g., `UGX 14,500,000`). If decimal cents occur in tax calculations, format with 2 decimals (e.g., `UGX 14,500,000.50`).
- **Dates in Tables:** `24 Oct 2026` (Geist Mono, 14px).
- **Date + Time in Audit Logs:** `24 Oct 2026, 14:32 EAT` (East Africa Time, UTC+3).
- **Quantities with Units:** `450.00 m³`, `1,200.00 kg`, `14 nr`, `1.00 item`.

---

## 7. Content Review Checklist

Before signing off on any template or generated copy:
- [ ] No placeholder copy ("Lorem ipsum", "John Doe", "test", "foo") remains.
- [ ] Every currency value includes the explicit `UGX` prefix.
- [ ] All action buttons begin with an active verb.
- [ ] Destructive actions explain consequences clearly before confirmation.
- [ ] Negative amounts are enclosed in brackets, never prefixed with a minus sign.
- [ ] Terminology matches the approved glossary (e.g., `Client`, not `Customer`).

---

## 8. Open Questions Relevant to Content
1. `[OQ-10]`: Confirm preferred legal wording on invoice footer regarding payment terms (e.g., *"Payment due within 14 days of invoice date via Stanbic Bank Account..."*).

---

## 9. Change Log
- **24 October 2026 (v0.1):** Content guidelines, voice/tone, terminology glossary, and microcopy patterns established.

*Unresolved items must not be treated as approved requirements.*
