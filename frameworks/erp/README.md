# 🏢 Enterprise Resource Planning (ERP) Frameworks (`frameworks/erp/`)

> **Classification**: Enterprise Application Architecture, Business Process Automation & Systems Integration  
> **Target Systems**: Odoo 17/18 Community & Enterprise, Frappe Framework v15/v16 & ERPNext  
> **Scope**: Business Logic Engines, Document Lifecycles, Financial Ledgers, Inventory Workflows, and Customization Architectures  

---

## 1. Directory Overview

Modern enterprise software engineering relies heavily on extensible ERP frameworks to manage transactional business reality—accounting, manufacturing, supply chain, CRM, human resources, and point-of-sale. 

Unlike generic web frameworks, ERP platforms operate as **domain application operating systems**. They provide declarative metadata engines, automated object-relational mapping, strict role-based access control (RBAC), multi-company data isolation, and append-only financial invariants.

```
frameworks/erp/
├── README.md               # Directory overview and architectural comparison
├── odoo.md                 # Odoo 17/18 Architecture, Models/ORM, XML Views, Security, APIs
└── erpnext.md              # Frappe Framework v15/v16, DocTypes, Hooks, Server/Client Scripts, REST
```

---

## 2. Architectural Comparison: Odoo vs. ERPNext (Frappe)

| Dimension | Odoo (17 / 18) | ERPNext / Frappe (v15 / v16) |
|---|---|---|
| **Primary Language** | Python 3.10+ & JavaScript (OWL - Odoo Web Library) | Python 3.10+ & JavaScript (Frappe Desk UI) |
| **Database Engine** | PostgreSQL (strict relational schema with foreign keys) | MariaDB / MySQL (or PostgreSQL), relational with JSON metadata |
| **Metadata Engine** | Python Model Classes (`models.Model`) + XML View Definitions | Declarative JSON DocTypes stored in repo & `tabDocType` tables |
| **Inheritance Model** | Classical Python inheritance + Model Extension (`_inherit`) | DocType customization, Server Scripts, and `hooks.py` event overrides |
| **Frontend Framework** | OWL (Odoo Web Library - Component-based reactive UI) | Desk UI (jQuery / Vue / vanilla JS components with real-time SSE) |
| **Accounting Invariant** | Double-entry journal entries (`account.move` & `account.move.line`) | Double-entry general ledger entries (`GL Entry`) |
| **Inventory Engine** | Double-entry stock moves (`stock.move` & `stock.valuation.layer`) | Double-entry stock ledger entries (`Stock Ledger Entry`) |
| **Security Architecture** | Model ACLs (`ir.model.access.csv`) + Record Rules (`ir.rule`) | Role Permission Manager + User Permissions (DocType level) |
| **Multi-Tenancy** | Database-per-tenant or Multi-Company row-level domain filtering | Multi-tenant Bench (Site-per-tenant with separate DBs) |
| **Background Jobs** | Odoo Cron (`ir.cron`) + gevent/longpolling workers | Redis Queue (`rq`) with `frappe.enqueue` across worker queues |

---

## 3. Related Systems & Enterprise Deep Dives

For cross-cutting ERP invariants, consult the dedicated enterprise sections:
- [`../../sections/erp-enterprise/core-accounting-ledger.md`](../../sections/erp-enterprise/core-accounting-ledger.md) — Double-entry immutability, foreign currency revaluation, fiscal year closing, and PEPPOL/tax compliance.
- [`../../sections/erp-enterprise/inventory-supply-chain.md`](../../sections/erp-enterprise/inventory-supply-chain.md) — Perpetual vs periodic inventory, FIFO valuation queues, landed costs, and batch/serial tracking.
