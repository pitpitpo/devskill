# 🔌 Enterprise Database Connection Pooling Architecture & Sizing

> **Standard Identifier**: `SEC-DATABASE-POOLING-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Database Administrators, Backend Architects, Infrastructure Engineers  
> **Classification**: Level 4 Core Systems Knowledge Base  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *In PostgreSQL, a connection is an expensive, dedicated OS process consuming 5–10MB of RAM and heavy context-switching overhead. Oversizing connections degrades performance; undersizing induces connection starvation. Effective pooling with PgBouncer or HikariCP is mandatory for high-throughput production workloads.*

Many development teams mistakenly assume that handling 1,000 concurrent web requests requires 1,000 database connections. In reality, a database disk subsystem can only execute queries as fast as its underlying CPU cores and I/O spindles allow. Attempting to run hundreds of concurrent PostgreSQL backend processes results in CPU cache trashing, lock contention, and cascading connection timeouts.

This guide codifies connection pool sizing mathematics, PgBouncer architectures, application-level pool tuning (HikariCP / asyncpg), and deadlock diagnostics.

---

## 2. Connection Pool Architectures & Sizing Mathematics

```
   ┌─────────────────────────────────────────────────────────┐
   │            50x API / Worker Pods (Node/Go/Python)       │
   │            (Up to 2,000 concurrent client threads)      │
   └────────────────────────────┬────────────────────────────┘
                                │ Client Connections
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │          PgBouncer Layer (Transaction Pooling Mode)     │
   │          Accepts 2,000 clients -> Multiplexes to 50     │
   └────────────────────────────┬────────────────────────────┘
                                │ Server Connections (50 max)
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │           PostgreSQL Primary Instance (16 vCPU)         │
   │           max_connections = 60                          │
   └─────────────────────────────────────────────────────────┘
```

### The Sizing Formula
Originated by the PostgreSQL core team and validated by benchmarks, the theoretical maximum optimal connection pool size is calculated as:

$$\text{Optimal Connections} = ((\text{Core Count} \times 2) + \text{Effective Spindle Count})$$

*Example*: For a 16-vCPU database instance attached to fast NVMe SSD storage (effective spindle count $\approx 1$):
$$\text{Pool Size} = ((16 \times 2) + 1) = 33 \text{ connections}$$

Configuring hundreds or thousands of direct connections wastes memory ($33 \text{ conns} \times 10\text{MB} = 330\text{MB}$ vs $1000 \text{ conns} \times 10\text{MB} = 10\text{GB}$) and induces catastrophic latency spikes under load.

---

## 3. Pooling Modes: Session vs Transaction vs Statement

| Pooling Mode | Connection Bound | Prepared Statements Supported | Temp Tables Supported | SET Commands Supported | Best Suited For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Session Pooling** | Entire client session lifetime | Yes | Yes | Yes | Long-running legacy apps, administrative consoles |
| **Transaction Pooling** | Duration of single transaction (`BEGIN` ... `COMMIT`) | Requires named query planning or protocol support | No (session scope lost) | Requires `DISCARD ALL` or reset queries | High-throughput web APIs, microservices (Recommended) |
| **Statement Pooling** | Single SQL statement | No | No | No | Read-only reporting, strictly forbidden for multi-statement transactions |

> [!CAUTION]
> In **Transaction Pooling Mode** (PgBouncer default for microservices), session-level features like `LISTEN/NOTIFY`, `PREPARE` statements, and temporary tables cannot be shared across multiple transactions. Use PgBouncer 1.21+ with prepared statement protocol support, or application-level client emulation.

---

## 4. Production Configurations

### 4.1 Production `pgbouncer.ini`
```ini
[databases]
* = host=127.0.0.1 port=5432 auth_user=pgbouncer

[pgbouncer]
logfile = /var/log/postgresql/pgbouncer.log
pidfile = /var/run/postgresql/pgbouncer.pid
listen_addr = *
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Connection Limits
max_client_conn = 5000       ; Max incoming client connections from app pods
default_pool_size = 40       ; Max server connections to Postgres per DB/user
min_pool_size = 10           ; Minimum warm connections maintained
reserve_pool_size = 5        ; Emergency buffer when pool is exhausted
reserve_pool_timeout = 5.0   ; Wait 5s before drawing from reserve pool
max_db_connections = 60      ; Hard ceiling on PostgreSQL server connections

# Pooling Mode
pool_mode = transaction

# Timeouts & Health Checks
server_idle_timeout = 600.0
server_connect_timeout = 15.0
server_login_retry = 1.0
query_timeout = 30.0         ; Abort queries taking longer than 30s
idle_transaction_timeout = 60.0 ; Kill abandoned uncommitted transactions
client_idle_timeout = 0
client_login_timeout = 60.0
```

### 4.2 Application Client Configuration (Node.js / TypeScript `pg` + `pg-pool`)
```typescript
import { Pool, PoolConfig } from "pg";

const poolConfig: PoolConfig = {
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "6432", 10), // Point to PgBouncer port
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  
  // Application pool configuration when connecting through PgBouncer
  max: 20,                       // Max connections per container pod
  min: 2,                        // Min idle connections
  idleTimeoutMillis: 30000,      // Close connection after 30s idle
  connectionTimeoutMillis: 5000, // Error out if connection cannot be acquired in 5s
  maxUses: 7500,                 // Cycle connection periodically to mitigate memory leaks
};

export const dbPool = new Pool(poolConfig);

dbPool.on("error", (err, client) => {
  console.error("[Database Pool Error] Unexpected error on idle client:", err);
});
```

---

## 5. Security & Operational Diagnostics

### 5.1 Monitoring Connection Saturation & Leaks
Execute diagnostic queries to detect leaked connections holding locks:

```sql
-- Find active vs idle connections in transaction
SELECT 
    pid, 
    usename, 
    client_addr, 
    state, 
    now() - state_change AS duration, 
    query 
FROM pg_stat_activity 
WHERE state = 'idle in transaction'
ORDER BY duration DESC;

-- Terminate rogue connection blocking transactions > 5 minutes
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle in transaction' 
  AND now() - state_change > interval '5 minutes';
```

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Max Connections Set to 2000 in postgresql.conf** | Attempting to solve connection errors by raising server limits | Linux kernel OOM kills Postgres; query performance drops 90% | Set `max_connections = 100` on Postgres; place PgBouncer in front |
| **Unclosed Leaked Connections** | Missing `try ... finally { client.release() }` | Pool starvation; app stops accepting requests within hours | Always use automated pool checkout helpers or ORM transaction scopes |
| **Session State in Transaction Mode** | Using `SET search_path` or temp tables inside PgBouncer transaction mode | State leaks into subsequent queries run by completely different users | Use explicit table qualification (`schema.table`) or session pool |
| **Overly Long Connection Timeouts** | Setting connection timeout to 60s | Web requests hang for 60s, exhausting upstream reverse proxy (Nginx) workers | Fail fast: 3–5 second connection timeout |

---

## 7. Verification Checklist & Production Audit

- [ ] PostgreSQL `max_connections` is tuned to the CPU formula and does not exceed 100–200 on primary instances.
- [ ] PgBouncer is deployed between stateless app tiers and PostgreSQL in `transaction` pooling mode.
- [ ] `idle_transaction_timeout` is configured to prevent abandoned transactions from holding table locks.
- [ ] Application client pool specifies both `connectionTimeoutMillis` (< 5000ms) and `maxUses`.
- [ ] Metric alarms monitor `pg_stat_database.numbackends` alerting when connections exceed 80% capacity.
- [ ] Unclosed connection leaks are caught via integration test assertions verifying pool cleanups.
