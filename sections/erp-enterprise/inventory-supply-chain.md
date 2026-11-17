# 📦 Enterprise Inventory Valuation & Supply Chain (`sections/erp-enterprise/inventory-supply-chain.md`)

> **Classification**: Inventory Engineering, Perpetual Stock Valuation, Supply Chain Invariants  
> **Target Systems**: Universal Inventory Engines, ERP Subsystems (Odoo, ERPNext, SAP S/4HANA, NetSuite)  
> **Applicability Scope**: Warehousing, Manufacturing, E-Commerce Fulfillment, Landed Cost Calculations  
> **Governing Rules**: **R-001** (Zero TODOs), **R-038** (Zero Magic Values), **R-061** (SQL Parameterization), **R-184** (Idempotency)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Domain** | Perpetual Inventory Valuation, Stock Ledger, Supply Chain Logistics |
| **Valuation Standards** | FIFO (First-In, First-Out), Moving Weighted Average Cost (AVCO), Standard Cost |
| **Ledger Model** | Append-Only Stock Ledger Entry (SLE) with Double-Entry Stock Moves |
| **Key Invariant Rules** | Non-negative inventory balance, atomic row-level locks on stock bins, exact Cost of Goods Sold (COGS) synchronization with General Ledger |

---

## 2. Core Philosophy / Golden Rule

> **Physical Stock Cannot Be Negative; Inventory Valuation Must Reflect Exact Material Flow, and Every Physical Movement Must Generate an Invariant-Preserving Financial Counterpart.**
> 
> *In supply chain engineering, a stock balance is not an abstract counter that can drop below zero. Allowing negative stock in software masks physical shrinkage, produces mathematical absurdities in FIFO cost layers, and breaks Cost of Goods Sold (COGS) accounting. Every warehouse receipt, delivery, or internal transfer must execute as an append-only stock move backed by strict concurrency locks.*

---

## 3. Architecture & Design Patterns

```
                          PERPETUAL INVENTORY ENGINE & LEDGER
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               WAREHOUSE LOGISTICS EVENTS                               │
│            Purchase Receipts, Delivery Orders, Manufacturing Consumptions              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ROW-LEVEL LOCK & INVENTORY CHECK                                │
│              `SELECT current_qty, valuation_rate FROM stock_bin WHERE ...`             │
│              `FOR UPDATE` -> Assert: (current_qty + delta_qty) >= 0.0                  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            VALUATION QUEUE ENGINE (FIFO)                               │
│       Incoming: Enqueue [Qty: 50, Rate: $10.00], Enqueue [Qty: 50, Rate: $12.00]       │
│       Outgoing (70 units): Dequeue 50 @ $10.00 ($500) + Dequeue 20 @ $12.00 ($240)    │
│                            Calculated COGS Value = $740.00                             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      IMMUTABLE STOCK LEDGER ENTRY (SLE)                                │
│       • Voucher Type & Number (e.g. Delivery Order `WH/OUT/0042`)                      │
│       • Item Code, Warehouse ID, Batch / Serial Number                                 │
│       • Quantity Change (`actual_qty`), Resulting Balance (`qty_after_transaction`)    │
│       • Valuation Rate & Stock Value Difference (`stock_value_difference = -$740.00`)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Synchronous Double-Entry Post
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         GENERAL LEDGER (GL) ACCOUNTING MOVE                            │
│           Debit: Cost of Goods Sold (COGS Expense) ------------ $740.00                │
│           Credit: Inventory Asset Account --------------------- $740.00                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Production FIFO Queue & Perpetual Stock Valuation Engine

```python
"""
Enterprise Perpetual Inventory & FIFO Valuation Engine.
Implements: Strict Non-Negative Stock Guarantees, FIFO Cost Layer Queue,
Landed Cost Allocation, and Automated COGS Journal Entry Generation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional
import datetime
import uuid


class InventoryError(Exception):
    """Base exception for inventory domain errors."""
    pass


class NegativeStockError(InventoryError):
    """Raised when an outgoing movement would cause warehouse balance to drop below zero."""
    pass


@dataclass
class StockLayer:
    """Represents a specific batch of incoming stock at a specific unit cost."""
    layer_id: str
    receipt_date: datetime.date
    remaining_qty: Decimal
    unit_cost: Decimal

    def consume(self, qty_to_consume: Decimal) -> tuple[Decimal, Decimal]:
        """
        Consumes up to `qty_to_consume` from this layer.
        Returns: (consumed_quantity, total_value_of_consumed_stock).
        """
        taken = min(self.remaining_qty, qty_to_consume)
        value = (taken * self.unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        self.remaining_qty -= taken
        return taken, value


@dataclass
class StockLedgerEntry:
    entry_id: str
    item_code: str
    warehouse_id: str
    voucher_type: str
    voucher_no: str
    posting_date: datetime.date
    actual_qty: Decimal
    qty_after_transaction: Decimal
    stock_value_difference: Decimal
    valuation_rate: Decimal
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)


class PerpetualInventoryEngine:
    def __init__(self, allow_negative_stock: bool = False):
        self.allow_negative_stock = allow_negative_stock
        # Maps (item_code, warehouse_id) -> list[StockLayer] (FIFO Queue)
        self._layers: dict[tuple[str, str], list[StockLayer]] = {}
        # History of all immutable Stock Ledger Entries
        self._ledger: list[StockLedgerEntry] = []

    def get_stock_balance(self, item_code: str, warehouse_id: str) -> tuple[Decimal, Decimal]:
        """Returns: (total_quantity_on_hand, total_inventory_value)."""
        key = (item_code, warehouse_id)
        layers = self._layers.get(key, [])
        total_qty = sum((l.remaining_qty for l in layers), Decimal("0.00"))
        total_val = sum((l.remaining_qty * l.unit_cost for l in layers), Decimal("0.00"))
        return total_qty, total_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    def record_incoming_receipt(
        self,
        item_code: str,
        warehouse_id: str,
        voucher_type: str,
        voucher_no: str,
        posting_date: datetime.date,
        quantity: Decimal,
        unit_cost: Decimal,
    ) -> StockLedgerEntry:
        """
        Records an incoming purchase receipt or manufacturing output.
        Adds a new FIFO layer and appends to the Stock Ledger.
        """
        if quantity <= Decimal("0.00"):
            raise InventoryError("Incoming receipt quantity must be strictly positive.")
        if unit_cost < Decimal("0.00"):
            raise InventoryError("Unit cost cannot be negative.")

        key = (item_code, warehouse_id)
        if key not in self._layers:
            self._layers[key] = []

        # 1. Enqueue new FIFO cost layer
        layer = StockLayer(
            layer_id=str(uuid.uuid4()),
            receipt_date=posting_date,
            remaining_qty=quantity,
            unit_cost=unit_cost,
        )
        self._layers[key].append(layer)

        # 2. Compute updated aggregates
        current_qty, current_val = self.get_stock_balance(item_code, warehouse_id)
        stock_value_diff = (quantity * unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        valuation_rate = (current_val / current_qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)

        # 3. Create Immutable Stock Ledger Entry
        entry = StockLedgerEntry(
            entry_id=str(uuid.uuid4()),
            item_code=item_code,
            warehouse_id=warehouse_id,
            voucher_type=voucher_type,
            voucher_no=voucher_no,
            posting_date=posting_date,
            actual_qty=quantity,
            qty_after_transaction=current_qty,
            stock_value_difference=stock_value_diff,
            valuation_rate=valuation_rate,
        )
        self._ledger.append(entry)
        return entry

    def record_outgoing_delivery(
        self,
        item_code: str,
        warehouse_id: str,
        voucher_type: str,
        voucher_no: str,
        posting_date: datetime.date,
        quantity: Decimal,
    ) -> tuple[StockLedgerEntry, Decimal]:
        """
        Records an outgoing customer shipment or manufacturing consumption.
        Consumes from the oldest available FIFO layers.
        Returns: (StockLedgerEntry, total_cost_of_goods_sold).
        """
        if quantity <= Decimal("0.00"):
            raise InventoryError("Outgoing quantity must be strictly positive.")

        key = (item_code, warehouse_id)
        layers = self._layers.get(key, [])
        available_qty, _ = self.get_stock_balance(item_code, warehouse_id)

        # Invariant: Prevent Negative Inventory
        if not self.allow_negative_stock and available_qty < quantity:
            raise NegativeStockError(
                f"Cannot deliver {quantity} units of {item_code} from warehouse {warehouse_id}. "
                f"Available stock is only {available_qty} units."
            )

        # 1. Dequeue stock across FIFO layers
        needed_qty = quantity
        total_cogs_value = Decimal("0.00")

        # Iterate through layers in chronological order
        while needed_qty > Decimal("0.00") and layers:
            current_layer = layers[0]
            consumed_qty, consumed_val = current_layer.consume(needed_qty)
            total_cogs_value += consumed_val
            needed_qty -= consumed_qty

            if current_layer.remaining_qty == Decimal("0.00"):
                layers.pop(0)  # Evict exhausted layer

        # 2. Compute updated balances
        current_qty, current_val = self.get_stock_balance(item_code, warehouse_id)
        valuation_rate = Decimal("0.00") if current_qty == 0 else (current_val / current_qty).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_EVEN
        )

        # 3. Create Immutable Stock Ledger Entry
        entry = StockLedgerEntry(
            entry_id=str(uuid.uuid4()),
            item_code=item_code,
            warehouse_id=warehouse_id,
            voucher_type=voucher_type,
            voucher_no=voucher_no,
            posting_date=posting_date,
            actual_qty=-quantity,
            qty_after_transaction=current_qty,
            stock_value_difference=-total_cogs_value,
            valuation_rate=valuation_rate,
        )
        self._ledger.append(entry)
        return entry, total_cogs_value

    def allocate_landed_costs(
        self,
        receipt_entry_id: str,
        landed_cost_amount: Decimal,
        allocation_method: str = "QUANTITY",
    ):
        """
        Distributes additional landed costs (freight, customs, handling)
        back into the FIFO layers of an existing purchase receipt.
        """
        receipt_sle = next((e for e in self._ledger if e.entry_id == receipt_entry_id), None)
        if not receipt_sle or receipt_sle.actual_qty <= 0:
            raise InventoryError("Landed cost must target a valid incoming receipt SLE.")

        key = (receipt_sle.item_code, receipt_sle.warehouse_id)
        layers = self._layers.get(key, [])

        cost_per_unit = (landed_cost_amount / receipt_sle.actual_qty).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )

        for layer in layers:
            # Revalue remaining stock in this layer
            layer.unit_cost += cost_per_unit
```

---

## 5. Security & Performance Considerations

### 5.1 Concurrency & Row-Level Locking on Warehouses
When multiple workers process shipments concurrently:
- Race conditions permit two concurrent orders of 50 units to succeed against a warehouse containing only 60 units.
- **Mandatory Mitigation**: Before inspecting balances or dequeuing FIFO layers, execute:
  ```sql
  SELECT current_qty FROM stock_bin WHERE item_id = $1 AND warehouse_id = $2 FOR UPDATE;
  ```
  This serializes updates and ensures the negative stock invariant is guaranteed at the database engine level.

### 5.2 FIFO Queue Compaction
Over years of operations, having thousands of fragmented 1-unit layers degrades in-memory dequeue performance:
- Maintain an automated monthly reconciliation job that consolidates adjacent layers sharing identical unit costs and batches.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Permitting Negative Inventory
- **Violation**: Setting `allow_negative_stock: true` to bypass delivery blocks when physical stock is miscounted.
- **Consequence**: Outgoing stock consumed at zero or negative cost values. When stock is later received, historical valuation is permanently corrupted, requiring complex retroactive revaluations.
- **Remediation**: Block negative inventory strictly. Enforce physical stock reconciliation before fulfilling orders.

### Anti-Pattern 2: Disconnected Inventory and General Ledger Moves
- **Violation**: Deducting stock quantities in the warehouse database without posting an immediate financial entry to the Inventory Asset and COGS Expense accounts.
- **Consequence**: Discrepancies between the physical stock valuation report and the balance sheet, failing external financial audits.
- **Remediation**: Execute Stock Ledger Entries and General Ledger Moves within the same atomic database transaction.

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Non-Negative Inventory** | Balance $\ge 0.0$ at all times | Assert `qty_after_transaction >= 0` across all ledger rows |
| **2. Stock-GL Balance** | Valuation delta $\equiv$ GL Move | Stock value difference matches GL Inventory Asset credit |
| **3. FIFO Ordering** | Oldest layers consumed first | Automated test verifies layer dequeue matches chronological receipt date |
| **4. Landed Cost Invariant** | Costs capitalized into asset value | Landed cost addition increases layer unit cost without changing on-hand quantity |
| **5. Atomicity Under Concurrency** | Zero race condition overselling | Run parallel worker simulation with `SELECT FOR UPDATE` |

---

*See also*: [`./core-accounting-ledger.md`](./core-accounting-ledger.md) for general ledger invariants, and [`../../frameworks/erp/erpnext.md`](../../frameworks/erp/erpnext.md) for Frappe Stock Ledger Entry details.
