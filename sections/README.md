# 🏗️ Cross-Cutting Architectural Sections (`sections/`)

This directory houses cross-cutting engineering domains that span across frameworks and languages.

## Subdirectories

- [`backend/`](backend/):
  - [`api-design.md`](backend/api-design.md): REST, GraphQL, gRPC, Idempotency, Pagination, and Error envelopes.
  - [`caching-strategies.md`](backend/caching-strategies.md): Redis patterns, Cache-aside, Stampede prevention, and TTL strategies.
- [`database/`](database/):
  - [`postgresql-mastery.md`](database/postgresql-mastery.md): Indexing, EXPLAIN ANALYZE, Connection pooling, and Locks.
- [`devops-infrastructure/`](devops-infrastructure/):
  - [`docker-containers.md`](devops-infrastructure/docker-containers.md): Multi-stage builds, non-root users, layer caching, and distroless images.
  - [`observability-telemetry.md`](devops-infrastructure/observability-telemetry.md): OpenTelemetry, structured JSON logging, distributed tracing, and metrics.
- [`frontend/`](frontend/):
  - [`state-management.md`](frontend/state-management.md): Server state vs Client state, TanStack Query, and Zustand.
- [`testing-qa/`](testing-qa/):
  - [`test-pyramid.md`](testing-qa/test-pyramid.md): Testing strategy, Unit, Integration with Testcontainers, and E2E with Playwright.
