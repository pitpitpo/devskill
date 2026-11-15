# 🧬 Polyglot Persistence: Redis, Vector Databases & NoSQL Mastery

> **Standard Identifier**: `SEC-DATABASE-POLYGLOT-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Data Engineers, AI Engineers, Backend Architects  
> **Classification**: Level 4 Core Systems Knowledge Base  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *No single database engine excels at relational transactions, sub-millisecond key-value caching, unstructured document hierarchies, and high-dimensional vector similarity simultaneously. Employ polyglot persistence based on explicit access patterns, indexing mechanisms, and consistency requirements.*

Modern cloud architectures demand specialized storage tiers:
1. **Relational (PostgreSQL)**: ACID transactions, relational integrity, complex multi-table joins.
2. **In-Memory (Redis)**: Volatile caching, real-time counters, distributed locks, rate limiting.
3. **Vector (Pgvector / Qdrant / Pinecone)**: High-dimensional semantic search, embeddings, RAG pipelines.
4. **Document / Key-Value (MongoDB / DynamoDB)**: Flexible schema catalogs, single-table design for predictable ultra-high write throughput.

---

## 2. Technology Selection & Trade-Off Matrix

```
                               ┌────────────────────────────────────────────────────────┐
                               │               DATA ACCESS PATTERN SELECTOR             │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
          ┌───────────────────────┬───────────────────────┼───────────────────────┬───────────────────────┐
          ▼                       ▼                       ▼                       ▼                       ▼
    ACID Relational       Sub-millisecond State        Semantic Search         High-Volume Catalog     Time-Series
     Transactions         & Distributed Primitives      & AI Embeddings        & Key-Value Lookups       Telemetry
          │                       │                       │                       │                       │
      PostgreSQL                Redis                  Pgvector                DynamoDB /              TimescaleDB
    (B-Tree, GIN)         (Hashes, Streams)          (HNSW / IVFFlat)          MongoDB Document         (Hypertables)
```

| Engine | Primary Index Structure | Write Latency | Read Latency | Consistency Model | Scaling Dimension |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | B-Tree, GiST, GIN, BRIN | 2 - 10 ms | 1 - 5 ms | Strict ACID / Serializability | Vertical scale-up, read replicas |
| **Redis** | In-memory Hash Table, SkipList | < 1 ms | < 1 ms | Master-Replica Asynchronous | In-memory sharding, cluster slots |
| **Pgvector** | HNSW (Hierarchical Navigable Small World) | 5 - 20 ms | 2 - 15 ms | Strict ACID | Co-located with relational tables |
| **DynamoDB** | B-Tree / Distributed Partition Hash | 5 - 10 ms | 2 - 5 ms | Eventual or Strong (per read) | Horizontal automated partition split |
| **MongoDB** | WiredTiger B-Tree | 2 - 8 ms | 2 - 5 ms | Configurable Write Concerns (`w: majority`) | Sharded cluster |

---

## 3. High-Dimensional Vector Search: Pgvector Deep Dive

### 3.1 Index Types: HNSW vs IVFFlat
When storing embeddings (e.g. OpenAI `text-embedding-3-small` at 1536 dimensions):

- **IVFFlat (Inverted File Flat)**:
  - Partitions vectors into clusters (lists). Searches only vectors within nearest clusters.
  - *Pros*: Fast build time, small memory footprint.
  - *Cons*: Lower recall (90–95%), requires retraining when distribution drifts.
- **HNSW (Hierarchical Navigable Small World)**:
  - Builds a multi-layer graph of vectors. Searches from top sparse layer down to dense layer.
  - *Pros*: Outstanding recall (> 99%), extremely fast queries under high load.
  - *Cons*: Slower index build time, higher RAM usage.

### 3.2 Production Pgvector Schema & Query
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table definition with 1536-dimensional vector column
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW Cosine Distance Index
-- m: max number of connections per layer (16-64)
-- ef_construction: size of dynamic candidate list during construction (64-256)
CREATE INDEX idx_doc_embeddings_hnsw 
ON document_embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 128);

-- Metadata Filter Index
CREATE INDEX idx_doc_embeddings_metadata ON document_embeddings USING gin (metadata);

-- Hybrid Query: Semantic Cosine Distance combined with Metadata Filtering
SELECT 
    id, 
    chunk_text, 
    1 - (embedding <=> '[0.012, -0.043, 0.054]'::vector) AS similarity_score
FROM document_embeddings
WHERE metadata @> '{"tenant_id": "tenant_123", "public": true}'
ORDER BY embedding <=> '[0.012, -0.043, 0.054]'::vector
LIMIT 5;
```

---

## 4. Advanced Redis Data Structures

Beyond simple key-value strings, production Redis patterns leverage specialized primitives:

### 4.1 Redis Streams for Event Sourcing
```bash
# Append event to stream
XADD orders:events * event_type "OrderPlaced" order_id "ord_101" amount "199.99"

# Create Consumer Group
XGROUP CREATE orders:events inventory_workers $ MKSTREAM

# Worker Read
XREADGROUP GROUP inventory_workers worker_1 COUNT 10 BLOCK 2000 STREAMS orders:events >

# Acknowledge processed event
XACK orders:events inventory_workers 1718000000000-0
```

### 4.2 HyperLogLog for Unique Cardinality
Counting unique visitors without storing millions of UUIDs:
```bash
# Add elements (Memory usage capped at 12KB regardless of entries)
PFADD daily_visitors:2026-11-15 "user_101" "user_102" "user_103"

# Retrieve approximate cardinality (0.81% standard error)
PFCOUNT daily_visitors:2026-11-15
```

---

## 5. Security & Consistency Considerations

1. **Dual-Write Consistency**: Writing to Postgres and Redis/Vector in separate uncoordinated operations invites consistency drift. Use the **Transactional Outbox Pattern** to reliably sync changes.
2. **Vector Dimension Mismatch**: Enforce strict dimension constraints (`vector(1536)`) at the database schema level.
3. **NoSQL Injection**: Always sanitize and parameterize document queries (MongoDB `$where` or `$regex` clauses must never interpolate raw user strings).

---


---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Blocking Commands on Redis** | Running `KEYS *` or `FLUSHALL` in production | Freezes single-threaded Redis event loop; cascades timeouts | Use `SCAN` with bounded `COUNT` parameters |
| **Unindexed Vector Columns** | Executing semantic search without HNSW/IVFFlat | High query latency (> 500ms) on datasets > 50,000 vectors | Create an HNSW index with calibrated `m` and `ef_construction` |
| **Dual-Write Drift** | Writing to Postgres and Vector DB without outbox | Eventual inconsistency between relational truth and vector index | Use the Transactional Outbox pattern or CDC pipeline |

## 6. Verification Checklist & Production Audit

- [ ] Pgvector tables use HNSW indexes for high recall in latency-sensitive search paths.
- [ ] Embeddings dimensionality matches the model architecture exactly.
- [ ] Redis memory usage is monitored with alerting on eviction rate spikes.
- [ ] Outbox pattern or Change Data Capture (Debezium) is employed when syncing data between relational and vector/search stores.
- [ ] DynamoDB/NoSQL tables have explicitly defined partition keys avoiding hot partitions.
