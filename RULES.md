# 📜 Universal Engineering Rules (`RULES.md`)

> **Status**: Non-Negotiable Law  
> **Applicability**: All AI Agents and Engineers across all languages, frameworks, and repositories.  
> **Enforcement**: Automated CI/CD gates, Static Analysis, Code Review, and Pre-Commit Hooks.

---

## 1. Architectural Integrity

1. **Law of Separation of Concerns**:
   - Never mix domain business logic with transport layers (HTTP/gRPC/CLI) or persistence layers (ORM/SQL).
   - Use Hexagonal / Clean / Layered architecture:
     ```
     Transport (Controllers / Handlers)
          │ calls
          ▼
     Application / Service Layer (Use Cases & Business Logic)
          │ calls
          ▼
     Domain Layer (Entities, Value Objects, Domain Events)
          │ calls
          ▼
     Infrastructure (DB Repositories, Third-party Clients, Messaging)
     ```
2. **Stateless Service Design**:
   - Application servers and API handlers must be completely stateless.
   - Session state must reside in external distributed caches (e.g., Redis) or encrypted client-side tokens (e.g., secure cookies).
   - Never store local in-memory state that prevents horizontal scaling or container restarts.
3. **Idempotency by Default**:
   - Any mutating operation that could be retried (payment processing, order placement, webhook emission) MUST require an `Idempotency-Key` header or deterministic deduplication token.
4. **Graceful Degradation & Circuit Breaking**:
   - All network calls to external downstream dependencies (APIs, microservices, caches) must feature explicit timeouts (maximum 2000ms default), retries with exponential backoff and jitter, and circuit breakers (e.g., resilience4j, Polly, opossum).

---

## 2. Code Quality & Type Safety

1. **Strict Type Systems**:
   - TypeScript: `"strict": true`, `"noImplicitAny": true`, `"exactOptionalPropertyTypes": true`. Never use `any`. Use `unknown` with runtime type narrowing.
   - Python: Complete type hints (`typing` / `types`). Enforce with `mypy --strict` and `ruff`. Never leave return types or function parameters untyped.
   - Go: Explicit error handling checking `if err != nil`. Never ignore returned errors with `_`.
   - Rust: Handle `Result` and `Option` explicitly via pattern matching or `?`. Never use `unwrap()` in production paths.
2. **Explicit Error Handling (No Silent Swallowing)**:
   - Never use empty `catch {}` or `except: pass` blocks.
   - Errors must either be handled with a verified fallback or translated into a domain exception with contextual metadata and re-thrown.
   - Stack traces must be captured in internal logs but NEVER returned in client-facing HTTP responses.
3. **No Magic Values**:
   - All constants, configurations, status codes, and timeouts must be defined as named constants, enums, or configuration variables.
4. **Single Responsibility per Function**:
   - Functions should do one thing and do it predictably. Target maximum cyclomatic complexity ≤ 10 and length ≤ 40 lines.
   - Favor pure functions with predictable inputs and outputs without hidden side effects.

---

## 3. Database & Persistence Hygiene

1. **No Unbounded Queries**:
   - Never issue `SELECT *` in production code. Request only the specific columns needed.
   - Never query without explicit `LIMIT` and pagination controls (Keyset/Cursor-based pagination preferred over offset-based for large datasets).
2. **Zero N+1 Query Tolerance**:
   - ORM relationships must use eager loading (`select_related`, `prefetch_related`, `include`, `joinedload`) or batch loaders (DataLoader).
   - Every list endpoint must be verified against query count analyzers.
3. **Atomic Transactions**:
   - Any multi-step write mutation spanning multiple rows or tables must execute inside an explicit atomic database transaction (`BEGIN ... COMMIT / ROLLBACK`).
4. **Index All Filtering & Joining Columns**:
   - Every foreign key must have an index.
   - Query filters (`WHERE status = ?`, `ORDER BY created_at DESC`) must have composite indexes aligned with query selectivity.
5. **Zero-Downtime Migrations**:
   - Database schema changes must follow the Expand/Contract pattern:
     1. Add new nullable column / new table.
     2. Write to both old and new columns.
     3. Backfill existing rows.
     4. Switch read paths to new column.
     5. Remove old column in a subsequent release.
   - Never lock production tables with blocking `ALTER TABLE` operations.

---

## 4. Zero-Compromise Security

1. **Input Validation at System Boundaries**:
   - All external inputs (request bodies, query params, headers, files, webhooks) must be validated through strict runtime schema parsers (e.g., Zod, Pydantic, Joi) BEFORE reaching business logic.
   - Fail fast with structured 422/400 validation error responses.
2. **Parameterized Queries Only**:
   - Never concatenate, interpolate, or format strings into SQL, NoSQL, LDAP, or shell commands.
   - Always use prepared statements or parameterized queries.
3. **Principle of Least Privilege**:
   - Database connection users must have only the permissions required for their role (e.g., no `DROP`, `ALTER`, or superuser permissions for the web application role).
   - Container processes must run as non-root users (`USER 10001`).
4. **Zero Secrets in Source Control**:
   - Secrets, API keys, private certificates, and passwords must never be committed to git.
   - Enforce pre-commit scanning with `gitleaks` and `trivy`.
   - Inject secrets via environment variables from secure secret vaults (Vault, AWS Secrets Manager, Doppler).
5. **Defense-in-Depth Authentication & Authorization**:
   - Authenticate every request.
   - Validate authorization (RBAC/ABAC) at the service/controller method level, not just the network routing edge.
   - Protect all APIs against brute force with rate limiters (Token bucket / Leaky bucket via Redis).

---

## 5. Testing & Verification

1. **The Production Test Pyramid**:
   - **Unit Tests (70%)**: Fast, in-memory, deterministic testing of isolated domain logic without external dependencies.
   - **Integration Tests (20%)**: Testing data access, service interaction, and API endpoints using ephemeral containers (Testcontainers).
   - **End-to-End Tests (10%)**: Critical business flows (e.g., Checkout, Signup, Onboarding) using real browser automation (Playwright).
2. **Deterministic & Flake-Free**:
   - Never use arbitrary `sleep(ms)` or timers in test assertions. Use polling assertions with explicit predicate conditions.
   - Mock all third-party external networks and paid APIs (Stripe, Twilio, OpenAI) using reliable mock servers (WireMock, MSW).
3. **Test Failure Paths**:
   - For every happy path test, write at least two failure path tests (invalid inputs, network timeout, unauthorized access, resource conflict).

---

## 6. Observability & Telemetry

1. **Structured JSON Logging**:
   - Logs must be formatted as structured JSON with standardized fields:
     - `timestamp` (ISO 8601 UTC)
     - `level` (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`)
     - `message` (human-readable event description)
     - `trace_id` / `span_id` (OpenTelemetry distributed tracing context)
     - `service` (service name)
     - `context` (relevant IDs like `user_id`, `org_id`, `request_id`)
2. **Sanitize Log Data**:
   - PII (Personally Identifiable Information), passwords, tokens, full credit card numbers, and secret keys must be redacted before writing to log streams.
3. **Health & Readiness Checks**:
   - Every service must provide `/healthz` (liveness: process running) and `/readyz` (readiness: DB, cache, and dependent systems connected and responding).

---

## 7. Versioning & Git Cleanliness

1. **Conventional Commits**:
   - All commits must follow the standard: `<type>(<scope>): <short summary>`  
     Types: `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `chore`, `ci`.
2. **Atomic Pull Requests**:
   - Keep PRs focused on a single logical change. Target ≤ 400 lines changed per PR.
3. **Self-Documenting Code**:
   - Write clean, self-explanatory variable and function names. Comments should explain *why* an unusual decision was made, never *what* self-evident code does.
