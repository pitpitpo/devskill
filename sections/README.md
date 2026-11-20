# 🏗️ Cross-Cutting Architectural Sections (`sections/`)

This directory houses cross-cutting engineering domains that span across frameworks and languages.

## Subdirectories

- [`architecture-foundations/`](architecture-foundations/):
  - [`software-design-craft.md`](architecture-foundations/software-design-craft.md): Deep modules (Ousterhout), Tidy First (Beck), Legacy Code & Characterization Tests (Feathers), DDD (Evans/Vernon), Google Engineering laws.
  - [`distributed-systems-reliability.md`](architecture-foundations/distributed-systems-reliability.md): DDIA (Kleppmann), Release It! stability patterns (Nygard), Database Internals (Petrov), Google SRE SLOs & error budgets.
  - [`evolutionary-delivery-architecture.md`](architecture-foundations/evolutionary-delivery-architecture.md): Automated architectural fitness functions, connascence, Continuous Delivery, DORA metrics, Team Topologies.
- [`ai-ml/`](ai-ml/):
  - [`llm-integration.md`](ai-ml/llm-integration.md): LLM gateways, structured outputs, RAG, MCP/A2A, OWASP Agentic guardrails, and OTel GenAI telemetry.
- [`backend/`](backend/):
  - [`api-design.md`](backend/api-design.md): REST, GraphQL, gRPC, Idempotency, Pagination, and Error envelopes.
  - [`caching-strategies.md`](backend/caching-strategies.md): Redis patterns, Cache-aside, Stampede prevention, and TTL strategies.
- [`database/`](database/):
  - [`postgresql-mastery.md`](database/postgresql-mastery.md): Indexing, EXPLAIN ANALYZE, PostgreSQL 18 upgrades, Connection pooling, and Locks.
- [`devops-infrastructure/`](devops-infrastructure/):
  - [`docker-containers.md`](devops-infrastructure/docker-containers.md): Multi-stage builds, non-root users, layer caching, and distroless images.
  - [`kstack-cluster-operations.md`](devops-infrastructure/kstack-cluster-operations.md): Agentic Kubernetes forensics, 4-pillar cluster auditing, and zero-leak ephemeral debug cleanup (`kstack`).
  - [`observability-telemetry.md`](devops-infrastructure/observability-telemetry.md): OpenTelemetry, structured JSON logging, distributed tracing, and metrics.
- [`erp-enterprise/`](erp-enterprise/):
  - [`core-accounting-ledger.md`](erp-enterprise/core-accounting-ledger.md) & [`inventory-supply-chain.md`](erp-enterprise/inventory-supply-chain.md): Immutable double-entry ledgers and atomic stock reservations.
- [`frontend/`](frontend/):
  - [`design-systems-ui-craft.md`](frontend/design-systems-ui-craft.md) (OKLCH tokens, modern CSS `@layer`/`@container`/Popover/View Transitions, headless primitives, anti-slop UI craft), [`accessibility.md`](frontend/accessibility.md), [`state-management.md`](frontend/state-management.md), and [`web-performance.md`](frontend/web-performance.md).
- [`systems-kernel/`](systems-kernel/):
  - [`linux-kernel-driver.md`](systems-kernel/linux-kernel-driver.md): Linux kernel modules, concurrency locks, and DMA safety.
- [`testing-qa/`](testing-qa/):
  - [`test-pyramid.md`](testing-qa/test-pyramid.md): Testing strategy, Unit, Integration with Testcontainers, and E2E with Playwright.
