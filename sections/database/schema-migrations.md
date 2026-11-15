# 🔄 Zero-Downtime Schema Migrations Guide (`schema-migrations.md`)

> **Classification**: Production Database Migration Standard  
> **Target**: Backend Engineers, DBAs, Platform Engineers, SREs  
> **Core Philosophy**: "Every migration MUST be backward-compatible with the currently running application version — deploy code first, migrate schema second, contract later."

---

## Table of Contents

1. [The Expand/Contract Pattern](#1-the-expandcontract-pattern)
2. [Schema Migrations vs Data Migrations](#2-schema-migrations-vs-data-migrations)
3. [Safe Column Operations](#3-safe-column-operations)
4. [Locking Considerations (PostgreSQL)](#4-locking-considerations-postgresql)
5. [Online Schema Change Tools](#5-online-schema-change-tools)
6. [Migration Tooling by Ecosystem](#6-migration-tooling-by-ecosystem)
7. [Migration Ordering & Dependencies](#7-migration-ordering--dependencies)
8. [Rollback Strategies](#8-rollback-strategies)
9. [Testing Migrations in CI](#9-testing-migrations-in-ci)
10. [Security & Performance Considerations](#10-security--performance-considerations)
11. [Common Pitfalls & Anti-Patterns](#11-common-pitfalls--anti-patterns)
12. [Verification Checklist](#12-verification-checklist)

---

## 1. The Expand/Contract Pattern

The Expand/Contract pattern (also called Parallel Change) is the **foundational strategy** for zero-downtime schema changes. It ensures that old and new application versions coexist with the database schema at every point during deployment.

```mermaid
flowchart LR
    A["Phase 1: Expand\n(Add new column/table)"] --> B["Phase 2: Migrate\n(Dual-write + backfill)"]
    B --> C["Phase 3: Contract\n(Drop old column/table)"]
    
    A -- "Old app still works" --> A
    B -- "Both versions work" --> B
    C -- "Only new app runs" --> C
```

### Phase 1 — Expand

Add the new column, table, or index **without removing anything**. The new column MUST be nullable or have a server-side default that does not require a table rewrite.

```sql
-- ✅ GOOD: Nullable column, no table rewrite in PG 11+
ALTER TABLE users ADD COLUMN display_name TEXT;

-- ❌ BAD: NOT NULL without default forces table rewrite on older PG
ALTER TABLE users ADD COLUMN display_name TEXT NOT NULL;
```

### Phase 2 — Migrate (Dual-Write + Backfill)

Deploy application code that writes to **both** the old and new columns. Then run a background data migration to backfill historical rows:

```python
# Backfill in batches — never unbounded UPDATE
import time
from sqlalchemy import text

BATCH_SIZE = 1000
THROTTLE_MS = 50

def backfill_display_name(engine):
    """Backfill display_name from first_name + last_name in batches."""
    while True:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE users
                SET display_name = first_name || ' ' || last_name
                WHERE id IN (
                    SELECT id FROM users
                    WHERE display_name IS NULL
                    ORDER BY id
                    LIMIT :batch_size
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id
            """), {"batch_size": BATCH_SIZE})
            
            updated = result.rowcount
            if updated == 0:
                break
        
        time.sleep(THROTTLE_MS / 1000.0)
```

### Phase 3 — Contract

After **all** application instances are reading from the new column and the old column is confirmed unused (via query logging or application metrics), drop the old column in a subsequent release:

```sql
-- Only after confirming zero reads from old columns
ALTER TABLE users DROP COLUMN first_name;
ALTER TABLE users DROP COLUMN last_name;
```

> [!IMPORTANT]
> The Contract phase MUST happen in a **separate deployment** from the Expand phase. Never expand and contract in the same release — this defeats zero-downtime guarantees.

---

## 2. Schema Migrations vs Data Migrations

| Aspect | Schema Migration | Data Migration |
|---|---|---|
| **What changes** | DDL: columns, indexes, constraints, tables | DML: row values, backfills, transformations |
| **Execution speed** | Usually instant (metadata-only in modern PG) | Can take hours on large tables |
| **Locking risk** | High if done incorrectly (AccessExclusiveLock) | Low (row-level locks with `FOR UPDATE SKIP LOCKED`) |
| **Rollback** | Reverse DDL (drop column, drop index) | Reverse DML or restore from backup |
| **Should run in migration tool** | Yes | Only for small datasets; use background jobs for large |
| **Idempotency** | MUST be idempotent | MUST be idempotent |

### Golden Rule

Schema migrations SHOULD be **fast and metadata-only**. Data migrations SHOULD run as **background jobs** with progress tracking, batching, and throttling.

```python
# Alembic migration — schema only, fast
def upgrade():
    op.add_column("orders", sa.Column("total_cents", sa.BigInteger(), nullable=True))

def downgrade():
    op.drop_column("orders", "total_cents")
```

```python
# Separate data migration script — NOT in Alembic
# Run as: python scripts/backfill_order_totals.py
def backfill_order_totals():
    """Convert total_dollars (NUMERIC) to total_cents (BIGINT)."""
    # Batched, throttled, idempotent, resumable
    ...
```

---

## 3. Safe Column Operations

### Adding Columns

| Operation | Safe? | Notes |
|---|---|---|
| `ADD COLUMN ... NULL` | ✅ Yes | Metadata-only in PostgreSQL |
| `ADD COLUMN ... DEFAULT val` (PG 11+) | ✅ Yes | Stored in catalog, no rewrite |
| `ADD COLUMN ... DEFAULT val` (PG < 11) | ❌ No | Full table rewrite |
| `ADD COLUMN ... NOT NULL DEFAULT val` (PG 11+) | ✅ Yes | Default stored in catalog |
| `ADD COLUMN ... NOT NULL` (no default) | ❌ No | Fails if existing rows exist |

### Renaming Columns Safely

**Never** rename a column directly. Instead, use Expand/Contract:

```sql
-- Step 1 (Deploy 1): Add new column
ALTER TABLE products ADD COLUMN title TEXT;

-- Step 2 (Application): Dual-write to both `name` and `title`
-- Step 3 (Background): Backfill `title` from `name`

-- Step 4 (Deploy 2): Switch reads to `title`, stop writing `name`

-- Step 5 (Deploy 3): Drop old column
ALTER TABLE products DROP COLUMN name;
```

### Removing Columns Safely

1. **Deploy 1**: Stop reading from the column in application code (remove from SELECT, ORM model)
2. **Deploy 2**: Stop writing to the column
3. **Deploy 3**: Drop the column from the schema

```sql
-- ✅ GOOD: Column is already unused by application
ALTER TABLE users DROP COLUMN legacy_avatar_url;

-- ❌ BAD: Dropping column while old app version still reads it
-- This causes SELECT * queries and ORM hydration to break
```

### Adding Indexes Concurrently

Standard `CREATE INDEX` acquires a `ShareLock` on the table, blocking all writes for the duration of the index build. On large tables this can take minutes or hours.

```sql
-- ✅ GOOD: Non-blocking index creation
CREATE INDEX CONCURRENTLY idx_orders_created_at
ON orders (created_at);

-- ❌ BAD: Blocks all INSERT/UPDATE/DELETE during build
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

> [!WARNING]
> `CREATE INDEX CONCURRENTLY` cannot run inside a transaction. Migration tools like Alembic require special configuration. In Alembic, use `op.execute()` with `autocommit` mode or configure the migration to run outside of a transaction block.

```python
# Alembic: concurrent index creation
from alembic import op

def upgrade():
    # Must disable transaction wrapping for CONCURRENTLY
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
        "idx_orders_status ON orders (status)"
    )

# In env.py or migration header:
# revision.module.__migration_flags__ = {"transaction": False}
```

---

## 4. Locking Considerations (PostgreSQL)

PostgreSQL uses a hierarchy of lock modes. The most dangerous for migrations is `AccessExclusiveLock`, which blocks **all** operations including `SELECT`.

### Lock Mode Hierarchy (Relevant to Migrations)

| Lock Mode | Acquired By | Blocks |
|---|---|---|
| `AccessShareLock` | `SELECT` | Nothing except `AccessExclusiveLock` |
| `RowExclusiveLock` | `INSERT`, `UPDATE`, `DELETE` | `ShareLock` and above |
| `ShareLock` | `CREATE INDEX` (non-concurrent) | `RowExclusiveLock` and above |
| `AccessExclusiveLock` | `ALTER TABLE`, `DROP TABLE`, `TRUNCATE`, `REINDEX` | **Everything** |

### Dangerous DDL Operations

```sql
-- ❌ These acquire AccessExclusiveLock (blocks all queries):
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
ALTER TABLE users ALTER COLUMN age TYPE BIGINT;  -- type change = rewrite
ALTER TABLE users ADD CONSTRAINT uk_email UNIQUE (email);
ALTER TABLE users RENAME COLUMN name TO full_name;
DROP INDEX idx_users_email;  -- brief lock but still AccessExclusive
```

### Safe Alternatives

```sql
-- ✅ Add NOT NULL via constraint (PG 12+, no rewrite):
ALTER TABLE users ADD CONSTRAINT users_email_nn
  CHECK (email IS NOT NULL) NOT VALID;
-- Then validate separately (only ShareUpdateExclusiveLock):
ALTER TABLE users VALIDATE CONSTRAINT users_email_nn;

-- ✅ Create unique index concurrently, then add constraint using it:
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_unique ON users (email);
ALTER TABLE users ADD CONSTRAINT uk_email UNIQUE USING INDEX idx_users_email_unique;
```

### Lock Timeout Configuration

Always set a lock timeout to prevent migrations from queuing behind long-running queries and then blocking all subsequent queries once they acquire the lock:

```sql
-- Set aggressive lock timeout for migrations
SET lock_timeout = '5s';
SET statement_timeout = '30s';

-- If the lock can't be acquired in 5 seconds, the migration
-- fails fast instead of blocking the entire application
ALTER TABLE users ADD COLUMN bio TEXT;
```

---

## 5. Online Schema Change Tools

For MySQL and very large PostgreSQL tables where even metadata-only DDL is risky, use online schema change (OSC) tools.

### gh-ost (GitHub Online Schema Migration for MySQL)

```bash
# Rename column safely using gh-ost
gh-ost \
  --host=replica.db.internal \
  --database=myapp \
  --table=users \
  --alter="CHANGE name full_name VARCHAR(255) NOT NULL" \
  --execute \
  --allow-on-master \
  --chunk-size=1000 \
  --max-lag-millis=1500 \
  --throttle-control-replicas="replica1.db.internal"
```

**How gh-ost works**:
1. Creates a ghost (shadow) table with the desired schema
2. Copies data in chunks from the original table
3. Uses binary log streaming (not triggers) to capture live changes
4. Performs an atomic table rename (`RENAME TABLE`) at cut-over

### pt-online-schema-change (Percona Toolkit)

```bash
pt-online-schema-change \
  --alter "ADD COLUMN phone VARCHAR(20) DEFAULT NULL" \
  --execute \
  --chunk-size=500 \
  --max-lag=1 \
  D=myapp,t=users
```

### pgroll (PostgreSQL)

For PostgreSQL, [pgroll](https://github.com/xataio/pgroll) provides automated expand/contract migrations:

```json
{
  "name": "add_display_name",
  "operations": [
    {
      "add_column": {
        "table": "users",
        "column": {
          "name": "display_name",
          "type": "text",
          "nullable": true
        }
      }
    }
  ]
}
```

---

## 6. Migration Tooling by Ecosystem

### Alembic (Python / SQLAlchemy)

```bash
# Initialize
alembic init alembic

# Generate migration from model changes
alembic revision --autogenerate -m "add users display_name"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

```python
# alembic/versions/20240115_add_display_name.py
"""add users display_name"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4"
down_revision = "e5f6g7h8"

def upgrade():
    op.add_column("users", sa.Column("display_name", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("users", "display_name")
```

### Prisma Migrate (TypeScript / Node.js)

```bash
# Generate migration from schema.prisma changes
npx prisma migrate dev --name add_display_name

# Apply in production (no interactive prompts)
npx prisma migrate deploy

# Check migration status
npx prisma migrate status
```

```prisma
// schema.prisma — add the field
model User {
  id          Int     @id @default(autoincrement())
  email       String  @unique
  displayName String? @map("display_name")  // nullable = safe
}
```

### Drizzle Kit (TypeScript)

```bash
# Generate migration SQL from schema changes
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# Push schema directly (dev only)
npx drizzle-kit push
```

```typescript
// drizzle/schema.ts
import { pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  email: text("email").notNull().unique(),
  displayName: text("display_name"),  // nullable by default
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
```

### Flyway (Java / Spring Boot)

```bash
# Directory structure — lexicographic ordering
src/main/resources/db/migration/
├── V1__create_users_table.sql
├── V2__add_display_name.sql
├── V3__backfill_display_name.sql    # Data migration (small tables only)
└── V4__drop_legacy_name_columns.sql  # Contract phase
```

```sql
-- V2__add_display_name.sql
ALTER TABLE users ADD COLUMN display_name TEXT;
```

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    validate-on-migrate: true
    out-of-order: false  # Enforce strict ordering
```

---

## 7. Migration Ordering & Dependencies

### Rules for Ordering

1. **Monotonically increasing identifiers**: Use timestamps (`20240115120000`) or sequential numbers (`V001`)
2. **One concern per migration**: Never mix DDL for unrelated tables
3. **Forward-only in production**: Out-of-order migrations MUST be rejected in production CI
4. **Branch conflicts**: When two branches add migrations with the same sequence, the second to merge MUST resequence

### Dependency Graph Example

```mermaid
flowchart TD
    M1["V1: Create users table"] --> M2["V2: Create orders table\n(FK → users)"]
    M2 --> M3["V3: Add orders.status column"]
    M1 --> M4["V4: Add users.display_name"]
    M3 --> M5["V5: Create idx_orders_status\n(CONCURRENTLY)"]
    M4 --> M6["V6: Backfill display_name\n(data migration)"]
    M6 --> M7["V7: Drop users.first_name\n(contract)"]
```

### Preventing Merge Conflicts

```bash
# In CI: verify no duplicate migration sequence numbers
DUPLICATES=$(ls db/migrations/ | cut -d'_' -f1 | sort | uniq -d)
if [ -n "$DUPLICATES" ]; then
    echo "❌ Duplicate migration sequence numbers: $DUPLICATES"
    exit 1
fi
```

---

## 8. Rollback Strategies

### Strategy Matrix

| Strategy | Speed | Risk | When to Use |
|---|---|---|---|
| **Reverse migration** (down) | Fast | Medium — may lose data | Schema-only changes |
| **Forward-fix migration** | Fast | Low | Preferred for production |
| **Point-in-time recovery** | Slow | High — data loss window | Catastrophic failures |
| **Application rollback** | Fast | Low | If schema is backward-compatible |

### Forward-Fix Over Rollback

Rolling back a migration that has been running in production with dual-writes is dangerous. Prefer a **forward-fix**:

```python
# ❌ BAD: Rolling back after data has been written to new column
def downgrade():
    op.drop_column("orders", "total_cents")  # Loses all backfilled data!

# ✅ GOOD: Forward-fix — add missing constraint in a new migration
def upgrade():
    op.alter_column("orders", "total_cents",
                    existing_type=sa.BigInteger(),
                    nullable=False,
                    server_default=sa.text("0"))
```

### Rollback Readiness Checklist

- [ ] Every migration file has a working `downgrade()` / `down` function
- [ ] Down migrations are tested in CI against a database with sample data
- [ ] Data migrations store enough metadata to be reversed
- [ ] Destructive operations (DROP COLUMN) are in separate, delayed migrations

---

## 9. Testing Migrations in CI

### CI Pipeline Architecture

```mermaid
flowchart LR
    A["Checkout Code"] --> B["Start Ephemeral PG\n(Docker/Testcontainers)"]
    B --> C["Apply All Migrations\n(upgrade head)"]
    C --> D["Run Schema Validation\n(diff vs models)"]
    D --> E["Run Down Migrations\n(downgrade base)"]
    E --> F["Re-apply All Migrations\n(upgrade head again)"]
    F --> G["Run Application Tests"]
```

### GitHub Actions Example

```yaml
name: Migration Tests
on: [pull_request]

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt

      # Test forward migration
      - name: Apply all migrations
        run: alembic upgrade head
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb

      # Test rollback
      - name: Rollback all migrations
        run: alembic downgrade base
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb

      # Test re-apply (idempotency)
      - name: Re-apply all migrations
        run: alembic upgrade head
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb

      # Verify no model drift
      - name: Check for unapplied model changes
        run: |
          alembic check 2>&1 || {
            echo "❌ Model changes detected without a migration"
            exit 1
          }
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
```

### Migration Lint Rules

```bash
#!/usr/bin/env bash
# Lint migration files for dangerous patterns
set -euo pipefail

MIGRATION_DIR="alembic/versions"
ERRORS=0

for f in "$MIGRATION_DIR"/*.py; do
    # Check for non-concurrent index creation
    if grep -qP "CREATE\s+INDEX\s+(?!CONCURRENTLY)" "$f" 2>/dev/null; then
        echo "❌ $f: CREATE INDEX without CONCURRENTLY"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for ALTER TABLE ... SET NOT NULL without constraint
    if grep -qiP "ALTER\s+.*SET\s+NOT\s+NULL" "$f" 2>/dev/null; then
        echo "❌ $f: SET NOT NULL may acquire AccessExclusiveLock"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for missing downgrade
    if ! grep -q "def downgrade" "$f" 2>/dev/null; then
        echo "❌ $f: Missing downgrade() function"
        ERRORS=$((ERRORS + 1))
    fi
done

exit $ERRORS
```

---

## 10. Security & Performance Considerations

### Security

- **R-067 Compliance**: The database user running migrations SHOULD be a dedicated migration user with `ALTER`, `CREATE`, `DROP` privileges — **not** the application runtime user (which SHOULD have only `SELECT`, `INSERT`, `UPDATE`, `DELETE`).
- **Audit trail**: Log every migration execution with timestamp, user, revision ID, and duration to an immutable audit log.
- **Secrets in migrations**: Data migrations that transform PII MUST NOT log row contents. Use `SET log_statement = 'none'` during PII backfills.

### Performance

- **Lock monitoring**: Before running migrations, check for long-running queries that could block DDL:
  ```sql
  SELECT pid, now() - query_start AS duration, query
  FROM pg_stat_activity
  WHERE state = 'active' AND query_start < now() - interval '1 minute'
  ORDER BY duration DESC;
  ```
- **Replication lag**: Monitor replication lag during data migrations. Throttle if lag exceeds acceptable thresholds (typically 1–5 seconds).
- **Table bloat**: After large backfills, schedule a `VACUUM ANALYZE` to reclaim dead tuples and update statistics.

---

## 11. Common Pitfalls & Anti-Patterns

| # | Anti-Pattern | Why It's Dangerous | Correct Approach |
|---|---|---|---|
| 1 | Running `ALTER TABLE ... SET NOT NULL` directly | Acquires `AccessExclusiveLock`, blocks all queries | Use `CHECK CONSTRAINT NOT VALID` + `VALIDATE CONSTRAINT` |
| 2 | Changing column type (`ALTER COLUMN ... TYPE`) | Full table rewrite + `AccessExclusiveLock` | Add new column, backfill, swap reads, drop old |
| 3 | Unbounded `UPDATE` for backfills | Locks millions of rows, bloats WAL, kills replicas | Batch with `LIMIT` + `FOR UPDATE SKIP LOCKED` |
| 4 | `CREATE INDEX` without `CONCURRENTLY` | `ShareLock` blocks all writes during build | Always use `CONCURRENTLY` in production |
| 5 | Mixing schema + data in one migration | Makes rollback impossible, slow execution | Separate into distinct migration files |
| 6 | Dropping a column before removing app references | Application crashes on missing column | Remove from app first, drop in later release |
| 7 | Adding `NOT NULL` column without default | `ALTER TABLE` fails when rows exist | Use nullable, backfill, then add constraint |
| 8 | Renaming column directly | Breaks running application instances | Use Expand/Contract over 3 deployments |
| 9 | Trusting `--autogenerate` blindly | May generate destructive operations or miss custom indexes | Always review generated SQL before applying |
| 10 | Running migrations during peak traffic | Lock contention amplified under high concurrency | Schedule during low-traffic maintenance windows |

---

## 12. Verification Checklist

Before merging any migration PR, verify:

- [ ] Migration has both `upgrade()` and `downgrade()` functions
- [ ] `downgrade()` is tested against a database with realistic data
- [ ] No `CREATE INDEX` without `CONCURRENTLY` on tables > 10K rows
- [ ] No `ALTER COLUMN ... TYPE` on tables > 100K rows without OSC tooling
- [ ] No `SET NOT NULL` without using `CHECK CONSTRAINT NOT VALID` pattern
- [ ] Data migrations are batched (≤ 1000 rows per transaction)
- [ ] Data migrations include throttling (`sleep` between batches)
- [ ] Data migrations are idempotent (safe to re-run)
- [ ] Lock timeout is set (`SET lock_timeout = '5s'`)
- [ ] No PII is logged during data transformation
- [ ] Migration is backward-compatible with the currently deployed app version
- [ ] Expand and Contract phases are in **separate** migration files
- [ ] CI runs: upgrade → downgrade → upgrade (full roundtrip)
- [ ] Replication lag monitoring is in place for data migrations
- [ ] `VACUUM ANALYZE` is scheduled after large backfills

---

## Cross-References

- [PostgreSQL Production Mastery](./postgresql-mastery.md) — Query analysis, indexing, connection pooling
- [Connection Pooling & Management](./connection-pooling.md) — PgBouncer interaction with migrations
- [NoSQL, Redis & Vector Databases](./nosql-redis-vector.md) — Schema-less migration considerations
- [Deployment Strategies](../../pipelines/deployment-strategies.md) — Coordinating migrations with blue/green deploys
- [RULES.md](../../RULES.md) — R-108 (Expand/Contract), R-109 (Non-Blocking DDL), R-115 (Batched Backfills)
