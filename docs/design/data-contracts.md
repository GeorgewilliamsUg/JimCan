# Jimcan Operations Dashboard: Front-End / Backend Data Contracts

**Document:** `docs/design/data-contracts.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Backend Schema Document.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Backend%20Schema%20Document.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`states.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/states.md)
- [`handoff.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/handoff.md)

---

## 1. Architectural Contract Principles

The Jimcan Dashboard relies on **HTML Over The Wire**:
1. **Server-Rendered HTML First:** Django templates generate complete, semantic HTML. There is no heavy client-side JavaScript Single Page App (SPA) framework or separate REST/GraphQL API layer for the UI.
2. **HTMX Fragment Swaps:** Interactive updates (filters, pagination, modal loads, inline status edits) return server-rendered HTML fragments (partials), swapping cleanly into target DOM nodes via `hx-target` and `hx-swap`.
3. **Embedded JSON for Visualizations:** Chart.js charts consume JSON data payloads embedded directly within the initial HTML page via Django's `json_script` template tag.
4. **Public vs Internal Keys:** Public URLs strictly use UUIDs (`public_id`) to prevent sequential enumeration. Internal foreign keys use 64-bit BigInts (`id`).

---

## 2. Data Types, Formats & Precision Rules

| Data Type | Backend Representation | Template / Display Format | Validation Rules |
|---|---|---|---|
| **Currency** | `Decimal(16, 2)` | `UGX 14,500,000` (Geist Mono, tabular) | Always positive on entry; negative displays in brackets `(UGX 100)`. Never float. |
| **Tax Percent** | `Decimal(6, 2)` | `18.00%`, `6.00%` | Valid range `0.00` to `100.00`. |
| **Quantities** | `Decimal(14, 3)` | `450.000 m³`, `12.500 nr` | Scale up to 3 decimals for accurate engineering calculations. |
| **Date** | `datetime.date` | `24 Oct 2026` | ISO format `YYYY-MM-DD` on submission. |
| **Timestamp** | `datetime.datetime` (UTC) | `24 Oct 2026, 14:32 EAT` | Stored in UTC; converted to East Africa Time (UTC+3) at render time. |
| **Phone** | `VarChar(32)` | `+256 772 123 456` | E.164 international or 10-digit Uganda local format. |
| **Status Enums** | `VarChar(32)` | Rendered via semantic badge chip | Must match database enum string strictly. |

---

## 3. HTMX Interaction & Response Contracts

### 3.1 Request Headers
When HTMX dispatches an asynchronous request, Django inspects standard request headers:
- `HX-Request: "true"`
- `HX-Target: "[DOM Element ID]"`
- `HX-Current-URL: "[Browser Location]"`

### 3.2 Response Codes & Behaviors
- **HTTP 200 OK (Fragment Swap):** Returns the HTML fragment to replace `hx-target`.
  ```html
  <!-- Swapped partial: templates/leads/_lead_row.html -->
  <tr id="lead-row-{{ lead.public_id }}" class="..."> ... </tr>
  ```
- **HTTP 422 Unprocessable Entity (Validation Error):** When a form submission fails validation, Django returns HTTP 422 with the re-rendered form partial containing error summaries. HTMX swaps the form to display error messages.
- **HTTP 204 No Content:** Used for background operations (e.g., heartbeat, read receipts).
- **HTTP 302 / `HX-Redirect`:** Client redirect to new screen upon major state transition (e.g. converting a lead redirects to `/projects/<public_id>/`).

### 3.3 Event Triggering via `HX-Trigger`
Django views trigger client-side UI effects (like Toasts) by setting the `HX-Trigger` response header:
```python
response = render(request, 'leads/_lead_row.html', {'lead': lead})
response['HX-Trigger'] = json.dumps({
    "showToast": {"message": "Lead status updated to Won", "type": "success"}
})
return response
```

---

## 4. Form Submission & Error Shapes

All forms post with `Content-Type: application/x-www-form-urlencoded` or `multipart/form-data`, including the mandatory CSRF token (`{% csrf_token %}`).

### 4.1 Field Error Template Structure
When validation fails, Django forms render using the standardized `_field_errors.html` partial:
```html
{% if form.errors %}
  <div role="alert" class="bg-red-50 border border-danger p-4 rounded-lg mb-6">
    <div class="flex items-center text-danger font-bold text-sm">
      <svg class="w-5 h-5 mr-2" fill="currentColor"> ... </svg>
      Please correct the errors below before proceeding.
    </div>
    <ul class="list-disc list-inside mt-2 text-xs text-danger">
      {% for field, errors in form.errors.items %}
        {% for error in errors %}
          <li><strong>{{ form|get_field_label:field }}:</strong> {{ error }}</li>
        {% endfor %}
      {% endfor %}
    </ul>
  </div>
{% endif %}
```

---

## 5. Chart.js Data Payload Contract

Dashboard charts (`S-10`) consume structured JSON data provided by Django view context:

```html
<!-- Inside S-10 template -->
{{ cashflow_chart_data|json_script:"cashflow-data-payload" }}

<script>
  document.addEventListener("DOMContentLoaded", function() {
    const data = JSON.parse(document.getElementById("cashflow-data-payload").textContent);
    new Chart(document.getElementById("cashflow-canvas"), {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          { label: 'Money In (UGX)', data: data.money_in, backgroundColor: '#3E8E5A' },
          { label: 'Money Out (UGX)', data: data.money_out, backgroundColor: '#B23A3A' }
        ]
      },
      options: { ... }
    });
  });
</script>
```

### 5.1 JSON Payload Shape
```json
{
  "labels": ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
  "currency": "UGX",
  "money_in": [140000000, 195000000, 80000000, 220000000, 310000000, 420000000],
  "money_out": [110000000, 140000000, 95000000, 160000000, 240000000, 310000000]
}
```

---

## 6. File Upload Contract (`S-47`, `S-76`, `S-90`)

- **Encoding:** `multipart/form-data`.
- **Maximum File Size:** 10.0 MB per upload.
- **Allowed MIME Types:** `image/jpeg`, `image/png`, `image/webp`, `application/pdf`, `application/acad` (DWG/DXF).
- **Processing Pipeline:** Pillow strips EXIF metadata, auto-rotates images according to orientation tags, and compresses files before saving to private storage outside the web root.
- **Private Media Delivery:** Media files are served through a Django protected view (`/media/private/<token>/`) that verifies user permissions before streaming file bytes. Direct public URL access is prohibited.

---

## 7. Open Questions Relevant to Data Contracts
1. `[OQ-14]`: Confirmation of whether CAD drawings (`.dwg`) should be previewed via a third-party viewer or offered purely as raw file downloads.

---

## 8. Change Log
- **24 October 2026 (v0.1):** Front-end/backend data contracts, HTMX headers, validation shapes, and Chart.js payloads defined.

*Unresolved items must not be treated as approved requirements.*
