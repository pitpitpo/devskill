# ⚖️ Technology Selection & Architectural Decision Matrix (`decisions.md`)

> **Objective**: Eliminate arbitrary, hype-driven development. Provide deterministic, trade-off-driven decision trees for choosing frameworks, storage engines, API paradigms, and deployment strategies.

---

## 1. Architectural Pattern Decision Tree

```
Does the team have < 15 engineers?
 ├── YES ──► MODULAR MONOLITH (Single deployable, clean domain boundaries, in-process calls)
 └── NO  ──► Are there divergent scaling characteristics, independent team deploy cadences, 
             or distinct security boundaries?
              ├── NO  ──► MODULAR MONOLITH (Fast refactoring, zero network latency between modules)
              └── YES ──► DISTRIBUTED MICROSERVICES (gRPC internal transport, event-driven async messaging)
```

### Trade-Off Comparison

| Metric | Monolith / Modular Monolith | Microservices | Serverless / Event-Driven |
|---|---|---|---|
| **Operational Complexity** | Low (Single CI/CD, 1 DB, simple tracing) | High (K8s, service mesh, distributed tracing) | Medium (Vendor lock-in, cold starts) |
| **Development Velocity (Early)** | Extremely Fast | Slow (network contracts, deployment overhead) | Fast for event ingestion, slow for complex apps |
| **Data Consistency** | ACID Transactions across entities | Eventual Consistency (Sagas, Outbox pattern) | Eventual Consistency |
| **Team Autonomy** | Moderate (Coordinated deployments) | High (Independent deploy per service) | High per function |
| **Recommended Choice** | **Default choice for 95% of products** | Only when team > 20 and domains clearly split | Webhooks, image processing, bursty crons |

---

## 2. Database Selection Matrix

```
What is your primary data model & access pattern?
 ├── Relational, ACID, Structured, Financial, Relational Joins ──► POSTGRESQL 18 (The Universal Default: AIO, native uuidv7())
 ├── In-memory, sub-millisecond, session cache, rate-limiting   ──► VALKEY / REDIS 8
 ├── Unstructured polymorphic documents, dynamic schema        ──► MONGODB
 ├── Massive scale (>100k writes/sec), key-value lookups       ──► DYNAMODB / SCYLLADB
 ├── AI Vector Embeddings, Semantic Search, RAG                ──► PGVECTOR (if using Postgres) or QDRANT
 └── High-frequency Time-series, IoT, Metrics                  ──► TIMESCALEDB / CLICKHOUSE
```

### Deep Dive: PostgreSQL vs Document Stores

| Factor | PostgreSQL (Recommended Default) | MongoDB / Document DB |
|---|---|---|
| **Schema Evolution** | Strict migrations, JSONB support for flexibility | Schemaless (can lead to data drift/corruption) |
| **Integrity & Joins** | Foreign keys, constraints, composite indexes | Denormalized, manual embedding, application-level joins |
| **Ecosystem & Tooling** | Unmatched (Alembic, Prisma, Drizzle, PgBouncer, pgvector) | Mongoose, Prisma |
| **When to Choose** | E-commerce, SaaS, Fintech, Multi-tenant apps | CMS, rapid polymorphic prototyping, gaming inventories |

---

## 3. API Paradigm Decision Matrix

```
Who is the consumer and what are the bandwidth/latency requirements?
 ├── Public consumers, web/mobile apps, third-party developers  ──► RESTful API (OpenAPI / JSON)
 ├── Complex frontend with nested, client-defined data graphs   ──► GRAPHQL (Apollo / Yoga)
 ├── High-throughput microservice-to-microservice internal RPC  ──► gRPC (Protobuf, HTTP/2)
 ├── Fullstack TypeScript monorepo with end-to-end type safety  ──► tRPC
 └── Real-time bidirectional low-latency push (chat, live feed) ──► WEBSOCKETS / SSE
```

### Comparison Matrix

| Protocol | Transport | Latency | Type Safety | Tooling & Ecosystem |
|---|---|---|---|---|
| **REST (JSON)** | HTTP/1.1 or HTTP/2 | Normal | Via OpenAPI/Swagger | Universal browser & SDK support |
| **tRPC** | HTTP/JSON | Low | Native TypeScript compile-time | Unbeatable DX in fullstack TS monorepos |
| **gRPC** | HTTP/2 (Binary) | Ultra-low | Protobuf compiler | Ideal for high-scale backend services |
| **GraphQL** | HTTP/POST | Normal | Strict Schema | Best for complex multi-platform clients |
| **SSE / WebSocket**| Persistent TCP | Sub-10ms | Protocol-dependent | Live updates, notifications, streaming |

---

## 4. Frontend & Fullstack Framework Selector

```
What are the SEO, performance, and application requirements?
 ├── Public-facing SaaS, E-commerce, marketing, high SEO demands ──► NEXT.JS (App Router, RSC) / NUXT
 ├── Private enterprise dashboard, heavy internal tool (Behind Login) ──► REACT + VITE (SPA) / VUE
 ├── Ultra-lightweight, high interactivity, minimal JS bundle   ──► SVELTEKIT
 └── Cross-platform Mobile (iOS + Android)                      ──► REACT NATIVE (Expo) or FLUTTER
```

### Trade-Offs: SSR vs SPA

| Criteria | Server-Side Rendering (Next.js / Nuxt) | Single Page Application (Vite + React) |
|---|---|---|
| **Initial Page Load (LCP)** | Fast (HTML pre-rendered on server/edge) | Slower (Large JS bundle download required) |
| **SEO Indexability** | 100% native crawler friendly | Requires search engines to execute JavaScript |
| **Hosting Simplicity** | Requires Node.js server or Edge runtime | Static files (S3, Cloudflare Pages, Netlify) |
| **Security Footprint** | API keys can stay server-side in RSC | All client-side code visible in browser |

---

## 5. Backend Framework Decision Engine

```
What is the primary constraint?
 ├── High Developer Velocity, Rich AI/ML Ecosystem, Data Pipelines ──► FASTAPI (Python 3.13/3.14, uv, Pydantic v2)
 ├── Enterprise Node.js, Modular DI, Hexagonal Architecture      ──► NESTJS (TypeScript 6/7, Node 24 LTS)
 ├── Robust Battery-Included, Admin Panel, Rapid CRUD SaaS       ──► DJANGO 5.2+ + DRF / NINJA
 ├── Maximum Concurrency, Ultra-Low Latency, Low Memory Footprint ──► GO 1.25+ (GIN/CHI) or RUST 2024 (AXUM)
 └── Enterprise Corporate Systems, Strong Typings, Massive Scale  ──► SPRING BOOT 3.4+ (Java 21+ Virtual Threads)
```

---

## 6. Frontend State Management Selector

```
What type of state are you handling?
 ├── Server-originated data (cached API responses, pagination) ──► TANSTACK QUERY (React Query)
 ├── Global client-only UI state (modals, theme, sidebars)    ──► ZUSTAND (Lightweight, hook-based)
 ├── Atomic fine-grained reactive state                       ──► JOTAI / SIGNALS
 └── Legacy or massively complex event-driven enterprise state ──► REDUX TOOLKIT (RTK)
```

> **The Golden Rule**: 90% of state is **Server State**. Do not put API data into global Redux/Zustand stores; use TanStack Query with automatic cache invalidation and background revalidation.

---

## 7. Asynchronous Queues & Message Brokers

| Requirement | Recommended Solution | Rationale |
|---|---|---|
| **Simple background task (emails, thumbnails)** | **Redis + BullMQ (Node) / Celery (Python)** | Minimal infrastructure overhead, low latency |
| **Complex routing, AMQP standards, DLQs** | **RabbitMQ** | Reliable routing exchanges, persistent queues |
| **Event streaming, high throughput (>50k/sec), replay** | **Apache Kafka** | Distributed partition log, immutable event store |
| **Cloud-native serverless queuing** | **AWS SQS + SNS / Google Cloud Pub/Sub** | Zero maintenance, infinite horizontal auto-scaling |

---

## 8. Agentic AI Interoperability Protocol Selector (2026)

```
What boundary is your AI agent crossing?
 ├── Agent invoking external tools, APIs, or structured data sources ──► MCP (Stateless Streamable HTTP + OAuth 2.1 RFC 8707)
 ├── Agent delegating async multi-step tasks to opaque peer agents   ──► A2A (Agent Cards at /.well-known/agent-card.json)
 ├── Packaging portable procedural expertise & repo rules for agents ──► Agent Skills (SKILL.md) + AGENTS.md (AAIF standard)
 └── Single in-process model call with deterministic JSON extraction ──► Native Structured Outputs / Direct Function Calling
```

| Protocol | Best Fit | Security Baseline | Avoid When |
|---|---|---|---|
| **MCP (Streamable HTTP)** | Exposing typed tools/resources to multiple AI hosts/IDEs | OAuth 2.1 + RFC 8707 Resource Indicators, Zod/Pydantic schemas | Simple single-app private helper function |
| **A2A (Agent2Agent)** | Cross-team or cross-vendor async agent delegation | TLS 1.3 + mTLS/OAuth 2.1, hop limits, W3C `traceparent` | Tight synchronous sub-10ms RPC loops |
| **Agent Skills (`SKILL.md`)** | Reusable workflows, playbooks, and verifiable scripts | Progressive disclosure, AST10 script audit | Runtime secrets or dynamic user state |

