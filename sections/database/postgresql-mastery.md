# 🐘 PostgreSQL Production Mastery (`postgresql-mastery.md`)

> **Classification**: Production Relational Database Standard  
> **Target**: Database Architects, Backend Developers, SREs  
> **Core Philosophy**: "Index for Your Queries, Master EXPLAIN Plans, Protect the Connection Pool."

---

## 1. Query Execution Analysis (`EXPLAIN ANALYZE`)

Never optimize blind. Always run:
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT id, title, created_at 
FROM articles 
WHERE status = 'published' 
ORDER BY created_at DESC 
LIMIT 20;
```

### Red Flags in Query Plans:
- ❌ **Seq Scan (Sequential Scan)** on large tables (> 10,000 rows): Indicates missing or unused index.
- ❌ **High Buffer Shared Read**: High disk I/O; query should hit memory (`Buffers: shared hit`).
- ❌ **Sort Method: external merge Disk**: Sort spilled to disk. Increase `work_mem` or add an index that supports the sort order.

---

## 2. Strategic Indexing Guide

| Index Type | Best Used For | Example Use Case |
|---|---|---|
| **B-Tree (Default)** | Equality (`=`), Range (`<, <=, >, >=`), Sorting (`ORDER BY`) | Primary keys, foreign keys, timestamps |
| **Partial Index** | Highly skewed status columns | `CREATE INDEX idx_pending_orders ON orders (created_at) WHERE status = 'PENDING';` |
| **GIN (Generalized Inverted)**| Array containment, JSONB searches, Full-Text search | `CREATE INDEX idx_meta ON users USING gin (metadata jsonb_path_ops);` |
| **BRIN (Block Range)** | Massive append-only chronological tables (Logs, metrics) | Very small footprint on multi-million row time-series tables |

---

## 3. Connection Pooling (PgBouncer)

PostgreSQL spawns a separate OS process per connection (~5-10MB RAM per connection). Direct connection counts > 300 will degrade CPU cache performance.

### Configuration Rules:
- Deploy **PgBouncer** in front of PostgreSQL.
- Use **Transaction Pooling mode** (`pool_mode = transaction`) for web applications.
- Formula for Max Pool Connections:
  $$\text{Connections} = ((\text{CPU Cores} \times 2) + \text{Disk Spindles})$$
  *(For a typical 8-core server, optimal active pool size is 20–30 connections).*

---

## 4. Concurrency & Row-Level Locking

Prevent race conditions (e.g., inventory double-booking or wallet balance overdraw) with explicit row locks:

```sql
BEGIN;

-- Lock only the specific user's row until transaction completes
SELECT balance 
FROM accounts 
WHERE id = 'acc_123' 
FOR UPDATE;

-- Update balance safely without race conditions
UPDATE accounts 
SET balance = balance - 50 
WHERE id = 'acc_123';

COMMIT;
```
