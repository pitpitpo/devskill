# 🌐 Distributed Systems, Storage Internals & Production Reliability (`distributed-systems-reliability.md`)

> **Standard Identifier**: `SEC-FOUNDATIONS-DISTRIBUTED-001`  
> **Status**: Active / Production Standard  
> **Canonical Sources**: Martin Kleppmann (*Designing Data-Intensive Applications*), Michael Nygard (*Release It!*, 2nd Ed.), Alex Petrov (*Database Internals*), Betsy Beyer et al. (*Site Reliability Engineering*, Google SRE)  
> **Enforced Rules**: [`RULES.md`](../../RULES.md) (`R-046`–`R-059`, `R-103`–`R-116`, `R-193`, `R-241`–`R-243`)

---

## 1. Data Consistency & Distributed Invariants (*Designing Data-Intensive Applications* — Kleppmann)

Distributed systems fail partially, networks delay or reorder packets arbitrarily, and wall-clock time (`Date.now()` / `time.time()`) can jump backward during NTP adjustments.

### 1.1 Mandatory Distributed System Realities
1. **Monotonic Clocks for Durations, Never Wall Clocks**: Measure elapsed time, timeouts, and lease durations strictly using monotonic clocks (`performance.now()`, `time.monotonic()`, `Instant::now()`). Wall clocks are for display timestamps only.
2. **Replication Lag Anomalies & Remedies**:
   - **Read-Your-Own-Writes**: After a user updates their profile or posts an order, route their immediate reads to the primary or pin to a replication LSN/watermark so they never see their own write vanish.
   - **Monotonic Reads**: Pin a user's read session to a consistent replica so time never appears to move backward across refreshes.
   - **Write Skew & Phantoms**: `READ COMMITTED` and even `REPEATABLE READ` (snapshot isolation) do NOT prevent write skew (e.g., two on-call doctors simultaneously taking themselves off call). Guard multi-row invariants with `SELECT ... FOR UPDATE`, `SERIALIZABLE` isolation, or materialized conflict rows with unique constraints.
3. **Fencing Tokens for Distributed Locks (`R-193`)**: A lease/lock (Redis `SET NX EX`, ZooKeeper, etcd) can expire silently during a GC pause or OS scheduling stall, allowing two writers to believe they hold the lock simultaneously. Every lock grant MUST issue a monotonically increasing **fencing token** checked by the storage layer (`WHERE epoch < :token`).
4. **Transactional Outbox & Log-Based CDC (`R-241`)**: Never perform a dual-write across two independent systems (e.g., `INSERT INTO orders` followed by `kafka.publish(orderCreated)`). If the process crashes between the two calls, state diverges permanently. Instead, write the domain row AND an `outbox_events` row inside the **same local ACID transaction**, and relay events asynchronously via polling or Debezium WAL CDC with idempotent consumers.

```
   ❌ DUAL WRITE (Split-Brain Bug)             ✅ TRANSACTIONAL OUTBOX (Atomic)
   ┌───────────────────────────┐               ┌───────────────────────────────┐
   │ 1. DB COMMIT (succeeds)   │               │ BEGIN TRANSACTION             │
   │ 2. Process crashes / OOM  │               │   INSERT INTO orders ...      │
   │ 3. Broker publish LOST!   │               │   INSERT INTO outbox_events   │
   └───────────────────────────┘               │ COMMIT (atomic!)              │
                                               └───────────────┬───────────────┘
                                                               ▼
                                               CDC / Relay Worker ──► Broker (At-least-once)
                                                               ▼
                                               Idempotent Consumer (dedupe by event_id)
```

---

## 2. Production Stability Patterns (*Release It!* 2nd Ed. — Michael Nygard)

Every external network call—database, cache, payment API, DNS resolver, LLM gateway—is an **Integration Point**, the #1 trigger of cascading production outages.

### 2.1 Stability Anti-Patterns vs. Mandatory Stability Patterns (`R-242`)

| Anti-Pattern (Crack Propagation) | Production Failure Mode | Mandatory Stability Pattern |
| :--- | :--- | :--- |
| **Unbounded Waiting** | Slow downstream socket ties up all worker threads/connections until the whole fleet deadlocks | **Explicit Timeouts** (`connect`, `read`, `total` deadline budgets propagated across RPC hops, `R-050`) |
| **Retry Storms** | All clients retry synchronously on a struggling service, multiplying load 10× and preventing recovery | **Exponential Backoff + Full Jitter** (`R-051`) + **Retry Budget** (cap retries at ≤ 10% of total traffic) |
| **Shared Fate Thread/Conn Pools** | Slow analytics endpoint exhausts the DB pool shared with checkout/auth, taking down core revenue | **Bulkheads** (separate connection pools, worker queues, and memory quotas per criticality tier) |
| **Unbounded Result Sets** | `SELECT * FROM events` or unbounded in-memory queues cause instant OOM crashes under traffic spikes | **Bounded Queues, Keyset Pagination (`R-186`) & Load Shedding** (fail fast with HTTP `429`/`503` + `Retry-After`) |
| **Sluggish Recovery After Outage** | Calling a known-dead dependency repeatedly adds full timeout latency to every user request | **Circuit Breakers** (`Closed → Open → Half-Open`, `R-052`) + **Graceful Fallback** (`R-054`) |
| **Unchecked Growth (Logs, Disk, Sessions)** | Disk fills to 100% after 90 days; unindexed audit tables slow every query | **Steady State** (automated log rotation, TTLs on caches/sessions, archival/partitioning, bounded retention) |

### 2.2 Backpressure & Load Shedding
When ingress rate exceeds processing capacity ($\lambda > \mu$), an unbounded queue guarantees unbounded latency followed by OOM. Enforce **bounded queues** at every ingress and worker boundary; when full, shed low-priority load immediately with `503 Service Unavailable` / `429 Too Many Requests` so high-priority requests still complete inside their SLO.

---

## 3. Storage Engine Trade-Offs (*Database Internals* — Alex Petrov)

Choosing the right storage engine and schema design requires understanding the **RUM Conjecture** (Read, Update/Write, and Memory/Space amplification trade-offs):

| Engine Family | Representative Systems | Read Performance | Write Performance | Optimal Workload |
| :--- | :--- | :--- | :--- | :--- |
| **B-Tree (Page-Oriented, In-Place Update + WAL)** | PostgreSQL, MySQL InnoDB, SQLite | Fast point & range lookups; predictable latency | Random I/O on non-sequential keys (mitigated by monotonic `uuidv7()` / `BIGINT` PKs!) | OLTP, transactional ledgers, relational queries with rich secondary indexes |
| **LSM-Tree (Log-Structured Merge-Tree + SSTables)** | RocksDB, Cassandra, ScyllaDB, ClickHouse MergeTree | Needs Bloom filters & multi-level compaction reads | Blazing sequential append-only write throughput | High-ingest telemetry, time-series, write-heavy KV stores, append-only logs |

- **Durability Law**: A write is NOT durable until flushed to the **Write-Ahead Log (WAL)** (`fsync`) before acknowledging commit.
- **Compaction & Vacuum Reality**: B-Trees accumulate dead tuple bloat under heavy updates (requiring aggressive PostgreSQL `autovacuum`); LSM-Trees experience read/I/O spikes during compaction (requiring I/O throttling and headroom).

---

## 4. Reliability Engineering (*Site Reliability Engineering* — Google SRE)

### 4.1 SLIs, SLOs & Error Budgets (`R-243`)
100% reliability is the wrong target for almost every system—it paralyzes velocity without benefiting users. Define quantitative targets for every Tier-1 service:
- **SLI (Service Level Indicator)**: Concrete measured ratio (e.g., *proportion of valid HTTP requests returning non-5xx within 300ms*).
- **SLO (Service Level Objective)**: Target over a rolling window (e.g., *99.9% over 28 days* → **40.3 minutes** of allowed error budget).
- **Error Budget Policy**:
  - **Budget Remaining > 0**: Ship features at full velocity.
  - **Budget Exhausted**: Freeze non-critical feature launches; redirect engineering capacity exclusively to reliability, load testing, and incident root-cause elimination until error budget recovers.
- **Multi-Window Burn-Rate Alerts**: Alert on **fast burn** (e.g., 2% of 30-day budget consumed in 1 hour → page immediately) rather than noisy single-point CPU spikes (`OBSERVABILITY.md`).

### 4.2 Eliminating Toil & Blameless Postmortems
- **Toil Definition**: Manual, repetitive, automatable, reactive operational work that scales linearly with service growth. Cap SRE/team toil at **< 50%**; automate recurring runbooks permanently.
- **Blameless Postmortems**: Assume engineers acted with good intent given the information available. Treat human error as a **symptom of missing guardrails** (missing canary check, missing confirmation gate, ambiguous CLI flag) and fix the system, not the person.

---

## 5. Verification Checklist

- [ ] No dual-writes across DB + message broker without Transactional Outbox / CDC (`R-241`).
- [ ] Every external integration point enforces explicit timeouts, jittered retries with budget, circuit breakers, and isolated bulkheads (`R-242`).
- [ ] Bounded queues and explicit load-shedding (`429`/`503`) protect ingress against overload cascades.
- [ ] Distributed locks issue monotonically increasing fencing tokens checked at the storage boundary (`R-193`).
- [ ] Tier-1 services define measurable SLIs, SLOs, error budgets, and burn-rate alerting (`R-243`).
- [ ] Durations and timeouts use monotonic clocks exclusively (never wall-clock subtraction).
