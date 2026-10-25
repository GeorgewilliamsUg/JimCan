# Jimcan Operations Dashboard: Roles & Permissions Matrix

**Document:** `docs/design/roles-permissions.md`  
**Version:** 0.1  
**Date:** 24 October 2026  
**Status:** Draft for review  
**Owner:** George  
**Related Documents:**
- [`../../Project_Plan/Jimcan Operations Dashboard Product Requirements Document %28PRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Product%20Requirements%20Document%20%28PRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Technical Requirements Document %28TRD%29.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Technical%20Requirements%20Document%20%28TRD%29.md)
- [`../../Project_Plan/Jimcan Operations Dashboard Backend Schema Document.md`](file:///home/george/Desktop/Dev2026/Jimcan/Project_Plan/Jimcan%20Operations%20Dashboard%20Backend%20Schema%20Document.md)
- [`screens.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/screens.md)
- [`flows.md`](file:///home/george/Desktop/Dev2026/Jimcan/docs/design/flows.md)

---

## 1. Role Definitions & Access Philosophy

The Jimcan access control architecture implements strict **Role-Based Access Control (RBAC)** enforced at the Django view and database query layer. Hiding UI elements is strictly cosmetic; every request is authorized against the authenticated user's role before executing business logic.

The system defines four internal roles and one unauthenticated persona:

1. **`Admin` (Managing Director / Owner):** Complete operational and financial authority. Only role authorized to void issued documents, adjust tax rates, manage staff accounts, and view the raw audit log.
2. **`Manager` (Project Manager / Quantity Surveyor):** Operates the commercial engine: manages leads, builds BOQs, generates quotes, issues progress claims, and reviews site expenses.
3. **`Site Engineer` (Field Engineer / Site Foreman):** Operates on active construction sites via mobile phones. Focused strictly on physical execution: uploading site progress photos, logging field disbursements, and advancing construction phases.
4. **`Accountant` (Internal / External Financial Controller):** Read-only visibility over operational records with full analytical authority over tax reconciliation, payment verification, withholding tax tracking, and financial statements.
5. **`Visitor` (Public Website Prospect):** Unauthenticated public user submitting contact requests via `jimcanconstruction.site`.

---

## 2. Core Security & Privacy Constraints

1. **Information Barrier for Site Engineers:** Site Engineers are strictly prohibited from viewing client contract values, unit rate profit markups, supplier balances, company profit and loss, or tax returns.
2. **Immutability of Financial Records:** No role (including Admin) can permanently delete an issued invoice, recorded payment, or locked BOQ version. Adjustments must follow formal accounting reversals (credit notes or voids with recorded reasons).
3. **Least Privilege Principle:** Users default to zero permissions; capabilities are explicitly granted based on assigned role.

---

## 3. Comprehensive Entity Permission Matrix

Legend:
- `FULL`: Complete Create, Read, Update, Delete (Soft) authority.
- `READ`: View and export authority only.
- `OWN`: Authority restricted to records created by or explicitly assigned to the user.
- `SUBMIT`: Can create drafts and submit for higher-level review.
- `NONE`: No access; URL navigation returns HTTP 403 Forbidden (`S-03`).

| Operational Entity | `Admin` | `Manager` | `Site Engineer` | `Accountant` | `Visitor` |
|---|---|---|---|---|---|
| **Public Lead Endpoint (`S-23`)** | `NONE` | `NONE` | `NONE` | `NONE` | `CREATE` |
| **Leads & CRM (`S-20`–`S-22`)** | `FULL` | `FULL` | `NONE` | `NONE` | `NONE` |
| **Client Directory (`S-30`, `S-31`)** | `FULL` | `FULL` | `NONE` | `READ` | `NONE` |
| **Project Overview (`S-40`, `S-41`)** | `FULL` | `FULL` | `OWN` (Assigned Builds) | `READ` | `NONE` |
| **Project Phase Progression** | `FULL` | `FULL` | `OWN` (Update Only) | `NONE` | `NONE` |
| **Rate Library (`S-50`, `S-51`)** | `FULL` | `FULL` | `NONE` | `READ` | `NONE` |
| **BOQ Builder (`S-60`, `S-61`)** | `FULL` | `FULL` | `NONE` | `READ` | `NONE` |
| **Quotes & Pricing (`S-62`, `S-63`)** | `FULL` | `FULL` | `NONE` | `READ` | `NONE` |
| **Invoices (`S-70`–`S-72`)** | `FULL` | `FULL` | `NONE` | `READ` | `NONE` |
| **Payments & WHT (`S-73`)** | `FULL` | `READ` | `NONE` | `FULL` (Record & Reconcile) | `NONE` |
| **Invoice Voiding & Credit Notes** | `FULL` (Requires Reason) | `NONE` | `NONE` | `NONE` | `NONE` |
| **Field Expenses (`S-75`–`S-77`)** | `FULL` (Approve & Pay) | `FULL` (Approve) | `SUBMIT` (Own Expenses Only) | `FULL` (Reconcile) | `NONE` |
| **Suppliers & Balances (`S-78`)** | `FULL` | `FULL` | `NONE` | `READ` | `NONE` |
| **Site Media & CAD Files (`S-47`)**| `FULL` | `FULL` | `FULL` (Upload & View Assigned) | `READ` | `NONE` |
| **Tax Portal (`S-86`–`S-89`)** | `FULL` | `NONE` | `NONE` | `FULL` | `NONE` |
| **Financial Statements (`S-80`–`S-85`)**| `FULL` | `OWN` (Project Costs Only) | `NONE` | `FULL` | `NONE` |
| **Company Settings (`S-93`–`S-95`)**| `FULL` | `NONE` | `NONE` | `NONE` | `NONE` |
| **User Accounts & Roles (`S-96`)** | `FULL` | `NONE` | `NONE` | `NONE` | `NONE` |
| **Audit Log Trail (`S-92`)** | `FULL` (Read Only) | `NONE` | `NONE` | `NONE` | `NONE` |

---

## 4. Permission Enforcement Patterns

### 4.1 Django Class-Based View Decorators
Every view checks permission via a custom mixin:
```python
# accounts/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class RequireAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'
    def handle_no_permission(self):
        raise PermissionDenied("Admin role required.")

class RequireManagerOrAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['admin', 'manager']
```

### 4.2 QuerySet Filtering (Row-Level Security)
Data isolation is enforced at the database query level:
```python
# projects/views.py
class ProjectListView(ListView):
    model = Project
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'accountant']:
            return Project.objects.filter(is_deleted=False)
        elif user.role == 'manager':
            return Project.objects.filter(is_deleted=False) # Or assigned
        elif user.role == 'engineer':
            return Project.objects.filter(members=user, is_deleted=False)
        return Project.objects.none()
```

### 4.3 Template UI Hiding
Navigation items and action buttons check role attributes:
```html
{% if request.user.role == 'admin' %}
  <a href="{% url 'settings_index' %}" class="...">Settings</a>
{% endif %}
```

---

## 5. Open Questions Relevant to Permissions
1. `[OQ-13]`: Determine whether Managers should be restricted strictly to their own assigned projects, or have company-wide project visibility like the Admin.

---

## 6. Change Log
- **24 October 2026 (v0.1):** 4-role RBAC matrix and enforcement architecture compiled based on PRD Section 5 and TRD Section 3.1.

*Unresolved items must not be treated as approved requirements.*
