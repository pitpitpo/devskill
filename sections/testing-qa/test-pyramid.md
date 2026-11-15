# 🧪 The Industrial Test Pyramid: Unit, Integration, Contract & E2E Strategies

> **Standard Identifier**: `SEC-TESTING-PYRAMID-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: QA Architects, Software Engineers, Tech Leads  
> **Classification**: Level 4 Testing & Quality Assurance Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Structure your test suite according to the Test Pyramid: 70% Unit, 20% Integration, 10% End-to-End. High test coverage with brittle, slow E2E tests creates a flaky deployment pipeline. Test business logic in pure unit tests, verify boundaries with real Testcontainers in integration tests, and reserve E2E tests for critical smoke paths.*

Flaky tests erode engineer confidence and slow down release velocity. Adhering to the Test Pyramid ensures fast local feedback loops (< 5 seconds for unit tests) while guaranteeing realistic environment parity during CI.

---

## 2. The Testing Pyramid Architecture

```
                               ┌─────────────┐
                               │     E2E     │  ~10% (Critical journeys, Playwright)
                               │   (Slow)    │
                               ├─────────────┤
                               │ INTEGRATION │  ~20% (Testcontainers, Real DB/Redis)
                               │  (Medium)   │
                               ├─────────────┤
                               │    UNIT     │  ~70% (Domain logic, pure functions,
                               │   (Fast)    │        fast, deterministic)
                               └─────────────┘
```

| Layer | Proportion | Execution Time | Environment Parity | Primary Focus | Tooling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unit** | ~70% | Milliseconds | Isolated / In-Memory | Pure domain logic, edge cases, algorithms | Vitest, Jest, Pytest, Go Test |
| **Integration** | ~20% | Seconds | High (Real containers) | Repositories, DB transactions, external APIs | Testcontainers, Supertest |
| **E2E** | ~10% | Minutes | Full production-like | Checkout flows, auth flows, critical user journeys | Playwright, Cypress |

---

## 3. Test Double Taxonomy: When to Mock vs Real

| Test Double | Definition | Usage Guideline |
| :--- | :--- | :--- |
| **Dummy** | Passed around but never actually used (e.g. empty string parameter) | Fill required method arguments |
| **Stub** | Provides canned answers to calls made during test | Unit tests needing static mock data |
| **Spy** | Records information about how it was called (arguments, count) | Verifying side effects (e.g., logger called) |
| **Mock** | Pre-programmed with expectations which form a specification | Strict protocol verification |
| **Fake** | Working implementation with a shortcut (e.g., in-memory repository) | Fast local integration tests |

> [!WARNING]
> Never mock the database in integration tests using in-memory SQLite when the production database is PostgreSQL. Differences in JSONB operators, concurrency locking, and dialect syntax create silent production bugs. Always use real PostgreSQL instances via **Testcontainers**.

---

## 4. Production Integration Test with Testcontainers (Node / TypeScript)

```typescript
import { test, beforeAll, afterAll, expect } from "vitest";
import { PostgreSqlContainer, StartedPostgreSqlContainer } from "@testcontainers/postgresql";
import { Pool } from "pg";

let container: StartedPostgreSqlContainer;
let pool: Pool;

beforeAll(async () => {
  // Spins up an ephemeral, real Docker container on-the-fly
  container = await new PostgreSqlContainer("postgres:16-alpine").start();

  pool = new Pool({
    connectionString: container.getConnectionUri(),
  });

  // Apply real migrations
  await pool.query(`
    CREATE TABLE accounts (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      balance NUMERIC(10, 2) NOT NULL CHECK (balance >= 0)
    );
  `);
}, 30000);

afterAll(async () => {
  await pool?.end();
  await container?.stop();
});

test("enforces atomic balance transfer without race conditions", async () => {
  const { rows } = await pool.query(
    "INSERT INTO accounts (balance) VALUES (100.00) RETURNING id"
  );
  const accountId = rows[0].id;

  // Attempt to deduct balance concurrently
  const deduct = async (amount: number) => {
    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      const res = await client.query(
        "SELECT balance FROM accounts WHERE id = $1 FOR UPDATE",
        [accountId]
      );
      const current = parseFloat(res.rows[0].balance);
      if (current >= amount) {
        await client.query(
          "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
          [amount, accountId]
        );
        await client.query("COMMIT");
        return true;
      }
      await client.query("ROLLBACK");
      return false;
    } finally {
      client.release();
    }
  };

  const [res1, res2] = await Promise.all([deduct(70.00), deduct(70.00)]);

  // Exactly one must succeed, one must fail due to insufficient balance
  expect(res1 !== res2).toBe(true);

  const finalRes = await pool.query("SELECT balance FROM accounts WHERE id = $1", [accountId]);
  expect(parseFloat(finalRes.rows[0].balance)).toBe(30.00);
});
```

---

## 5. Mutation Testing: Quality Beyond Line Coverage

High line coverage ($> 90\%$) often masks poor assertions where assertions are missing entirely. Employ **Stryker Mutator** (TypeScript) or **Mutmut** (Python) to inject intentional bugs ("mutants") into your code:
- If tests fail, the mutant is **killed** (good test suite).
- If tests pass despite the injected bug, the mutant **survived** (defective test suite).

---


---

## 5. Security & Performance Considerations

| Dimension | Focus | Standard Protocol |
| :--- | :--- | :--- |
| **Test Secret Hygiene** | Credential Exposure | Never hardcode production API credentials in fixtures; use mocked keys |
| **Parallel Execution** | Pipeline Speed | Shard test suites across CI worker containers using Vitest/Playwright sharding |
| **Deterministic Isolation** | Flakiness | Ensure each test run utilizes isolated database schemas or transactions that roll back |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Testing Implementation Details** | Asserting private class methods or state | Brittle tests that break on refactoring even when behavior is unchanged | Test public interface contracts and observable behavior |
| **In-Memory SQLite for Postgres** | Using SQLite in tests while running Postgres in prod | Misses dialect-specific query bugs, JSONB errors, and locking anomalies | Use real PostgreSQL containers via Testcontainers |
| **Excessive Mocking** | Mocking every collaborator in integration tests | Tests pass with 100% coverage, yet real system fails on deployment | Mock only external third-party network boundaries (e.g. Stripe, Twilio) |

## 6. Verification Checklist & Production Audit

- [ ] Unit test suite executes locally in $< 10$ seconds.
- [ ] Database integration tests run against real PostgreSQL containers via Testcontainers.
- [ ] Mocks are strictly forbidden for database and external queue boundaries in integration tests.
- [ ] E2E tests in Playwright are restricted to critical path smoke tests ($\le 20$ scenarios).
- [ ] CI pipeline fails if overall mutation score drops below 75%.
