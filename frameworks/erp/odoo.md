# 📦 Odoo 17 & 18 Enterprise Engineering Guide (`frameworks/erp/odoo.md`)

> **Classification**: Enterprise ERP Architecture, Module Development, Business Process Engineering  
> **Target Systems**: Odoo 17.0+ & 18.0+ Community & Enterprise Editions  
> **Prerequisites**: Python 3.10+, PostgreSQL 14+, JavaScript (ES6+ / OWL), XML, CSS/SCSS, Docker  
> **Governing Rules**: **R-001** (Zero TODOs), **R-033** (Strict Typing), **R-061** (SQL Parameterization), **R-063** (Access Control / Record Rules), **R-184** (Idempotency)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Framework Version** | Odoo 17.0 LTS / Odoo 18.0 LTS |
| **Runtime Environment** | Python 3.10 / 3.11 / 3.12, PostgreSQL 14 / 15 / 16 / 17 |
| **Frontend Framework** | OWL 2.0 (Odoo Web Library) Component Engine |
| **Communication Protocols** | JSON-RPC (HTTP `/web/dataset/call_kw`), RESTful JSON, XML-RPC (legacy) |
| **Key Invariant Rules** | **R-061** (Always use parameterized SQL queries via `self.env.cr.execute(query, params)`), **R-063** (Strict ACLs in `ir.model.access.csv` and multi-company record rules), **R-184** (Idempotent mutation endpoints) |

---

## 2. Core Philosophy / Golden Rule

> **Never Bypass the Odoo ORM or Record Rules to Execute Raw State Transitions; Respect the Environment Registry, Multi-Company Domains, and Double-Entry Invariants.**
> 
> *Odoo is not a standard web framework where models are passive data bags. Odoo models encapsulate validation, access security, automated audit trails (`mail.thread`), and transactional state machines. Direct SQL mutations that bypass the ORM skip record rules, invalidate in-memory caches, break compute dependency graphs, and desynchronize financial ledgers. Every business operation must execute as an atomic, multi-company safe transaction.*

---

## 3. Architecture & Design Patterns

```
                                ODOO 17/18 RUNTIME ARCHITECTURE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT BROWSER / MOBILE                                   │
│                        OWL 2.0 (Odoo Web Library) SPA + QWeb                           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / JSON-RPC / WebSocket
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         WSGI WORKER / LONGPOLLING REVERSE PROXY                        │
│                   Gevent / Threaded Dispatcher (Nginx + Let's Encrypt)                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                ODOO APPLICATION SERVER                                 │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │   HTTP Controller     │  │      ORM Engine       │  │     Security Layer         │  │
│  │   (`odoo.http.route`) │  │   (`models.Model`)    │  │  `ir.model.access` +       │  │
│  │   REST / JSON-RPC     │  │   Recordset API       │  │  `ir.rule` (Multi-Company) │  │
│  └───────────────────────┘  └───────────┬───────────┘  └────────────────────────────┘  │
│                                         │                                              │
│  ┌──────────────────────────────────────┴───────────────────────────────────────────┐  │
│  │                    Transactional Business Subsystems                             │  │
│  │  • Accounting (`account.move`, `account.move.line`) - Balanced Double-Entry       │  │
│  │  • Inventory (`stock.move`, `stock.quant`, `stock.valuation.layer`)              │  │
│  │  • Sales & Purchase (`sale.order`, `purchase.order`)                             │  │
│  └──────────────────────────────────────┬───────────────────────────────────────────┘  │
└─────────────────────────────────────────┼──────────────────────────────────────────────┘
                                          │ Parameterized SQL Connection Pool
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             POSTGRESQL RELATIONAL ENGINE                               │
│                Row-Level Locks, WAL, Foreign Key Constraints, PgBouncer                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Module Anatomy & Layout

Every enterprise Odoo module MUST adhere to the standardized directory anatomy:

```
custom_module/
├── __init__.py               # Python package initialization (imports controllers, models, wizards)
├── __manifest__.py           # Declarative manifest with dependencies, data, assets, and license
├── models/
│   ├── __init__.py           # Sub-package model imports
│   ├── custom_entity.py      # Core business entity definition
│   └── res_partner.py        # Model extension using `_inherit`
├── views/
│   ├── custom_entity_views.xml # Search, Form, Tree/List, Kanban views and Action Windows
│   └── menu_views.xml        # Top-level and sub-menu hierarchy definitions
├── security/
│   ├── ir.model.access.csv   # Role-based model access control table
│   └── security_rules.xml    # Multi-company, multi-branch, and record-level security rules
├── wizards/                  # Transient models (`models.TransientModel`) for modal wizards
│   ├── __init__.py
│   ├── bulk_action_wizard.py
│   └── bulk_action_wizard_views.xml
├── controllers/              # RESTful and JSON-RPC HTTP ingress routes
│   ├── __init__.py
│   └── api_controller.py
├── data/                     # Automated sequence numbers, cron jobs, and default data
│   ├── ir_sequence_data.xml
│   └── ir_cron_data.xml
├── static/
│   └── src/                  # OWL JavaScript components, XML templates, SCSS styles
│       ├── components/
│       └── views/
└── tests/                    # Unit, integration, and security test suites
    ├── __init__.py
    ├── test_custom_entity.py
    └── test_security.py
```

---

## 4. Concrete Code Examples

### 4.1 Production Model with State Machine, Invariants & Computed Fields

```python
# custom_module/models/custom_order.py
"""
Production Odoo 17/18 Business Entity Implementation.
Demonstrates: State Machine, Computed Fields with Inverses, Constraints,
Multi-Company Isolation, and Mail Thread Auditing.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomOrder(models.Model):
    _name = "custom.order"
    _description = "Enterprise Customer Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_order desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Order Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
        tracking=True,
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    date_order = fields.Datetime(
        string="Order Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("in_process", "In Process"),
            ("done", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
        tracking=True,
    )
    order_line_ids = fields.One2many(
        comodel_name="custom.order.line",
        inverse_name="order_id",
        string="Order Lines",
        copy=True,
    )
    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_amounts",
        store=True,
        tracking=True,
    )
    amount_tax = fields.Monetary(
        string="Taxes",
        compute="_compute_amounts",
        store=True,
    )
    amount_total = fields.Monetary(
        string="Total Amount",
        compute="_compute_amounts",
        store=True,
        tracking=True,
    )

    @api.depends("order_line_ids.price_subtotal", "order_line_ids.tax_amount")
    def _compute_amounts(self):
        """Batch-computes order monetary totals to prevent N+1 query overhead."""
        for order in self:
            untaxed = sum(order.order_line_ids.mapped("price_subtotal"))
            taxes = sum(order.order_line_ids.mapped("tax_amount"))
            order.amount_untaxed = untaxed
            order.amount_tax = taxes
            order.amount_total = untaxed + taxes

    @api.constrains("order_line_ids")
    def _check_order_lines(self):
        for order in self:
            if order.state == "confirmed" and not order.order_line_ids:
                raise ValidationError(_("A confirmed order must contain at least one order line."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                vals["name"] = self.env["ir.sequence"].with_company(company_id).next_by_code(
                    "custom.order"
                ) or _("New")
        return super().create(vals_list)

    def action_confirm(self):
        """Transitions order from draft to confirmed. Validates stock and reservations."""
        for order in self:
            if order.state != "draft":
                raise UserError(_("Only draft orders can be confirmed."))
            if not order.order_line_ids:
                raise UserError(_("Cannot confirm an order with zero lines."))

            order.write({"state": "confirmed"})
            order.message_post(
                body=_("Order confirmed with total value %s %s") % (order.amount_total, order.currency_id.symbol),
                subtype_xmlid="mail.mt_note",
            )
        return True

    def action_cancel(self):
        for order in self:
            if order.state == "done":
                raise UserError(_("Completed orders cannot be cancelled."))
            order.write({"state": "cancelled"})
        return True


class CustomOrderLine(models.Model):
    _name = "custom.order.line"
    _description = "Custom Order Line Item"
    _check_company_auto = True

    order_id = fields.Many2one(
        comodel_name="custom.order",
        string="Order Reference",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="order_id.company_id",
        string="Company",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="order_id.currency_id",
        string="Currency",
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        check_company=True,
    )
    product_uom_qty = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
    )
    price_unit = fields.Monetary(
        string="Unit Price",
        required=True,
        default=0.0,
    )
    tax_rate = fields.Float(
        string="Tax Rate (%)",
        default=0.0,
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute="_compute_line_totals",
        store=True,
    )
    tax_amount = fields.Monetary(
        string="Tax Amount",
        compute="_compute_line_totals",
        store=True,
    )

    @api.depends("product_uom_qty", "price_unit", "tax_rate")
    def _compute_line_totals(self):
        for line in self:
            subtotal = line.product_uom_qty * line.price_unit
            line.price_subtotal = subtotal
            line.tax_amount = subtotal * (line.tax_rate / 100.0)

    @api.constrains("product_uom_qty")
    def _check_positive_quantity(self):
        for line in self:
            if line.product_uom_qty <= 0.0:
                raise ValidationError(_("Order line quantity must be strictly greater than zero."))
```

---

### 4.2 Security Definitions: ACLs & Multi-Company Record Rules

#### Access Rights: `security/ir.model.access.csv`
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_custom_order_user,custom.order.user,model_custom_order,base.group_user,1,1,1,0
access_custom_order_manager,custom.order.manager,model_custom_order,base.group_system,1,1,1,1
access_custom_order_line_user,custom.order.line.user,model_custom_order_line,base.group_user,1,1,1,0
access_custom_order_line_manager,custom.order.line.manager,model_custom_order_line,base.group_system,1,1,1,1
```

#### Multi-Company Isolation Rule: `security/security_rules.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Multi-Company Record Rule for Custom Order -->
        <record id="custom_order_company_rule" model="ir.rule">
            <field name="name">Custom Order Multi-Company Isolation</field>
            <field name="model_id" ref="model_custom_order"/>
            <field name="global" eval="True"/>
            <field name="domain_force">
                ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
            </field>
        </record>

        <!-- Multi-Company Record Rule for Custom Order Line -->
        <record id="custom_order_line_company_rule" model="ir.rule">
            <field name="name">Custom Order Line Multi-Company Isolation</field>
            <field name="model_id" ref="model_custom_order_line"/>
            <field name="global" eval="True"/>
            <field name="domain_force">
                ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
            </field>
        </record>
    </data>
</odoo>
```

---

### 4.3 Declarative XML Views & Action Windows

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Tree / List View -->
    <record id="view_custom_order_tree" model="ir.ui.view">
        <field name="name">custom.order.tree</field>
        <field name="model">custom.order</field>
        <field name="arch" type="xml">
            <tree string="Customer Orders" decoration-info="state == 'draft'" decoration-success="state == 'done'" decoration-muted="state == 'cancelled'">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="date_order"/>
                <field name="company_id" groups="base.group_multi_company"/>
                <field name="amount_untaxed" sum="Total Untaxed"/>
                <field name="amount_total" sum="Total Amount" widget="monetary"/>
                <field name="currency_id" column_invisible="True"/>
                <field name="state" widget="badge" decoration-info="state == 'draft'" decoration-warning="state == 'confirmed'" decoration-success="state == 'done'"/>
            </tree>
        </field>
    </record>

    <!-- Form View -->
    <record id="view_custom_order_form" model="ir.ui.view">
        <field name="name">custom.order.form</field>
        <field name="model">custom.order</field>
        <field name="arch" type="xml">
            <form string="Customer Order">
                <header>
                    <button name="action_confirm" string="Confirm Order" type="object" class="oe_highlight" invisible="state != 'draft'"/>
                    <button name="action_cancel" string="Cancel" type="object" invisible="state in ('done', 'cancelled')"/>
                    <field name="state" widget="statusbar" statusbar_visible="draft,confirmed,done"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1>
                            <field name="name" readonly="1"/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id" readonly="state != 'draft'"/>
                            <field name="company_id" groups="base.group_multi_company" readonly="state != 'draft'"/>
                        </group>
                        <group>
                            <field name="date_order" readonly="state != 'draft'"/>
                            <field name="currency_id" invisible="1"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Order Lines">
                            <field name="order_line_ids" readonly="state != 'draft'">
                                <tree editable="bottom">
                                    <field name="product_id"/>
                                    <field name="product_uom_qty"/>
                                    <field name="price_unit"/>
                                    <field name="tax_rate"/>
                                    <field name="price_subtotal"/>
                                    <field name="currency_id" column_invisible="True"/>
                                </tree>
                            </field>
                            <group class="oe_subtotal_footer oe_right">
                                <field name="amount_untaxed"/>
                                <field name="amount_tax"/>
                                <div class="oe_subtotal_footer_separator oe_inline o_td_label">
                                    <label for="amount_total"/>
                                </div>
                                <field name="amount_total" nolabel="1" class="oe_subtotal_footer_separator"/>
                            </group>
                        </page>
                    </notebook>
                </sheet>
                <!-- Chatter for Auditing -->
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="activity_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>

    <!-- Action Window -->
    <record id="action_custom_order" model="ir.actions.act_window">
        <field name="name">Customer Orders</field>
        <field name="res_model">custom.order</field>
        <field name="view_mode">tree,form</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Create your first customer order!
            </p>
        </field>
    </record>
</odoo>
```

---

### 4.4 High-Performance Idempotent REST Ingress Controller

```python
# custom_module/controllers/api_controller.py
"""
High-Performance, Idempotent REST API Controller for Odoo 17/18.
Demonstrates: Bearer Token Auth, Idempotency-Key validation, JSON payload parsing,
RFC 9457 error responses, and atomic record creation.
"""

from odoo import http
from odoo.http import request, Response
import json
import hashlib
import logging

_logger = logging.getLogger(__name__)


class CustomOrderApiController(http.Controller):

    def _json_error(self, status: int, title: str, detail: str) -> Response:
        """Returns standard RFC 9457 Problem Details JSON envelope."""
        payload = {
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
        }
        return Response(
            json.dumps(payload),
            status=status,
            headers=[("Content-Type", "application/problem+json")]
        )

    @http.route("/api/v1/orders", type="http", auth="public", methods=["POST"], csrf=False)
    def create_order(self, **kwargs):
        """Creates an order idempotently via external webhook/API call."""
        auth_header = request.httprequest.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return self._json_error(401, "Unauthorized", "Missing or invalid Bearer token.")

        token = auth_header.replace("Bearer ", "").strip()
        user = request.env["res.users"].sudo().search([("api_key", "=", token)], limit=1)
        if not user:
            return self._json_error(403, "Forbidden", "Invalid API Key credentials.")

        # Enforce Idempotency-Key
        idempotency_key = request.httprequest.headers.get("Idempotency-Key")
        if not idempotency_key:
            return self._json_error(400, "Bad Request", "Mandatory 'Idempotency-Key' header missing.")

        try:
            body = json.loads(request.httprequest.get_data(as_text=True))
        except (ValueError, TypeError) as exc:
            return self._json_error(400, "Invalid JSON", f"Malformed JSON request body: {str(exc)}")

        # Validate Ingress Schema
        partner_id = body.get("partner_id")
        lines_data = body.get("lines", [])

        if not partner_id or not isinstance(lines_data, list) or len(lines_data) == 0:
            return self._json_error(422, "Unprocessable Entity", "Field 'partner_id' and non-empty 'lines' are required.")

        # Compute payload hash to prevent key-hijacking with altered payloads
        payload_hash = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()

        # Check existing idempotent record
        existing_request = request.env["custom.api.idempotency"].sudo().search([
            ("key", "=", idempotency_key)
        ], limit=1)

        if existing_request:
            if existing_request.payload_hash != payload_hash:
                return self._json_error(422, "Idempotency Conflict", "Idempotency-Key reused with differing request payload.")
            return Response(
                existing_request.response_body,
                status=existing_request.response_code,
                headers=[("Content-Type", "application/json")]
            )

        # Execute order creation as authenticated user
        env = request.env(user=user)
        try:
            order_lines = []
            for item in lines_data:
                order_lines.append((0, 0, {
                    "product_id": int(item["product_id"]),
                    "product_uom_qty": float(item["quantity"]),
                    "price_unit": float(item["unit_price"]),
                }))

            order = env["custom.order"].create({
                "partner_id": partner_id,
                "order_line_ids": order_lines,
            })

            response_payload = {
                "id": order.id,
                "name": order.name,
                "amount_total": order.amount_total,
                "state": order.state,
            }
            resp_str = json.dumps(response_payload)

            # Store Idempotency Entry atomically
            request.env["custom.api.idempotency"].sudo().create({
                "key": idempotency_key,
                "payload_hash": payload_hash,
                "response_code": 201,
                "response_body": resp_str,
            })

            return Response(resp_str, status=201, headers=[("Content-Type", "application/json")])

        except Exception as exc:
            _logger.exception("Failed to process order creation via API")
            return self._json_error(500, "Internal Server Error", str(exc))
```

---

## 5. Security & Performance Considerations

### 5.1 Multi-Company Domain Leaks
In Odoo multi-company environments, querying records without company filtering permits unauthorized data exfiltration across organizational boundaries:
- **Rule**: Every operational model MUST include `company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)` and declare `_check_company_auto = True`.
- **Relational Domain**: Many2one relations to shared resources (e.g., partners, products) MUST filter by `['|', ('company_id', '=', False), ('company_id', '=', company_id)]`.

### 5.2 Preventing N+1 Query Degradation
Odoo recordsets are lazily prefetched, but nested python loops trigger individual SQL queries if not batched:
- **Bad (N+1)**:
  ```python
  # Triggers an independent SELECT query for every single line
  for order in orders:
      for line in order.order_line_ids:
          total += line.price_subtotal
  ```
- **Good (Batched Prefetch)**:
  ```python
  # Odoo pre-fetches all line records in a single SQL query
  order_lines = orders.mapped('order_line_ids')
  total = sum(order_lines.mapped('price_subtotal'))
  ```

### 5.3 PostgreSQL Connection Pooling & PgBouncer
Under heavy transactional concurrency:
1. Run Odoo behind **PgBouncer** in `transaction` pooling mode.
2. Ensure `db_maxconn` in `odoo.conf` does not exceed PostgreSQL `max_connections`.
3. Separate web workers (`workers = (2 * CPU_CORES) + 1`) from the gevent longpolling worker.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Mutating Database with Unparameterized Raw SQL
- **Violation**: `self.env.cr.execute(f"UPDATE custom_order SET state = '{new_state}' WHERE id = {order_id}")`
- **Consequence**: Catastrophic SQL Injection (OWASP A03:2021) and cache corruption.
- **Remediation**: Use ORM `order.write({'state': new_state})`. If raw SQL is unavoidable for bulk analytics, parameterize: `self.env.cr.execute("UPDATE custom_order SET state = %s WHERE id = %s", (new_state, order_id))`.

### Anti-Pattern 2: Non-Stored Computed Fields in Search Views or Groupings
- **Violation**: Filtering or grouping by a computed field without `store=True`.
- **Consequence**: Full table scan in memory; Odoo fetches every record into memory and evaluates the python compute method individually, crashing the worker process on large datasets.
- **Remediation**: Set `store=True` on computed fields used in search filters, or supply a custom `search='_search_field_name'` method.

### Anti-Pattern 3: Bypassing `mail.thread` State Tracking
- **Violation**: Performing critical financial or logistical state changes without posting to the chatter (`message_post`).
- **Consequence**: Complete loss of audit trail; inability to determine which user or automation triggered the status transition.
- **Remediation**: Inherit `mail.thread`, add `tracking=True` on state fields, and emit audit messages on state transitions.

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Model ACL Coverage** | 100% of custom models mapped | Check `ir.model.access.csv` covers all models for `base.group_user` |
| **2. Multi-Company Isolation** | Zero cross-tenant data leaks | Execute test cases switching `env.company` verifying access denial |
| **3. Automated Test Pass** | Zero failures or errors | Run `odoo-bin -c odoo.conf -d test_db -u custom_module --test-enable --stop-after-init` |
| **4. Strict Parameterization** | Zero raw string SQL concatenation | Scan with `git grep -EIn "(cr\.execute\(f\"|cr\.execute\(\".*%)"` (Zero hits) |
| **5. Double-Entry Balance** | Invariant $\sum \text{Debit} \equiv \sum \text{Credit}$ | Account move validation tests assert balance difference is zero |
| **6. Migration Backwards-Compatibility** | Backwards-compatible schema | Ensure column renames follow Expand/Contract in migration scripts |

---

*See also*: [`./erpnext.md`](./erpnext.md) for Frappe/ERPNext comparison, and [`../../sections/erp-enterprise/core-accounting-ledger.md`](../../sections/erp-enterprise/core-accounting-ledger.md) for universal double-entry general ledger invariants.
