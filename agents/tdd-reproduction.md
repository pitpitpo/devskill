# 🔴 Red-Green TDD Bug Reproduction Protocol (`tdd-reproduction.md`)

> **Standard Identifier**: `AGENT-TDD-REPRO-001`  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Test Engineers, Core Maintainers  
> **Classification**: Level 5 Autonomous Quality & Defect Remediation Standard  
> **Prerequisites**: Familiarity with Unit & Integration Testing, Jest/Vitest/PyTest/Go Test  

---

## 1. Title, Metadata & Scope

When a bug report or regression is filed in a software system, the most common AI failure pattern is **speculative fixing**: jumping directly into production code, tweaking logic based on intuition, and claiming the issue is resolved without ever having reproduced the defect. This causes:
1. **False Positives**: Modifying code that wasn't actually causing the reported behavior.
2. **Hidden Regressions**: Breaking adjacent features while blindly patching a symptom.
3. **Unverifiable Fixes**: Inability to mathematically prove that the fix cured the underlying defect.

This protocol establishes the mandatory **Red-Green TDD Bug Reproduction Protocol**. Under this protocol, an autonomous agent is strictly forbidden from modifying production application code for a defect until it has written a deterministic test that reproduces the bug, executed it in the terminal, and captured the failing assertion (Red).

---

## 2. Core Philosophy & Golden Rules

> **"No Production Edit Without Prior Red Proof. If You Have Not Observed the Test Fail Against the Unmodified Codebase, Your Fix is Unproven Speculation."**

### The Four Cardinal Rules of Defect Triage

1. **Reproduction Before Modification**: Always create or run a test case that isolates the exact reported defect. Run it against unmodified code and verify exit code != 0.
2. **Deterministic Assertions**: The reproduction test must fail with the *exact* symptom or error signature described in the issue (e.g., `AssertionError: expected 400 to equal 200`), not an unrelated syntax or import error.
3. **Minimal Surgical Remediation**: Modify only the code necessary to turn the failing test green without altering the test's assertions.
4. **Permanent Regression Shield**: Once verified green, the reproduction test must be committed into the test suite permanently to prevent future regressions.

---

## 3. Architecture: The 5-Phase Defect Remediation Lifecycle

```
                 THE RED-GREEN REPRODUCTION STATE MACHINE

 ┌────────────────────────────────────────────────────────────────────────┐
 │ Phase 1: TRIAGE & ISOLATION                                            │
 │ • Read error report, stack trace, and user inputs                      │
 │ • Identify the boundary layer (HTTP endpoint, domain entity, database) │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Phase 2: WRITE REPRODUCTION TEST                                       │
 │ • Add a targeted test case to tests/repro/ or adjacent .test.ts file   │
 │ • Provide input conditions that trigger the reported defect            │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Phase 3: EXECUTE & VERIFY RED (Mandatory Proof Step)                   │
 │ • Run: npm test -- tests/target.test.ts                                │
 │ • OBSERVE: Exit code != 0                                              │
 │ • Capture exact failing assertion and stack trace in execution log     │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Phase 4: SURGICAL FIX (Phase 4 Implementer)                            │
 │ • Edit ONLY production code files to satisfy the failing invariant     │
 │ • DO NOT modify the assertions of the reproduction test!               │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Phase 5: EXECUTE & VERIFY GREEN                                        │
 │ • Re-run: npm test -- tests/target.test.ts (Exit code 0)               │
 │ • Run full regression suite: npm test (All tests pass)                 │
 │ • Commit test + fix together: fix(scope): resolve ...                  │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Walkthrough: Defect Remediation

### 4.1 Scenario: Negative Quantity Bypass in Shopping Cart

**Issue Report**: *Users can submit negative quantities during checkout, resulting in credits to their account balance instead of charges.*

#### Step 1: Write Reproduction Test (Red Phase)
```typescript
// tests/unit/cart-calculator.test.ts
import { describe, it, expect } from "vitest";
import { calculateCartTotal, CartItem } from "@/domain/cart";

describe("Cart Total Calculation - Regression Suite", () => {
  it("REPRO: should reject or throw when an item has a negative quantity", () => {
    const invalidItems: CartItem[] = [
      { id: "item-1", unitPriceCents: 5000, quantity: -2 }, // Exploitative negative quantity
    ];

    // Assert that the domain function rejects negative quantities
    expect(() => calculateCartTotal(invalidItems)).toThrowError(
      /Quantity must be a positive integer/
    );
  });
});
```

#### Step 2: Execute and Capture RED Proof
```bash
$ npm test -- tests/unit/cart-calculator.test.ts

FAIL tests/unit/cart-calculator.test.ts > Cart Total Calculation > REPRO: should reject...
AssertionError: expected [Function] to throw error matching /Quantity must be a positive integer/ but got -10000

Test Files  1 failed (1)
Tests       1 failed (1)
Exit Code:  1
```
*Proof Captured*: The test fails with exit code 1. The bug is confirmed to exist.

#### Step 3: Apply Minimal Surgical Fix
```typescript
// src/domain/cart.ts
export interface CartItem {
  id: string;
  unitPriceCents: number;
  quantity: number;
}

export function calculateCartTotal(items: CartItem[]): number {
  let total = 0;
  for (const item of items) {
    // Surgical fix: Validate quantity invariant
    if (!Number.isInteger(item.quantity) || item.quantity <= 0) {
      throw new Error(`Invalid cart item ${item.id}: Quantity must be a positive integer`);
    }
    total += item.unitPriceCents * item.quantity;
  }
  return total;
}
```

#### Step 4: Execute and Capture GREEN Proof
```bash
$ npm test -- tests/unit/cart-calculator.test.ts

PASS tests/unit/cart-calculator.test.ts
  ✓ Cart Total Calculation - Regression Suite > REPRO: should reject or throw when an item has a negative quantity (2ms)

Test Files  1 passed (1)
Tests       1 passed (1)
Exit Code:  0
```

#### Step 5: Full Regression Run
```bash
$ npm test

Test Files  24 passed (24)
Tests       192 passed (192)
Exit Code:  0
```

---

## 5. Security & Edge Case Reproduction

When reproducing critical bugs, ensure the reproduction test accounts for security boundary vectors:

| Bug Category | Reproduction Technique | Invariant Under Test |
|---|---|---|
| **SQL / NoSQL Injection** | Pass strings containing `' OR '1'='1` or `$where` | Parser must reject or parameterize; assert query cannot bypass auth |
| **Race Conditions (TOCTOU)** | Spawn parallel asynchronous workers hitting the same resource simultaneously | Ensure database row lock (`SELECT FOR UPDATE`) or atomic CAS prevents double-spend |
| **Memory / Goroutine Leaks** | Loop operation 1,000 times, check active goroutines or RSS memory | `runtime.NumGoroutine()` must return to baseline after worker completion |
| **Replay Attacks** | Re-send identical signed payload with timestamp > 300s old | HMAC signature validator must return `401 Unauthorized` |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Manifestation | Consequence | Remediated Standard |
|---|---|---|---|
| **Weakening the Test to Pass** | Modifying `expect(res.status).toBe(200)` to `toBe(500)` so test passes | Hides the bug, converts failure into false victory | NEVER modify test assertions to match incorrect code behavior |
| **Skipping the Red Phase** | Editing code first, then adding a passing test | No proof the test actually checks the defect; test could be tautological | Always execute test BEFORE editing code to witness exit code 1 |
| **Tautological Assertions** | `expect(actual !== undefined).toBe(true)` | Test never fails even if domain logic crashes | Assert exact returned values, types, and error messages |
| **Deleting Existing Tests** | Removing a failing existing test to make CI green | Silently drops regression coverage | Investigate why existing test broke; fix code to satisfy all tests |

---

## 7. Verification Checklist & Production Audit

Before closing any defect triage task:

- [ ] **Red Phase Proven**: Documented CLI execution showing test failure with exit code != 0 on unmodified codebase.
- [ ] **Exact Error Signature**: Failing test matches the exact symptom reported in the defect.
- [ ] **Zero Test Assertion Tweaking**: The reproduction test's assertions remained unchanged during the fix.
- [ ] **Green Phase Proven**: Documented CLI execution showing reproduction test passes with exit code 0.
- [ ] **Full Suite Regression Pass**: All existing unit, integration, and E2E tests pass cleanly.
- [ ] **Permanence**: Reproduction test is checked into version control under appropriate test directory.
