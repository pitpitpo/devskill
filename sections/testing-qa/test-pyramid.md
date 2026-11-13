# 🧪 The Production Test Pyramid & QA Strategy (`test-pyramid.md`)

> **Classification**: Software Quality Assurance & Verification Standard  
> **Target**: QA Engineers, Developers, Autonomous Agent Verifiers  
> **Core Philosophy**: "Test Behaviors, Not Implementations; Fast Feedback Loops; Zero Flakes."

---

## 1. The Production Test Distribution

```
                   /\
                  /  \        10% END-TO-END (Playwright)
                 / E2E\       - Critical business paths (Checkout, Signup)
                /------\      - Real browser execution in CI
               /        \
              / INTEGRAT.\    20% INTEGRATION (Testcontainers)
             /   TESTS    \   - Real DB (PostgreSQL) + Real Cache (Redis)
            /--------------\  - API endpoint contracts & migrations
           /                \
          /   UNIT  TESTS    \ 70% UNIT TESTS (Vitest, pytest, Go test)
         /                    \ - Pure domain logic, validators, calculations
        /----------------------\- Execution time < 5 seconds for entire suite
```

---

## 2. Integration Testing with Ephemeral Containers (Testcontainers)

Never test database queries against SQLite when your production database is PostgreSQL. Use Testcontainers:

```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture
async def db_session(postgres):
    engine = create_async_engine(postgres.get_connection_url().replace("psycopg2", "asyncpg"))
    # Run migrations, yield session, rollback after test
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
```

---

## 3. Playwright E2E Best Practices (Page Object Model)

```typescript
// tests/e2e/pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email Address');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign In' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, pass: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.submitButton.click();
  }
}
```

---

## 4. Flakiness Prevention Rules

1. **Zero Hardcoded Sleeps**: Never write `await sleep(3000)`. Always await deterministic events (`expect(element).toBeVisible()`).
2. **Hermetic Test Isolation**: Every test must set up its own state and clean up after execution. Tests must be order-independent.
3. **Mock Third-Party Networks**: Use Mock Service Worker (MSW) or WireMock for third-party billing/email APIs.
