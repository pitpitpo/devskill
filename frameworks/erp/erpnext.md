# 🚀 Frappe Framework & ERPNext Engineering Guide (`frameworks/erp/erpnext.md`)

> **Classification**: Enterprise ERP Architecture, Metadata-Driven DocTypes, Query Builder & Doppio SPA Engineering  
> **Target Systems**: Frappe Framework v15.0+ & v16.0+, ERPNext v15.0+ & v16.0+  
> **Prerequisites**: Python 3.11+, MariaDB 10.6+ / PostgreSQL 15+, JavaScript/TypeScript, Redis, Docker / Bench CLI  
> **Governing Rules**: **R-001** (Zero TODOs), **R-033** (Strict Typing), **R-061** (SQL Parameterization), **R-063** (DocType Role Permissions), **R-184** (Idempotency), **R-255** (Frappe Query Builder & Permission Discipline)  
> **Last Updated**: 2026-11-19  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Framework Version** | Frappe Framework v15 LTS / v16, ERPNext v15 / v16 |
| **Runtime Environment** | Python 3.11 / 3.12, Node.js 20 / 22, MariaDB 10.6+ / PostgreSQL 15+ |
| **Frontend Framework** | Frappe Desk UI + **Doppio** (Vite React/Vue + TypeScript + Tailwind + `frappe-react-sdk`) |
| **Caching & Message Broker** | Redis (Cache, RQ Background Queue, SocketIO Pub/Sub) |
| **Key Invariant Rules** | **R-061** (`frappe.qb` PyPika Query Builder over raw SQL), **R-063** (`frappe.get_list` + explicit `has_permission`), **R-255** (POST-only mutations, Frappe Recorder N+1 checks, idempotent `patches.txt`) |

---

## 2. Core Philosophy / Golden Rule

> **Never Execute Raw Database Mutations Outside the DocType Document Lifecycle; Respect Validation Hooks, Child Table Integrity, and General Ledger Immutability.**
> 
> *Frappe is a metadata-driven application framework where every business entity is defined as a DocType. Document controllers enforce business constraints across standardized lifecycle hooks (`validate`, `before_save`, `on_submit`, `on_cancel`). Direct database updates (`frappe.db.set_value` or raw SQL) bypass validation triggers, ignore child table linkages, skip permission gates, and corrupt financial double-entry ledger entries (`GL Entry`).*

---

## 3. Architecture & Design Patterns

```
                             FRAPPE / ERPNEXT BENCH ARCHITECTURE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT BROWSER / DESK UI                                  │
│              Frappe Desk SPA, Form Scripts (`cur_frm`), Real-time SocketIO             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / WebSocket / REST API
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              NGINX REVERSE PROXY                                       │
│          Static Asset Routing (`/assets`), Multi-Tenant Host Routing (`bench`)         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              GUNICORN WSGI APPLICATION                                 │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │ Whitelisted API Route │  │   DocType Controller  │  │   Permissions Engine       │  │
│  │ (`@frappe.whitelist`) │  │   (`Document` Class)  │  │   Role & User Perms        │  │
│  └───────────────────────┘  └───────────┬───────────┘  └────────────────────────────┘  │
│                                         │                                              │
│  ┌──────────────────────────────────────┴───────────────────────────────────────────┐  │
│  │                     Document Lifecycle State Pipeline                            │  │
│  │  validate() ──► before_save() ──► on_submit() ──► on_cancel()                    │  │
│  └──────────────────────────────────────┬───────────────────────────────────────────┘  │
└──────────────────┬──────────────────────┼───────────────────────┬──────────────────────┘
                   │                      │                       │
                   ▼                      ▼                       ▼
┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────────┐
│  REDIS CLUSTER           │ │ MARIADB / POSTGRESQL     │ │ RQ BACKGROUND WORKERS        │
│  • Session Store (11000) │ │ Relational DocType Tables│ │ • short / default / long     │
│  • Message Queue (12000) │ │ (`tabOrder`, `tabItem`)  │ │ • `frappe.enqueue` jobs      │
│  • SocketIO Pub/Sub (13) │ │ ACID Ledger Transactions │ │ • Cron Schedulers (`hooks`)  │
└──────────────────────────┘ └──────────────────────────┘ └──────────────────────────────┘
```

### 3.1 App & Directory Structure

```
custom_erp_app/
├── custom_erp_app/
│   ├── __init__.py
│   ├── hooks.py              # Application configuration, doc events, fixtures, scheduled jobs
│   ├── api.py                # Public & authenticated whitelisted REST API endpoints
│   ├── custom_erp_app/
│   │   ├── doctype/
│   │   │   └── manufacturing_batch/
│   │   │       ├── __init__.py
│   │   │       ├── manufacturing_batch.json # DocType schema metadata definition
│   │   │       ├── manufacturing_batch.py   # Python server-side document controller
│   │   │       ├── manufacturing_batch.js   # Client-side form script (Desk UI)
│   │   │       └── test_manufacturing_batch.py # Automated test suite
│   ├── public/               # Client-side assets (CSS, JS, icons)
│   └── templates/            # Jinja2 web view templates
├── license.txt
└── pyproject.toml
```

---

## 4. Concrete Code Examples

### 4.1 Production DocType Document Controller with Lifecycle & Ledger Integrations

```python
# custom_erp_app/custom_erp_app/doctype/manufacturing_batch/manufacturing_batch.py
"""
Production Frappe Document Controller for Manufacturing Batch.
Demonstrates: Submittable Lifecycle (`docstatus`), Validation, Child Table Rollups,
Stock Ledger Entry (SLE) creation, and Idempotency Protection.
"""

from __future__ import annotations
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, get_datetime


class ManufacturingBatch(Document):
    """
    Manufacturing Batch Document Controller.
    DocStatus: 0 = Draft, 1 = Submitted, 2 = Cancelled.
    """

    def validate(self):
        """Pre-save validation hook. Validates invariants before commit."""
        self.validate_dates()
        self.validate_items()
        self.calculate_batch_totals()

    def before_submit(self):
        """Pre-submission verification. Checks raw material stock availability."""
        self.check_raw_material_availability()

    def on_submit(self):
        """Submission hook. Executes permanent state transitions and ledger updates."""
        self.db_set("status", "In Production")
        self.create_stock_ledger_entries()
        self.publish_realtime_update("submitted")

    def on_cancel(self):
        """Cancellation hook. Generates compensating reverse stock ledger entries."""
        self.db_set("status", "Cancelled")
        self.cancel_stock_ledger_entries()
        self.publish_realtime_update("cancelled")

    def validate_dates(self):
        if self.start_date and self.end_date:
            if get_datetime(self.start_date) > get_datetime(self.end_date):
                frappe.throw(
                    msg=_("End Date ({0}) cannot be earlier than Start Date ({1}).").format(
                        self.end_date, self.start_date
                    ),
                    title=_("Invalid Date Range"),
                )

    def validate_items(self):
        if not self.get("items"):
            frappe.throw(
                msg=_("A manufacturing batch must contain at least one item."),
                title=_("Missing Child Items"),
            )

        for row in self.items:
            if flt(row.required_qty) <= 0.0:
                frappe.throw(
                    msg=_("Row #{0}: Required Quantity for item {1} must be positive.").format(
                        row.idx, row.item_code
                    )
                )

    def calculate_batch_totals(self):
        """Computes summary aggregates across child table rows."""
        total_qty = 0.0
        total_estimated_cost = 0.0

        for row in self.items:
            row.amount = flt(row.required_qty) * flt(row.standard_rate)
            total_qty += flt(row.required_qty)
            total_estimated_cost += row.amount

        self.total_quantity = total_qty
        self.total_cost = total_estimated_cost

    def check_raw_material_availability(self):
        """Verifies that warehouse stock is sufficient for consumption."""
        for row in self.items:
            actual_qty = frappe.db.get_value(
                "Bin",
                {"item_code": row.item_code, "warehouse": row.source_warehouse},
                "actual_qty",
            ) or 0.0

            if flt(actual_qty) < flt(row.required_qty):
                frappe.throw(
                    msg=_(
                        "Insufficient stock for Item {0} in Warehouse {1}. Available: {2}, Required: {3}."
                    ).format(row.item_code, row.source_warehouse, actual_qty, row.required_qty),
                    title=_("Stock Shortage"),
                )

    def create_stock_ledger_entries(self):
        """
        Generates immutable Stock Ledger Entries consuming raw materials.
        Follows ERPNext Stock Ledger Invariants.
        """
        for row in self.items:
            sle = frappe.get_doc({
                "doctype": "Stock Ledger Entry",
                "item_code": row.item_code,
                "warehouse": row.source_warehouse,
                "posting_date": nowdate(),
                "posting_time": frappe.utils.nowtime(),
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "voucher_detail_no": row.name,
                "actual_qty": -flt(row.required_qty),  # Deduct stock
                "company": self.company,
                "is_cancelled": 0,
            })
            # Submitting the SLE updates the Bin balance atomically
            sle.submit()

    def cancel_stock_ledger_entries(self):
        """Reverses stock moves upon document cancellation."""
        existing_sles = frappe.get_all(
            "Stock Ledger Entry",
            filters={"voucher_type": self.doctype, "voucher_no": self.name, "is_cancelled": 0},
            pluck="name",
        )
        for sle_name in existing_sles:
            sle = frappe.get_doc("Stock Ledger Entry", sle_name)
            sle.cancel()

    def publish_realtime_update(self, event_name: str):
        """Pushes real-time SSE / WebSocket notifications to active Desk users."""
        frappe.publish_realtime(
            event="batch_status_change",
            message={"batch_id": self.name, "status": self.status, "event": event_name},
            user=self.owner,
        )
```

---

### 4.2 Client-Side Form Scripting (`manufacturing_batch.js`)

```javascript
// custom_erp_app/custom_erp_app/doctype/manufacturing_batch/manufacturing_batch.js
/**
 * Frappe Desk Client-Side Form Script for Manufacturing Batch.
 * Implements: Field event handling, child table auto-computations,
 * dynamic warehouse filtering, and custom workflow action buttons.
 */

frappe.ui.form.on('Manufacturing Batch', {
    setup(frm) {
        // Enforce filtering on source_warehouse to match current company
        frm.set_query('source_warehouse', 'items', (doc) => {
            return {
                filters: {
                    company: doc.company,
                    is_group: 0,
                }
            };
        });
    },

    refresh(frm) {
        // Display custom action button on submitted documents
        if (frm.doc.docstatus === 1 && frm.doc.status === 'In Production') {
            frm.add_custom_button(__('Mark Quality Inspected'), () => {
                frappe.confirm(
                    __('Are you sure you want to approve quality inspection for batch {0}?', [frm.doc.name]),
                    () => {
                        frappe.call({
                            method: 'custom_erp_app.api.approve_quality',
                            args: { batch_name: frm.doc.name },
                            freeze: true,
                            freeze_message: __('Recording inspection...'),
                            callback(r) {
                                if (!r.exc) {
                                    frm.reload_doc();
                                    frappe.show_alert({
                                        message: __('Batch inspection approved successfully.'),
                                        indicator: 'green'
                                    });
                                }
                            }
                        });
                    }
                );
            }, __('Actions'));
        }
    },

    company(frm) {
        // Clear child table warehouses if company changes
        if (frm.doc.items) {
            frm.doc.items.forEach(row => {
                frappe.model.set_value(row.doctype, row.name, 'source_warehouse', '');
            });
        }
    }
});

// Child Table Event Handlers
frappe.ui.form.on('Manufacturing Batch Item', {
    item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        // Fetch standard rate asynchronously from Item Master
        frappe.db.get_value('Item', row.item_code, ['standard_rate', 'stock_uom'])
            .then(res => {
                if (res && res.message) {
                    frappe.model.set_value(cdt, cdn, 'standard_rate', res.message.standard_rate || 0.0);
                    frappe.model.set_value(cdt, cdn, 'uom', res.message.stock_uom);
                }
            });
    },

    required_qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const amount = flt(row.required_qty) * flt(row.standard_rate);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    }
});
```

---

### 4.3 High-Performance Whitelisted REST API & Background Job Queue

```python
# custom_erp_app/api.py
"""
High-Performance, Whitelisted REST API Endpoints and Background Workers.
Demonstrates: Token Auth, Idempotency-Key validation, Error Envelope handling,
and asynchronous task dispatch via Redis Queue.
"""

from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt
import hashlib
import json


@frappe.whitelist(methods=["POST"])
def create_batch_order():
    """
    Whitelisted API endpoint for creating manufacturing batches idempotently.
    Enforces Role Permission and Idempotency Keys.
    """
    # 1. Permission Check
    if not frappe.has_permission("Manufacturing Batch", "create"):
        frappe.throw(_("Not permitted to create Manufacturing Batch."), frappe.PermissionError)

    # 2. Extract Idempotency Key
    idempotency_key = frappe.get_request_header("Idempotency-Key")
    if not idempotency_key:
        frappe.throw(
            msg=_("Missing required 'Idempotency-Key' header in request."),
            exc=frappe.MandatoryError,
        )

    data = frappe.request.get_json()
    if not data or not data.get("items"):
        frappe.throw(_("Payload must contain 'company' and 'items' array."), frappe.ValidationError)

    payload_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()

    # 3. Check Idempotency Store
    cache_key = f"idempotency:batch:{idempotency_key}"
    cached_response = frappe.cache.get_value(cache_key)

    if cached_response:
        cached_data = json.loads(cached_response)
        if cached_data.get("hash") != payload_hash:
            frappe.throw(
                msg=_("Idempotency-Key conflict: Key reused with differing request payload."),
                exc=frappe.DuplicateEntryError,
            )
        return cached_data.get("response")

    # 4. Construct Document
    doc = frappe.new_doc("Manufacturing Batch")
    doc.company = data.get("company")
    doc.start_date = data.get("start_date")
    doc.end_date = data.get("end_date")

    for item in data.get("items", []):
        doc.append("items", {
            "item_code": item.get("item_code"),
            "source_warehouse": item.get("source_warehouse"),
            "required_qty": flt(item.get("required_qty")),
        })

    doc.insert()

    # If requested to submit directly, enqueue background job to avoid HTTP timeout
    if data.get("auto_submit"):
        frappe.enqueue(
            method="custom_erp_app.api.background_submit_batch",
            queue="default",
            timeout=300,
            batch_name=doc.name,
        )

    response_payload = {
        "status": "success",
        "batch_name": doc.name,
        "docstatus": doc.docstatus,
        "total_cost": doc.total_cost,
    }

    # Cache response for 24 hours
    frappe.cache.set_value(
        cache_key,
        json.dumps({"hash": payload_hash, "response": response_payload}),
        expires_in_sec=86400,
    )

    return response_payload


def background_submit_batch(batch_name: str):
    """Asynchronous background worker executing document submission."""
    try:
        doc = frappe.get_doc("Manufacturing Batch", batch_name)
        if doc.docstatus == 0:
            doc.submit()
            frappe.db.commit()
    except Exception as exc:
        frappe.log_error(title=f"Background Submit Failed for {batch_name}", message=str(exc))
        frappe.db.rollback()


@frappe.whitelist(methods=["POST"])
def approve_quality(batch_name: str):
    """Action method called from Desk UI form button."""
    doc = frappe.get_doc("Manufacturing Batch", batch_name)
    doc.check_permission("write")

    doc.db_set("quality_inspected", 1)
    doc.add_comment("Comment", _("Quality inspection approved by {0}").format(frappe.session.user))

    return {"status": "ok"}
```

---

### 4.4 `hooks.py` Event Orchestration & Scheduled Jobs

```python
# custom_erp_app/hooks.py
"""
Application Configuration and Lifecycle Hook Registrations.
"""

app_name = "custom_erp_app"
app_title = "Custom ERP Extensions"
app_publisher = "DevSkill Architecture Team"
app_description = "Enterprise ERP Extensions for Frappe and ERPNext"
app_version = "1.0.0"

# Document Lifecycle Event Subscriptions
doc_events = {
    "Sales Invoice": {
        "on_submit": "custom_erp_app.events.on_sales_invoice_submit",
        "on_cancel": "custom_erp_app.events.on_sales_invoice_cancel",
    },
    "Stock Entry": {
        "validate": "custom_erp_app.events.validate_custom_stock_rules",
    }
}

# Scheduled Background Tasks
scheduler_events = {
    "daily": [
        "custom_erp_app.tasks.reconcile_daily_inventory_batches",
    ],
    "hourly": [
        "custom_erp_app.tasks.sync_external_fulfillment_orders",
    ]
}

# Export Custom Fields and DocType Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["dt", "in", ["Item", "Sales Invoice"]]]
    }
]
```

---

### 4.5 Type-Safe, Database-Portable Queries with `frappe.qb` (PyPika)

Prefer `frappe.qb` over raw `frappe.db.sql` for all reporting and relational joins: it is structurally immune to SQL injection and compiles cleanly across both MariaDB and PostgreSQL:

```python
import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum

def get_warehouse_stock_valuation(company: str) -> list[dict]:
    Bin = DocType("Bin")
    Warehouse = DocType("Warehouse")

    query = (
        frappe.qb.from_(Bin)
        .inner_join(Warehouse)
        .on(Bin.warehouse == Warehouse.name)
        .select(
            Warehouse.name.as_("warehouse"),
            Sum(Bin.stock_value).as_("total_value"),
        )
        .where((Warehouse.company == company) & (Warehouse.is_group == 0))
        .groupby(Warehouse.name)
    )
    return query.run(as_dict=True)
```

### 4.6 Modern Custom SPAs with Doppio & `patches.txt` Discipline
- **Doppio SPA**: Scaffold rich customer/operator portals inside your Frappe app via `bench add-spa --app custom_erp_app --tailwindcss --typescript`, pairing Vite proxy (`proxyOptions.js`) with `frappe-react-sdk` (SWR cache + SocketIO + cookie auth).
- **Frappe v16 Hardening**: Mark all state-mutating `@frappe.whitelist(methods=["POST"])` routes explicitly; profile heavy endpoints with **Frappe Recorder** (`/app/recorder`) to catch N+1 queries before merge.
- **Idempotent Data Migrations (`patches.txt`)**: Register schema/data backfills under `[pre_model_sync]` or `[post_model_sync]` in `patches.txt` and ensure every patch is safe to re-run without duplicating entries.

---

## 5. Security & Performance Considerations

### 5.1 Query Builder First & Strict SQL Parameterization
Never use Python f-strings or string formatting in `frappe.db.sql()`. Prefer `frappe.qb` (PyPika); if raw SQL is unavoidable for engine-specific DDL/analytics, parameterize strictly:
- **Forbidden**: `frappe.db.sql(f"SELECT * FROM tabItem WHERE item_code = '{item}'")`
- **Preferred**: `frappe.qb.from_(Item).select(Item.name, Item.standard_rate).where(Item.item_code == item).run(as_dict=True)`
- **Parameterized Fallback**: `frappe.db.sql("SELECT name, item_name, standard_rate FROM `tabItem` WHERE item_code = %s", (item,), as_dict=True)`

### 5.2 Permission Leaks with `frappe.get_all` vs `frappe.get_list`
- `frappe.get_all`: Retrieves records **bypassing** user role permissions. Use only in internal background workers or trusted system tasks.
- `frappe.get_list`: Retrieves records **strictly enforcing** role permissions and user permissions (e.g., Company, Cost Center filters). Use in all user-facing APIs.

### 5.3 Batching Database Commits in Long-Running Tasks
Calling `frappe.db.commit()` inside tight loops creates disk I/O thrashing and lock contention. In long-running workers:
- Commit every 100–500 iterations.
- Wrap mutations in `frappe.db.begin()` and `frappe.db.rollback()` blocks to guarantee atomic error recovery.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Bypassing Document Submission Lifecycle
- **Violation**: Changing `docstatus` directly via SQL (`UPDATE tabOrder SET docstatus = 1 WHERE name = ...`).
- **Consequence**: The document is marked submitted, but `on_submit()` hooks are skipped. Stock ledger entries and general ledger entries are never generated, causing catastrophic accounting desynchronization.
- **Remediation**: Always invoke `doc.submit()` or `doc.cancel()`.

### Anti-Pattern 2: Unfiltered Child Table Queries
- **Violation**: Querying child tables without filtering on `parenttype` and `parent`.
- **Consequence**: Inadvertently matching child table rows belonging to unrelated documents of a different DocType.
- **Remediation**: Always filter child tables by `parent` and `parenttype`:
  ```python
  items = frappe.get_all("Manufacturing Batch Item", filters={"parent": batch_name, "parenttype": "Manufacturing Batch"})
  ```

### Anti-Pattern 3: Writing Client-Side Business Calculations Without Server Validation
- **Violation**: Calculating invoice totals only in JavaScript (`frm.set_value('total', total)`) without matching Python calculations in `validate()`.
- **Consequence**: Malicious clients can submit tampered totals via the REST API or console, bypassing pricing logic.
- **Remediation**: Always treat client-side scripts as UX conveniences. Recompute and validate all values authoritatively on the server in `validate()`.

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Unit & DocType Tests** | 100% test pass rate | `bench --site test.local run-tests --app custom_erp_app` exits with code 0 |
| **2. SQL Parameterization** | Zero unparameterized queries | Scan code with `git grep -EIn "frappe\.db\.sql\(f\""` (Zero hits) |
| **3. Permission Isolation** | Zero unauthorized reads | Verify `frappe.get_list` enforces company user permissions in tests |
| **4. Submittable Invariant** | Valid `docstatus` state transitions | Tests verify draft (0) $\to$ submitted (1) $\to$ cancelled (2) lifecycle |
| **5. Idempotent API Ingress** | Zero duplicate documents on retry | Execute duplicate POST with identical `Idempotency-Key` (returns 200/201 cached) |

---

*See also*: [`./odoo.md`](./odoo.md) for Odoo comparisons, and [`../../sections/erp-enterprise/inventory-supply-chain.md`](../../sections/erp-enterprise/inventory-supply-chain.md) for stock ledger calculation engines.
