# 🏦 Core Accounting & General Ledger Engineering (`sections/erp-enterprise/core-accounting-ledger.md`)

> **Classification**: Enterprise Accounting Engine, Financial Auditability, Regulatory Invariants  
> **Target Systems**: Universal General Ledger (GL) Engines, Enterprise ERPs (Odoo, ERPNext, SAP, NetSuite)  
> **Applicability Scope**: Financial Institutions, SaaS Billing, Multi-Entity Enterprises, Tax Compliance Gateways  
> **Governing Rules**: **R-001** (Zero TODOs), **R-038** (Zero Magic Values), **R-039** (Immutability), **R-061** (SQL Parameterization), **R-184** (Idempotency)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Domain** | Financial Accounting, General Ledger, Audit Invariants |
| **Numeric Precision** | Fixed-point arithmetic (`Decimal`), 4 decimal places for unit prices, 2 for currencies |
| **Regulatory Standards** | GAAP (Generally Accepted Accounting Principles), IFRS (International Financial Reporting Standards), PEPPOL BIS 3.0 / Factur-X |
| **Key Invariant Rules** | $\sum \text{Debits} \equiv \sum \text{Credits}$ per currency, strictly append-only posted journal entries, no destructive updates |

---

## 2. Core Philosophy / Golden Rule

> **A Posted Journal Entry is an Immutable Historical Fact; Never Mutate or Delete Posted Financial Records, Correct Exclusively via Signed Reversing Entries.**
> 
> *In financial engineering, the general ledger is the single source of truth for organizational solvency. Allowing an `UPDATE` or `DELETE` query on a posted journal entry destroys the audit trail, violates SOX/IFRS compliance, and introduces unreconcilable balance drift. Every correction must take the form of an explicit, auditable reversing journal entry with a cryptographic pointer to the original transaction.*

---

## 3. Architecture & Design Patterns

```
                          DOUBLE-ENTRY GENERAL LEDGER ENGINE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                TRANSACTION INGRESS                                     │
│            Sales Invoices, Vendor Bills, Payroll Runs, Payment Gateways                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           POSTING VALIDATOR & BALANCE CHECK                            │
│                  Assert: Sum(Debits) == Sum(Credits) within Epsilon                    │
│                  Assert: Fiscal Period is OPEN & UNLOCKED                              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        IMMUTABLE JOURNAL ENTRY (HEADER)                                │
│          • Entry UUID & Sequential Sequence (e.g. `JV/2026/00142`)                     │
│          • Transaction Date, Posting Date, Company ID, Currency ID                     │
│          • Reversal Pointer (`reversed_entry_id`) & Idempotency Key                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ 1 to N Line Split
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        GENERAL LEDGER LINES (`account_move_line`)                      │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │ Line 1: Accounts Rec │  │ Line 2: Sales Tax Pay│  │ Line 3: Revenue Account      │  │
│  │ Debit: $1,200.00     │  │ Credit: $200.00      │  │ Credit: $1,000.00            │  │
│  │ Base Debit: $1,200.00│  │ Base Credit: $200.00 │  │ Base Credit: $1,000.00       │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────────────┘  │
│                        Balance: $1,200.00 Debit == $1,200.00 Credit                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Append-Only Write
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           TRIAL BALANCE & FINANCIAL REPORTS                            │
│          Balance Sheet (Assets = Liabilities + Equity) & Profit / Loss Statements      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 The 5 Root Account Categories & Normal Balances

All Chart of Accounts (COA) nodes descend from five root types:

| Account Type | Normal Balance | Increase Mechanism | Decrease Mechanism | Reporting Statement |
|---|---|---|---|---|
| **Asset** | Debit ($+$) | Debit | Credit | Balance Sheet |
| **Liability** | Credit ($-$) | Credit | Debit | Balance Sheet |
| **Equity** | Credit ($-$) | Credit | Debit | Balance Sheet |
| **Revenue / Income** | Credit ($-$) | Credit | Debit | Profit & Loss (Income Statement) |
| **Expense** | Debit ($+$) | Debit | Credit | Profit & Loss (Income Statement) |

---

## 4. Concrete Code Examples

### 4.1 Production Double-Entry Ledger Engine with Multi-Currency & Reversing Entries

```python
"""
Enterprise Immutable General Ledger Engine.
Implements: Double-Entry Balance Verification, Decimal Fixed-Point Arithmetic,
Multi-Currency Exchange Rate Conversion, Roundoff Penny Balancing,
and Append-Only Reversing Entries.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from enum import Enum
from typing import Optional
import datetime
import uuid


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class PostingStatus(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class AccountingError(Exception):
    """Base exception for accounting domain violations."""
    pass


class UnbalancedJournalEntryError(AccountingError):
    """Raised when total debits do not equal total credits."""
    pass


class ClosedPeriodError(AccountingError):
    """Raised when posting to a closed or locked accounting period."""
    pass


@dataclass(frozen=True)
class Account:
    id: str
    code: str
    name: str
    account_type: AccountType
    currency: str
    company_id: str


@dataclass(frozen=True)
class JournalLine:
    account_id: str
    description: str
    debit: Decimal
    credit: Decimal
    currency: str
    exchange_rate: Decimal  # Rate to company functional currency
    base_debit: Decimal = field(init=False)
    base_credit: Decimal = field(init=False)

    def __post_init__(self):
        if self.debit < Decimal("0.00") or self.credit < Decimal("0.00"):
            raise AccountingError("Debit and credit amounts cannot be negative.")
        if self.debit > Decimal("0.00") and self.credit > Decimal("0.00"):
            raise AccountingError("A single line cannot contain both non-zero debit and credit.")
        if self.debit == Decimal("0.00") and self.credit == Decimal("0.00"):
            raise AccountingError("A line must have non-zero debit or credit.")

        # Compute functional/base currency equivalents
        base_deb = (self.debit * self.exchange_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        base_cred = (self.credit * self.exchange_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        object.__setattr__(self, "base_debit", base_deb)
        object.__setattr__(self, "base_credit", base_cred)


@dataclass
class JournalEntry:
    id: str
    company_id: str
    entry_number: str
    posting_date: datetime.date
    lines: list[JournalLine]
    status: PostingStatus = PostingStatus.DRAFT
    reversed_entry_id: Optional[str] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def validate_balance(self):
        """Verifies that the transaction balances in functional currency."""
        total_base_debit = sum((line.base_debit for line in self.lines), Decimal("0.00"))
        total_base_credit = sum((line.base_credit for line in self.lines), Decimal("0.00"))

        if total_base_debit != total_base_credit:
            diff = total_base_debit - total_base_credit
            raise UnbalancedJournalEntryError(
                f"Journal Entry {self.entry_number} is unbalanced in base currency! "
                f"Total Debit: {total_base_debit}, Total Credit: {total_base_credit}, Difference: {diff}"
            )


class GeneralLedgerService:
    def __init__(self, locked_until_date: datetime.date, roundoff_account_id: str):
        self.locked_until_date = locked_until_date
        self.roundoff_account_id = roundoff_account_id
        self._entries: dict[str, JournalEntry] = {}

    def post_entry(self, entry: JournalEntry) -> JournalEntry:
        """Atomically validates, balances, and locks a journal entry."""
        if entry.posting_date <= self.locked_until_date:
            raise ClosedPeriodError(
                f"Cannot post to date {entry.posting_date}; fiscal period is locked until {self.locked_until_date}."
            )

        if not entry.lines or len(entry.lines) < 2:
            raise AccountingError("A valid double-entry transaction must contain at least 2 lines.")

        # 1. Roundoff Adjustment: Handle currency conversion penny imbalances
        total_debit = sum((l.base_debit for l in entry.lines), Decimal("0.00"))
        total_credit = sum((l.base_credit for l in entry.lines), Decimal("0.00"))
        imbalance = total_debit - total_credit

        if Decimal("0.00") < abs(imbalance) <= Decimal("0.05"):
            # Automatically allocate minor penny roundoff to dedicated Roundoff Account
            if imbalance > 0:
                # Need credit to balance
                entry.lines.append(JournalLine(
                    account_id=self.roundoff_account_id,
                    description="Currency Exchange Roundoff Adjustment",
                    debit=Decimal("0.00"),
                    credit=imbalance,
                    currency="USD",
                    exchange_rate=Decimal("1.000000"),
                ))
            else:
                # Need debit to balance
                entry.lines.append(JournalLine(
                    account_id=self.roundoff_account_id,
                    description="Currency Exchange Roundoff Adjustment",
                    debit=abs(imbalance),
                    credit=Decimal("0.00"),
                    currency="USD",
                    exchange_rate=Decimal("1.000000"),
                ))

        # 2. Strict Balance Invariant Assertion
        entry.validate_balance()

        # 3. Mark Immutable & Persist
        entry.status = PostingStatus.POSTED
        self._entries[entry.id] = entry
        return entry

    def create_reversing_entry(
        self,
        original_entry_id: str,
        reversal_date: datetime.date,
        reason: str,
    ) -> JournalEntry:
        """
        Generates an immutable reversing journal entry.
        Swaps debits and credits cleanly to nullify the financial impact.
        """
        original = self._entries.get(original_entry_id)
        if not original:
            raise AccountingError(f"Original entry {original_entry_id} not found.")
        if original.status != PostingStatus.POSTED:
            raise AccountingError("Only POSTED entries can be reversed.")

        reversing_lines: list[JournalLine] = []
        for line in original.lines:
            # Invert: Swap debit and credit
            reversing_lines.append(JournalLine(
                account_id=line.account_id,
                description=f"Reversal of {original.entry_number}: {reason}",
                debit=line.credit,
                credit=line.debit,
                currency=line.currency,
                exchange_rate=line.exchange_rate,
            ))

        reversing_entry = JournalEntry(
            id=str(uuid.uuid4()),
            company_id=original.company_id,
            entry_number=f"REV-{original.entry_number}",
            posting_date=reversal_date,
            lines=reversing_lines,
            reversed_entry_id=original.id,
        )

        posted_reversal = self.post_entry(reversing_entry)
        original.status = PostingStatus.REVERSED
        return posted_reversal
```

---

## 5. Security & Performance Considerations

### 5.1 Concurrency & Period Locking
Under high transaction concurrency (e.g., automated batch invoicing or subscription renewals), race conditions can post entries into periods currently undergoing fiscal closure:
- **Locking Invariant**: Fiscal period tables MUST be queried with `SELECT FOR UPDATE` or verified against Redis distributed locks before committing transactions.
- **Sequential Sequence Numbering**: Sequence numbers (`INV/2026/0001`) must not leave gaps in legal jurisdictions requiring continuous sequence auditability. Use PostgreSQL sequences or atomic database counters.

### 5.2 Multi-Currency FX Gain / Loss Realization
When an invoice is issued at exchange rate $R_1$ and settled later at rate $R_2$:
- The difference $(\text{Amount} \times R_2) - (\text{Amount} \times R_1)$ is non-zero.
- The engine MUST generate an automatic balancing line to **Foreign Exchange Gain / Loss Account** to maintain zero balance drift.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Floating-Point Math for Monetary Values
- **Violation**: Using IEEE 754 floating-point numbers (`float` or `double`) to represent currency amounts.
- **Consequence**: `0.1 + 0.2 = 0.30000000000000004` causes journal entries to fail balance validation and leaks fractional cents across thousands of transactions.
- **Remediation**: Use arbitrary-precision fixed-point decimals (`Decimal` in Python, `BigDecimal` in Java, or integer micro-units in Go/SQL).

### Anti-Pattern 2: Deleting or Modifying Historical Journal Entries
- **Violation**: Executing `DELETE FROM account_move WHERE id = 123` to correct an invoicing mistake.
- **Consequence**: Legal violation of audit standards (SOX, IFRS). Breaches sequential voucher numbering and creates unresolvable reconciliation discrepancies with bank accounts.
- **Remediation**: Post a signed, reversing journal entry.

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Double-Entry Balance** | $\sum \text{Debit} - \sum \text{Credit} \equiv 0$ | Automated test verifies 0 balance delta across all posted vouchers |
| **2. Fixed-Point Precision** | Zero floating-point usage | `git grep -EIn "(float\(|double\b)" src/accounting/` returns 0 hits |
| **3. Period Lock Enforcement** | Rejection of closed-period posts | Test posts with `posting_date < locked_date` throw `ClosedPeriodError` |
| **4. Reversal Integrity** | Net balance nullified | Verify `Original + Reversal == 0.00` across all affected accounts |
| **5. Sequence Continuity** | Zero gaps in sequence numbers | Audit script checks monotonic increment without missing numbers |

---

*See also*: [`./inventory-supply-chain.md`](./inventory-supply-chain.md) for perpetual inventory valuation, and [`../../frameworks/erp/odoo.md`](../../frameworks/erp/odoo.md) for Odoo account.move implementation.
