# 🧭 Deterministic Agent Routing Matrix (`ROUTING.md`)

> **Classification**: Machine-Readable & Human-Auditable Agent Navigation Engine  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, LLM Orchestrator Engines, Engineering Leads  
> **Objective**: Eliminate token bloat, prevent rule omissions, and guarantee deterministic task execution by prescribing the exact file reading lists and verification pipelines for every software task archetype.

---

## 1. How to Use This Matrix

When an autonomous agent receives an engineering instruction:
1. **Identify the Task Archetype** from the 10 categories below.
2. **Ingest ONLY the Prescribed Files** in the strict sequential order listed under **Mandatory Reading List**. Do not waste context reading unrelated subsystems.
3. **Enforce the Mandatory Invariants** associated with that archetype.
4. **Execute the Verification Commands** and embed the resulting **`prove-it-works` Evidence Block** in the final delivery.

```
                          AGENT TASK ROUTING FLOW
                          
   [User Prompt Received] 
             │
             ▼
   [Classify Task Archetype] (e.g., Bug Fix, API Endpoint, Frontend UI, Migration)
             │
             ▼
   [Query ROUTING.md Matrix] ──► Fetch Exact Reading List (Max 3-5 Core Files)
             │
             ▼
   [Execute Phase 1-5 Lifecycle] 
             │
             ▼
   [Run Archetype-Specific Verification Commands] (Exit Code 0 Required)
             │
             ▼
   [Generate Scorecard against DEFINITION_OF_DONE.md]
```

---

## 2. Universal Pre-Flight Baseline (All Tasks)

Regardless of archetype, every agent session MUST adhere to:
- [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) (Universal Invariants: R-001 No TODOs, R-002 No Mock Data, R-034 No Any, R-064 No Secrets)
- [`agents/poteto-discipline.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/poteto-discipline.md) (Minimal surgical diffs, no conversational slop, concrete CLI execution proof)

---

## 3. Archetype Routing Catalog

---

### Archetype 1: Bug Fix & Defect Remediation

*Fixing a reported runtime error, crash, unexpected behavior, or logic flaw.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/tdd-reproduction.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/tdd-reproduction.md) *(TDD Bug Reproduction Protocol)*<br>2. [`MISTAKES.md`](file:///home/agy/.t3/userdata/attachments/devskill/MISTAKES.md) *(Known AI Pitfalls)*<br>3. Target Language Guide (e.g. [`languages/typescript.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/typescript.md) or [`languages/python.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/python.md))<br>4. Target failing test file and immediate source module |
| **Key Invariant Rules** | **R-086** (Red-Green TDD reproduction before editing source), **R-181** (Prove-It-Works proof), **R-182** (Minimal surgical diff), **R-183** (Reproduction test committed) |
| **Prohibited Actions** | ❌ Modifying production code before reproducing the bug with a failing test.<br>❌ Weakening test assertions or deleting existing tests to get a green exit code.<br>❌ Reformatting entire files or rewriting unrelated functions. |
| **Mandatory Verification** | 1. Reproduce Red: `npm test -- path/to/repro.test.ts` (Exit code != 0 observed)<br>2. Apply fix<br>3. Verify Green: `npm test -- path/to/repro.test.ts` (Exit code 0 observed)<br>4. Full Regression: `npm test` (All tests pass) |

---

### Archetype 2: New Backend API Endpoint / Webhook Handler

*Implementing a new REST route, GraphQL mutation, gRPC service, or external webhook receiver.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/backend/api-design.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/backend/api-design.md) *(RFC 9457 errors, Idempotency, Webhooks)*<br>2. [`security.md`](file:///home/agy/.t3/userdata/attachments/devskill/security.md) *(OWASP Top 10, AuthN/AuthZ, Input Sanitization)*<br>3. Target Backend Framework (e.g. [`frameworks/backend/fastapi.md`](file:///home/agy/.t3/userdata/attachments/devskill/frameworks/backend/fastapi.md) or [`frameworks/backend/nestjs.md`](file:///home/agy/.t3/userdata/attachments/devskill/frameworks/backend/nestjs.md))<br>4. [`sections/testing-qa/integration-contract.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/testing-qa/integration-contract.md) |
| **Key Invariant Rules** | **R-051** (RESTful nouns), **R-054** (RFC 9457 error envelope), **R-055** (Keyset cursor pagination), **R-060** (Zod/Pydantic schema validation at ingress), **R-061** (Parameterized SQL queries), **R-184** (Stripe-grade IETF Idempotency-Key on mutations per `api-design.md#81`), **R-185** (HMAC-SHA256 signature check for webhooks per `api-design.md#82`) |
| **Prohibited Actions** | ❌ Returning 200 OK with `{ error: "..." }` body.<br>❌ Exposing raw database IDs or stack traces in error responses.<br>❌ Mutating state without atomic idempotency lock & payload hash verification.<br>❌ Using offset-based pagination (`OFFSET N`) on high-volume endpoints. |
| **Mandatory Verification** | 1. Unit & Schema Tests: `npm test -- tests/unit/api/`<br>2. Integration Tests with Testcontainers/DB: `npm test -- tests/integration/api/`<br>3. Security & Parameterization Scan: `git grep -EIn "(query\(\`.*\\\$\{)" src/` (Zero unparameterized queries) |

---

### Archetype 3: Frontend UI Component, Screen or Form

*Building or modifying user interfaces in React, Next.js, Vue, or mobile frameworks.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`FRONTEND.md`](file:///home/agy/.t3/userdata/attachments/devskill/FRONTEND.md) *(Frontend Architecture & Core Web Vitals)*<br>2. [`sections/frontend/accessibility-a11y.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/frontend/accessibility-a11y.md) *(WCAG 2.2 AA, ARIA roles, Keyboard focus)*<br>3. Target Framework (e.g. [`frameworks/frontend/nextjs.md`](file:///home/agy/.t3/userdata/attachments/devskill/frameworks/frontend/nextjs.md) or [`frameworks/frontend/react.md`](file:///home/agy/.t3/userdata/attachments/devskill/frameworks/frontend/react.md))<br>4. [`sections/frontend/web-performance.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/frontend/web-performance.md) |
| **Key Invariant Rules** | **R-129** (WCAG 2.2 Level AA color contrast), **R-130** (Full keyboard operability), **R-131** (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1), **R-135** (Native semantic HTML tags), **R-137** (Explicit label and error associations), **R-141** (SSR hydration hygiene, no client APIs in root render) |
| **Prohibited Actions** | ❌ Using `<div onClick={...}>` in place of `<button>`.<br>❌ Missing visible focus outlines for keyboard navigation (`outline: none` without focus ring).<br>❌ Using `'use client'` at layout or page roots when React Server Components can be used.<br>❌ Loading below-the-fold images without `loading="lazy"` or above-the-fold images without `fetchpriority="high"`. |
| **Mandatory Verification** | 1. Accessibility Tree & Unit Tests: `npm test -- tests/components/`<br>2. E2E Keyboard & Screen Reader Test: `npx playwright test tests/e2e/`<br>3. Static A11y Lint: `npx eslint --rule 'jsx-a11y/*: error' src/` |

---

### Archetype 4: Database Schema Alteration & Migration

*Adding tables, altering columns, adding indexes, or changing relational constraints.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/database/schema-migrations.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/database/schema-migrations.md) *(Expand/Contract Pattern, Zero Downtime)*<br>2. [`sections/database/postgresql-mastery.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/database/postgresql-mastery.md) *(Index types, Locking mechanics, EXPLAIN)*<br>3. [`languages/sql.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/sql.md) *(ANSI SQL standards, Transactions)*<br>4. Target ORM config / migration directory |
| **Key Invariant Rules** | **R-065** (Schema migrations automated & committed), **R-066** (Expand/Contract zero-downtime migrations), **R-067** (Composite indexes ordered by equality then range), **R-072** (Foreign keys backed by explicit indexes), **R-073** (Safe online migrations, `CONCURRENTLY` for index creation) |
| **Prohibited Actions** | ❌ Renaming or dropping an active column in a single migration step (breaks running instances).<br>❌ Adding `NOT NULL` without a default value on populated production tables.<br>❌ Creating indexes without `CONCURRENTLY` in PostgreSQL (locks write traffic).<br>❌ Executing migrations without backwards-compatible rollback scripts. |
| **Mandatory Verification** | 1. Up & Down Migration Test: Run migration `up`, verify schema, run migration `down`, verify rollback.<br>2. Query Plan Verification: `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` showing index scan rather than sequential scan. |

---

### Archetype 5: Distributed Observability & SRE Alerting

*Instrumenting telemetry, logging pipelines, Prometheus metrics, and Google SRE alerts.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`OBSERVABILITY.md`](file:///home/agy/.t3/userdata/attachments/devskill/OBSERVABILITY.md) *(Observability Architecture & Core Standards)*<br>2. [`sections/devops-infrastructure/observability-telemetry.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/devops-infrastructure/observability-telemetry.md) *(OTel, Google SRE 4 Golden Signals, Multi-Burn Alerts)*<br>3. [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) (Section 10 & Section 14) |
| **Key Invariant Rules** | **R-142** (Structured JSON logs to stdout), **R-143** (Distributed W3C Trace Context propagation), **R-144** (PII and secret log scrubbing), **R-145** (`/healthz` and `/readyz` probes), **R-146** (Four Golden Signals: Latency, Traffic, Errors, Saturation), **R-148** (Low-cardinality metric labels), **R-187** (Full jitter backoff), **R-188** (Goroutine lifecycle ownership) |
| **Prohibited Actions** | ❌ Emitting raw `console.log("here")` or unformatted multi-line strings.<br>❌ Injecting user IDs, emails, or unbounded UUIDs into Prometheus metric labels (cardinality explosion).<br>❌ Logging credit cards, passwords, or Authorization bearer tokens.<br>❌ Failing to propagate `traceparent` across asynchronous HTTP or queue boundaries. |
| **Mandatory Verification** | 1. Log Structure Check: Verify JSON schema compliance of stdout logs.<br>2. Trace Context Propagation Test: Verify downstream spans inherit parent `trace_id`.<br>3. Metric Cardinality Audit: Confirm label values are bounded enums. |

---

### Archetype 6: Performance & Memory Optimization

*Eliminating high p99 latency, fixing CPU spikes, resolving memory leaks or goroutine leaks.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. Target Language Guide (e.g. [`languages/golang.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/golang.md) or [`languages/typescript.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/typescript.md))<br>2. [`sections/database/connection-pooling.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/database/connection-pooling.md) *(Pool sizing, timeouts, deadlocks)*<br>3. [`agents/poteto-discipline.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/poteto-discipline.md) *(Measure, prove, minimal diff)* |
| **Key Invariant Rules** | **R-114** (Database connection pool bounded), **R-115** (Client HTTP connection reuse), **R-116** (Zero unbuffered channel deadlock risks), **R-187** (Full jitter exponential backoff), **R-188** (Goroutine lifecycle ownership & zero leaks) |
| **Prohibited Actions** | ❌ Optimizing without profiling evidence (use `pprof`, flamegraphs, or benchmark tests).<br>❌ Spawning unmonitored background tasks or detached goroutines.<br>❌ Increasing pool size blindly without considering database backend memory limits. |
| **Mandatory Verification** | 1. Benchmark Execution: `go test -bench=. -benchmem` or `node --prof`<br>2. Race & Leak Test: `go test -race` or memory heap dump comparison.<br>3. p99 Latency Verification: Demonstrable reduction in execution time or allocation bytes. |

---

### Archetype 7: Security Audit & Vulnerability Remediation

*Fixing OWASP Top 10 vulnerabilities, addressing CVEs, resolving secret leaks, hardening auth.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`security.md`](file:///home/agy/.t3/userdata/attachments/devskill/security.md) *(OWASP Top 10, Auth Specs, Secret Management)*<br>2. [`pipelines/security-scanning-sast.md`](file:///home/agy/.t3/userdata/attachments/devskill/pipelines/security-scanning-sast.md) *(SAST, DAST, Secret scanners)*<br>3. [`agents/tdd-reproduction.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/tdd-reproduction.md) *(Reproduction before patching)* |
| **Key Invariant Rules** | **R-060** (Strict schema parsing at boundaries), **R-061** (SQL parameterization), **R-062** (Argon2id password hashing), **R-063** (Constant-time string comparison for signatures), **R-064** (Zero secrets in repo), **R-185** (HMAC-SHA256 signature verification) |
| **Prohibited Actions** | ❌ Committing mock secrets, real keys, or certificates into git history.<br>❌ Using `crypto.timingSafeEqual` with unequal buffer lengths (causes crash).<br>❌ Disabling security linters or suppressing SAST warnings with comments. |
| **Mandatory Verification** | 1. Security Scan: `git grep -EIn "(AKIA[0-9A-Z]{16}|sk_live_[0-9a-zA-Z]{24})"`<br>2. Dependency Audit: `npm audit --audit-level=high` or `govulncheck ./...`<br>3. SAST Scan: Verify clean scan with Semgrep or local scanner. |

---

### Archetype 8: CI/CD Pipeline & Deployment Automation

*Writing or modifying GitHub Actions, GitLab CI, Dockerfiles, or deployment manifests.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`DEPLOYMENT.md`](file:///home/agy/.t3/userdata/attachments/devskill/DEPLOYMENT.md) *(Deployment & Release Strategy)*<br>2. [`pipelines/github-actions.md`](file:///home/agy/.t3/userdata/attachments/devskill/pipelines/github-actions.md) *(or `gitlab-ci.md`)*<br>3. [`sections/devops-infrastructure/docker-containers.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/devops-infrastructure/docker-containers.md) *(Rootless, Multi-stage, Distroless)*<br>4. [`pipelines/deployment-strategies.md`](file:///home/agy/.t3/userdata/attachments/devskill/pipelines/deployment-strategies.md) |
| **Key Invariant Rules** | **R-153** (Twelve-Factor App compliance), **R-154** (Non-root container user), **R-155** (Multi-stage minimal builds), **R-156** (Base image pinned by SHA-256 digest), **R-157** (Zero-downtime rolling/canary deployments), **R-160** (Explicit CPU & memory requests/limits) |
| **Prohibited Actions** | ❌ Running containers as `root` (UID 0).<br>❌ Using mutable image tags like `:latest` in production manifests.<br>❌ Storing environment credentials directly inside Dockerfile `ENV` or workflow YAML. |
| **Mandatory Verification** | 1. Container Build Test: `docker build --tag test:local .`<br>2. Container Security Scan: `trivy image test:local` (Zero CRITICAL vulnerabilities)<br>3. Rootless Check: `docker run --rm test:local id` (UID != 0) |

---

### Archetype 9: Architecture Evaluation & System Design

*Designing new subsystems, picking frameworks/databases, or planning modular monoliths.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/arena-evaluator.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/arena-evaluator.md) *(Multi-Solution Arena Scoring)*<br>2. [`decisions.md`](file:///home/agy/.t3/userdata/attachments/devskill/decisions.md) *(Architecture Decision Trees)*<br>3. [`ARCHITECTURE.md`](file:///home/agy/.t3/userdata/attachments/devskill/ARCHITECTURE.md) *(Domain-Driven Design, Hexagonal Boundaries)*<br>4. [`specs.md`](file:///home/agy/.t3/userdata/attachments/devskill/specs.md) |
| **Key Invariant Rules** | **R-117** (Modular monolith before microservices), **R-118** (Hexagonal Ports & Adapters separation), **R-187** (Full jitter backoff & circuit breakers), **R-190** (Arena scorecard documented before implementation) |
| **Prohibited Actions** | ❌ Selecting a technology based on novelty without computing a 5-pillar Arena scorecard.<br>❌ Creating circular dependencies between domain modules.<br>❌ Mixing persistence infrastructure directly into domain entity models. |
| **Mandatory Verification** | 1. Arena Scorecard Table generated and checked into `decisions.md`.<br>2. Architecture Diagram (ASCII or Mermaid) verifying unidirectional dependency flow. |

---

### Archetype 10: Refactoring & Code Quality Modernization

*Restructuring code, eliminating technical debt, cleaning up types, or removing anti-patterns.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/poteto-discipline.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/poteto-discipline.md) *(Minimal diffs, zero commentary noise)*<br>2. [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) *(Universal Engineering Laws)*<br>3. Target Language Guide (e.g. [`languages/typescript.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/typescript.md))<br>4. [`DEFINITION_OF_DONE.md`](file:///home/agy/.t3/userdata/attachments/devskill/DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-001** (Zero deferred markers: TODO/FIXME), **R-034** (Zero `any` / `@ts-ignore`), **R-046** (No swallowed exceptions), **R-164** (Atomic commits), **R-182** (Minimal surgical diffs) |
| **Prohibited Actions** | ❌ Changing external public API signatures during internal refactors.<br>❌ Reformatting entire files unrelated to the refactored logic.<br>❌ Introducing any regressions in the test suite. |
| **Mandatory Verification** | 1. `git diff --stat` confirming small surgical scope.<br>2. Typecheck: `npx tsc --noEmit` or `mypy --strict .` (0 errors)<br>3. Regression Suite: Full test run passing with 100% green. |

---

## 4. Conflict Resolution Protocol

If two guides or rules appear to conflict in a specific context:
1. **Security & Data Integrity ALWAYS Wins**: `RULES.md` and `security.md` override any framework-specific convenience.
2. **Standard Library Over Third-Party**: When functionality exists natively in the target runtime (e.g., Node.js `crypto.timingSafeEqual` or Go `net/http`), prefer native implementation over adding an unverified micro-package.
3. **Explicit Typing Over Implicit Inference**: When type inference produces `unknown` or loose types, provide explicit schema parsing.
4. **Escalation**: If a genuine contradiction between project constraints is detected, invoke the **3-Strike Escalation Protocol** in [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md) Section 7.
