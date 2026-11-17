# 🏛️ Enterprise ERP Foundations & Ledger Invariants (`sections/erp-enterprise/`)

> **Classification**: Cross-Cutting Enterprise Architectural Standard & Financial Invariants  
> **Target Systems**: Universal General Ledger Engines, Perpetual Inventory Subsystems, ERP Integration Gateways  
> **Applicability Scope**: Odoo, ERPNext, SAP S/4HANA, NetSuite, Microsoft Dynamics 365, Custom Enterprise Backends  

---

## 1. Directory Overview

Generic CRUD architectures collapse when exposed to the rigid mathematical and regulatory requirements of enterprise business systems. 

Enterprise software engineering requires **immutable append-only auditability**, **zero-downtime fiscal closures**, **deterministic currency revaluation**, and **perpetual inventory queue mechanics**.

```
sections/erp-enterprise/
├── README.md                     # Directory overview and core financial invariants
├── core-accounting-ledger.md     # Double-Entry Ledger, Balance Invariants, FX Revaluation & PEPPOL
└── inventory-supply-chain.md     # FIFO Queues, Moving Average, Perpetual Inventory & Landed Costs
```

---

## 2. Universal Enterprise Invariants

Regardless of whether an organization deploys Odoo, ERPNext, or custom microservices, the following mathematical invariants are non-negotiable:

1. **Double-Entry Balance Invariant**:
   $$\sum_{i} \text{Debit}_i \equiv \sum_{i} \text{Credit}_i \quad \forall \text{ Journal Entry}$$
2. **Immutable Append-Only Audit Trail**:
   Posted financial and stock transactions MUST NEVER be updated or deleted in place. Errors are resolved exclusively by posting **Reversing Journal Entries** or **Compensating Stock Adjustments**.
3. **Strict Currency Precision & Roundoff Allocation**:
   Monetary calculations must use fixed-point arithmetic (`Decimal`) with explicit rounding modes (`ROUND_HALF_UP` or `ROUND_HALF_EVEN`). Roundoff pennies must be allocated to an explicit Roundoff Expense/Income account.
4. **Non-Negative Perpetual Inventory**:
   Inventory quantities in physical warehouses cannot drop below zero in physical reality. Stock consumption transactions must acquire row-level locks (`SELECT FOR UPDATE`) on bin balances to prevent race conditions.
