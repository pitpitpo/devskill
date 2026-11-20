# 🧭 Deterministic Agent Routing Matrix (`ROUTING.md`)

> **Classification**: Machine-Readable & Human-Auditable Agent Navigation Engine  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, LLM Orchestrator Engines, Engineering Leads  
> **Objective**: Eliminate token bloat, prevent rule omissions, and guarantee deterministic task execution by prescribing the exact file reading lists and verification pipelines for every software task archetype.  
> **Last Updated**: 2026-11-20

---

## 1. How to Use This Matrix

When an autonomous agent receives an engineering instruction:
1. **Identify the Task Archetype** from the 30 categories below.
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
- [`RULES.md`](RULES.md) (Universal Invariants: R-001 No TODOs, R-002 No Mock Data, R-034 No Any, R-064 No Secrets)
- [`agents/poteto-discipline.md`](agents/poteto-discipline.md) (Minimal surgical diffs, no conversational slop, concrete CLI execution proof)
- [`agents/zero-missed-requirements.md`](agents/zero-missed-requirements.md) *(Mandatory whenever a task has ≥ 4 requirements, spans multiple subsystems, or specifies strict negative constraints — R-261–R-265)*

---

## 3. Archetype Routing Catalog

---

### Archetype 1: Bug Fix & Defect Remediation

*Fixing a reported runtime error, crash, unexpected behavior, or logic flaw.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/tdd-reproduction.md`](agents/tdd-reproduction.md) *(TDD Bug Reproduction Protocol)*<br>2. [`MISTAKES.md`](MISTAKES.md) *(Known AI Pitfalls)*<br>3. Target Language Guide (e.g. [`languages/typescript.md`](languages/typescript.md) or [`languages/python.md`](languages/python.md))<br>4. Target failing test file and immediate source module |
| **Key Invariant Rules** | **R-005** & **R-183** (Red-Green TDD reproduction before editing source), **R-181** (Prove-It-Works proof), **R-182** (Minimal surgical diff), **R-086** (Test isolation & independence) |
| **Prohibited Actions** | ❌ Modifying production code before reproducing the bug with a failing test.<br>❌ Weakening test assertions or deleting existing tests to get a green exit code.<br>❌ Reformatting entire files or rewriting unrelated functions. |
| **Mandatory Verification** | 1. Reproduce Red: `npm test -- path/to/repro.test.ts` (Exit code != 0 observed)<br>2. Apply fix<br>3. Verify Green: `npm test -- path/to/repro.test.ts` (Exit code 0 observed)<br>4. Full Regression: `npm test` (All tests pass) |

---

### Archetype 2: New Backend API Endpoint / Webhook Handler

*Implementing a new REST route, GraphQL mutation, gRPC service, or external webhook receiver.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/backend/api-design.md`](sections/backend/api-design.md) *(RFC 9457 errors, Idempotency, Webhooks)*<br>2. [`security.md`](security.md) *(OWASP Top 10, AuthN/AuthZ, Input Sanitization)*<br>3. Target Backend Framework (e.g. [`frameworks/backend/fastapi.md`](frameworks/backend/fastapi.md) or [`frameworks/backend/nestjs.md`](frameworks/backend/nestjs.md))<br>4. [`sections/testing-qa/integration-contract.md`](sections/testing-qa/integration-contract.md) |
| **Key Invariant Rules** | **R-048** (RFC 9457 Problem Details error envelope), **R-060** (Zod/Pydantic schema parsing at ingress), **R-061** (Parameterized SQL queries), **R-105** & **R-186** (Keyset cursor pagination), **R-184** (Stripe-grade IETF Idempotency-Key on mutations per `api-design.md#81`), **R-185** (HMAC-SHA256 signature check for webhooks per `api-design.md#82`), **R-189** (Nominal branding for domain IDs) |
| **Prohibited Actions** | ❌ Returning 200 OK with `{ error: "..." }` body.<br>❌ Exposing raw database IDs or stack traces in error responses.<br>❌ Mutating state without atomic idempotency lock & payload hash verification.<br>❌ Using offset-based pagination (`OFFSET N`) on high-volume endpoints. |
| **Mandatory Verification** | 1. Unit & Schema Tests: `npm test -- tests/unit/api/`<br>2. Integration Tests with Testcontainers/DB: `npm test -- tests/integration/api/`<br>3. Security & Parameterization Scan: `git grep -EIn "(query\(\`.*\\\$\{)" src/` (Zero unparameterized queries) |

---

### Archetype 3: Frontend UI Component, Screen or Form

*Building or modifying user interfaces in React, Next.js, Vue, or mobile frameworks.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`FRONTEND.md`](FRONTEND.md) *(Frontend Architecture & Core Web Vitals)*<br>2. [`sections/frontend/accessibility.md`](sections/frontend/accessibility.md) *(WCAG 2.2 AA, ARIA roles, Keyboard focus)*<br>3. Target Framework (e.g. [`frameworks/frontend/nextjs.md`](frameworks/frontend/nextjs.md) or [`frameworks/frontend/react.md`](frameworks/frontend/react.md))<br>4. [`sections/frontend/web-performance.md`](sections/frontend/web-performance.md) |
| **Key Invariant Rules** | **R-129** (WCAG 2.2 Level AA color contrast), **R-130** (Full keyboard operability), **R-131** (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1), **R-135** (Native semantic HTML tags), **R-137** (Explicit label and error associations), **R-141** (SSR hydration hygiene, no client APIs in root render) |
| **Prohibited Actions** | ❌ Using `<div onClick={...}>` in place of `<button>`.<br>❌ Missing visible focus outlines for keyboard navigation (`outline: none` without focus ring).<br>❌ Using `'use client'` at layout or page roots when React Server Components can be used.<br>❌ Loading below-the-fold images without `loading="lazy"` or above-the-fold images without `fetchpriority="high"`. |
| **Mandatory Verification** | 1. Accessibility Tree & Unit Tests: `npm test -- tests/components/`<br>2. E2E Keyboard & Screen Reader Test: `npx playwright test tests/e2e/`<br>3. Static A11y Lint: `npx eslint --rule 'jsx-a11y/*: error' src/` |

---

### Archetype 4: Database Schema Alteration & Migration

*Adding tables, altering columns, adding indexes, or changing relational constraints.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/database/schema-migrations.md`](sections/database/schema-migrations.md) *(Expand/Contract Pattern, Zero Downtime)*<br>2. [`sections/database/postgresql-mastery.md`](sections/database/postgresql-mastery.md) *(Index types, Locking mechanics, EXPLAIN)*<br>3. [`languages/sql.md`](languages/sql.md) *(ANSI SQL standards, Transactions)*<br>4. Target ORM config / migration directory |
| **Key Invariant Rules** | **R-103** (Mandatory atomic transactions), **R-106** (Database foreign key constraints), **R-107** (Index all query predicates), **R-108** (Zero-downtime Expand/Contract migrations), **R-109** (Non-blocking DDL operations, `CONCURRENTLY` for index creation) |
| **Prohibited Actions** | ❌ Renaming or dropping an active column in a single migration step (breaks running instances).<br>❌ Adding `NOT NULL` without a default value on populated production tables.<br>❌ Creating indexes without `CONCURRENTLY` in PostgreSQL (locks write traffic).<br>❌ Executing migrations without backwards-compatible rollback scripts. |
| **Mandatory Verification** | 1. Up & Down Migration Test: Run migration `up`, verify schema, run migration `down`, verify rollback.<br>2. Query Plan Verification: `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` showing index scan rather than sequential scan. |

---

### Archetype 5: Distributed Observability & SRE Alerting

*Instrumenting telemetry, logging pipelines, Prometheus metrics, and Google SRE alerts.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`OBSERVABILITY.md`](OBSERVABILITY.md) *(Observability Architecture & Core Standards)*<br>2. [`sections/devops-infrastructure/observability-telemetry.md`](sections/devops-infrastructure/observability-telemetry.md) *(OTel, Google SRE 4 Golden Signals, Multi-Burn Alerts)*<br>3. [`RULES.md`](RULES.md) (Section 10 & Section 14) |
| **Key Invariant Rules** | **R-142** (Structured JSON logs to stdout), **R-143** (Distributed W3C Trace Context propagation), **R-144** (PII and secret log scrubbing), **R-145** (`/healthz` and `/readyz` probes), **R-146** (Four Golden Signals: Latency, Traffic, Errors, Saturation), **R-148** (Low-cardinality metric labels), **R-151** (OpenTelemetry semantic & GenAI conventions), **R-187** (Full jitter backoff), **R-188** (Goroutine lifecycle ownership) |
| **Prohibited Actions** | ❌ Emitting raw `console.log("here")` or unformatted multi-line strings.<br>❌ Injecting user IDs, emails, or unbounded UUIDs into Prometheus metric labels (cardinality explosion).<br>❌ Logging credit cards, passwords, or Authorization bearer tokens.<br>❌ Failing to propagate `traceparent` across asynchronous HTTP or queue boundaries. |
| **Mandatory Verification** | 1. Log Structure Check: Verify JSON schema compliance of stdout logs.<br>2. Trace Context Propagation Test: Verify downstream spans inherit parent `trace_id`.<br>3. Metric Cardinality Audit: Confirm label values are bounded enums. |

---

### Archetype 6: Performance & Memory Optimization

*Eliminating high p99 latency, fixing CPU spikes, resolving memory leaks or goroutine leaks.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. Target Language Guide (e.g. [`languages/golang.md`](languages/golang.md) or [`languages/typescript.md`](languages/typescript.md))<br>2. [`sections/database/connection-pooling.md`](sections/database/connection-pooling.md) *(Pool sizing, timeouts, deadlocks)*<br>3. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Measure, prove, minimal diff)* |
| **Key Invariant Rules** | **R-044** (Bounded resource allocation & memory ceilings), **R-111** (Connection pool sizing & lifecycle), **R-187** (Full jitter exponential backoff & circuit breakers), **R-188** (Goroutine lifecycle ownership & zero leaks), **R-212** (Scientific benchmark discipline) |
| **Prohibited Actions** | ❌ Optimizing without profiling evidence (use `pprof`, flamegraphs, or benchmark tests).<br>❌ Spawning unmonitored background tasks or detached goroutines.<br>❌ Increasing pool size blindly without considering database backend memory limits. |
| **Mandatory Verification** | 1. Benchmark Execution: `go test -bench=. -benchmem` or `node --prof`<br>2. Race & Leak Test: `go test -race` or memory heap dump comparison.<br>3. p99 Latency Verification: Demonstrable reduction in execution time or allocation bytes. |

---

### Archetype 7: Security Audit & Vulnerability Remediation

*Fixing OWASP Top 10:2025 & Agentic ASI01–ASI10 vulnerabilities, addressing CVEs, resolving secret leaks, hardening auth.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`security.md`](security.md) *(OWASP Top 10:2025, Agentic ASI01–ASI10, NIST 800-63B-4, PQC)*<br>2. [`pipelines/security-scanning-sast.md`](pipelines/security-scanning-sast.md) *(SAST, DAST, Secret scanners)*<br>3. [`agents/tdd-reproduction.md`](agents/tdd-reproduction.md) *(Reproduction before patching)* |
| **Key Invariant Rules** | **R-060** (Strict schema parsing at boundaries), **R-061** (SQL parameterization), **R-064** (Zero secrets in repo), **R-065** (Argon2id password hashing), **R-076** (Timing attack defense: constant-time comparison), **R-185** (HMAC-SHA256 webhook signature verification), **R-230** (NIST SP 800-63B-4 auth), **R-231** (Post-quantum crypto-agility), **R-232** (Fail-closed exceptional handling) |
| **Prohibited Actions** | ❌ Committing mock secrets, real keys, or certificates into git history.<br>❌ Using `crypto.timingSafeEqual` with unequal buffer lengths (causes crash).<br>❌ Disabling security linters or suppressing SAST warnings with comments. |
| **Mandatory Verification** | 1. Security Scan: `./scripts/ci-gate.sh`<br>2. Dependency Audit: `npm audit --audit-level=high` or `govulncheck ./...` or `pip-audit`<br>3. SAST Scan: Verify clean scan with Semgrep or Trivy. |

---

### Archetype 8: CI/CD Pipeline & Deployment Automation

*Writing or modifying GitHub Actions, GitLab CI, Dockerfiles, or deployment manifests.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`DEPLOYMENT.md`](DEPLOYMENT.md) *(Deployment & Release Strategy)*<br>2. [`pipelines/github-actions.md`](pipelines/github-actions.md) *(or `gitlab-ci.md`)*<br>3. [`sections/devops-infrastructure/docker-containers.md`](sections/devops-infrastructure/docker-containers.md) *(Rootless, Multi-stage, Distroless)*<br>4. [`pipelines/deployment-strategies.md`](pipelines/deployment-strategies.md) |
| **Key Invariant Rules** | **R-153** (Twelve-Factor App compliance), **R-154** (Non-root container user), **R-155** (Multi-stage minimal builds), **R-156** (Base image pinned by SHA-256 digest), **R-157** (Zero-downtime rolling/canary deployments), **R-160** (Explicit CPU & memory requests/limits) |
| **Prohibited Actions** | ❌ Running containers as `root` (UID 0).<br>❌ Using mutable image tags like `:latest` in production manifests.<br>❌ Storing environment credentials directly inside Dockerfile `ENV` or workflow YAML. |
| **Mandatory Verification** | 1. Container Build Test: `docker build --tag test:local .`<br>2. Container Security Scan: `trivy image test:local` (Zero CRITICAL vulnerabilities)<br>3. Rootless Check: `docker run --rm test:local id` (UID != 0) |

---

### Archetype 9: Architecture Evaluation & System Design

*Designing new subsystems, picking frameworks/databases, or planning modular monoliths.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/arena-evaluator.md`](agents/arena-evaluator.md) *(Multi-Solution Arena Scoring)*<br>2. [`decisions.md`](decisions.md) *(Architecture Decision Trees)*<br>3. [`ARCHITECTURE.md`](ARCHITECTURE.md) *(Domain-Driven Design, Hexagonal Boundaries)*<br>4. [`specs.md`](specs.md) |
| **Key Invariant Rules** | **R-027** (Single Responsibility Principle), **R-031** (Dependency Inversion Principle), **R-041** (Separation of Concerns / Clean Architecture), **R-187** (Full jitter backoff & circuit breakers), **R-198** (Adversarial debate & Arena scorecard before implementation) |
| **Prohibited Actions** | ❌ Selecting a technology based on novelty without computing a 5-pillar Arena scorecard.<br>❌ Creating circular dependencies between domain modules.<br>❌ Mixing persistence infrastructure directly into domain entity models. |
| **Mandatory Verification** | 1. Arena Scorecard Table generated and checked into `decisions.md`.<br>2. Architecture Diagram (ASCII or Mermaid) verifying unidirectional dependency flow. |

---

### Archetype 10: Refactoring & Code Quality Modernization

*Restructuring code, eliminating technical debt, cleaning up types, or removing anti-patterns.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Minimal diffs, zero commentary noise)*<br>2. [`RULES.md`](RULES.md) *(Universal Engineering Laws)*<br>3. Target Language Guide (e.g. [`languages/typescript.md`](languages/typescript.md))<br>4. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-001** (Zero deferred markers: TODO/FIXME), **R-034** (Zero `any` / `@ts-ignore`), **R-046** (No swallowed exceptions), **R-164** (Atomic commits), **R-182** (Minimal surgical diffs) |
| **Prohibited Actions** | ❌ Changing external public API signatures during internal refactors.<br>❌ Reformatting entire files unrelated to the refactored logic.<br>❌ Introducing any regressions in the test suite. |
| **Mandatory Verification** | 1. `git diff --stat` confirming small surgical scope.<br>2. Typecheck: `npx tsc --noEmit` or `mypy --strict .` (0 errors)<br>3. Regression Suite: Full test run passing with 100% green. |

---

### Archetype 11: Multi-Agent Orchestration & Workflow Automation

*Coordinating multi-agent swarms, dispatching parallel subagents, decomposing epics into DAGs, managing distributed Saga compensations, or orchestrating reconciler control loops.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/orchestrator.md`](agents/orchestrator.md) *(Topological DAGs, Fencing tokens, Saga rollback, Reconciler loop)*<br>2. [`agents.md`](agents.md) *(Persona boundaries, tool sandboxing, communication protocols)*<br>3. [`agents/arena-evaluator.md`](agents/arena-evaluator.md) *(Adversarial debate & arbiter scoring)*<br>4. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Surgical diffs & proof-of-work)*<br>5. [`RULES.md`](RULES.md) *(Section 14: R-191 to R-200)* |
| **Key Invariant Rules** | **R-191** (Orchestrator Role Isolation: orchestrator never directly implements), **R-192** (Pointer-based context handoffs, zero context tsunami), **R-193** (Martin Kleppmann fencing tokens on state writes), **R-194** (Saga compensating rollbacks on partial failure), **R-195** (Acyclic graph validation & $\le 3$ cycle ceiling), **R-196** (Unresponsive subagent & zombie reaping), **R-197** (Bounded worker concurrency $K \le 4$), **R-198** (Adversarial debate for high-stakes decisions), **R-199** (Reconciler desired-state convergence), **R-200** (Cryptographic HITL boundaries) |
| **Prohibited Actions** | ❌ Writing application source code directly inside the lead orchestrator context.<br>❌ Dumping raw multi-megabyte conversation transcripts into child agent prompts.<br>❌ Dispatching unbounded parallel workers without a semaphore pool ($K > 4$).<br>❌ Marking tasks complete without inspecting subagent terminal exit codes and assertion counts.<br>❌ Mutating distributed state without defining inverse Saga compensating rollbacks. |
| **Mandatory Verification** | 1. Graph Cycle Audit: Topological sort verification confirming acyclic DAG.<br>2. Fencing Token Assertion: Ensure epoch token is passed to all write operations.<br>3. Exit Code Verification: Inspect stdout/stderr of every child subagent (exit code 0).<br>4. Git Cleanliness: `git status -s` confirming 0 uncommitted or untracked changes. |
 
---
 
### Archetype 12: Enterprise ERP & Business Ledger Engineering
 
*Developing, customizing, or maintaining ERP systems (Odoo, ERPNext / Frappe), double-entry accounting ledgers, multi-currency transactions, FIFO inventory valuation, and supply chain automation.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/erp-enterprise/core-accounting-ledger.md`](sections/erp-enterprise/core-accounting-ledger.md) *(Ledger invariants, Debit=Credit, multi-currency, penny rounding)*<br>2. [`sections/erp-enterprise/inventory-supply-chain.md`](sections/erp-enterprise/inventory-supply-chain.md) *(FIFO cost layers, perpetual COGS, landed costs)*<br>3. Target ERP Framework: [`frameworks/erp/odoo.md`](frameworks/erp/odoo.md) *(Odoo 17/18 ORM, compute fields, access rules)* OR [`frameworks/erp/erpnext.md`](frameworks/erp/erpnext.md) *(Frappe v15/v16 DocType lifecycle, SLE, hooks)*<br>4. [`RULES.md`](RULES.md) *(Financial data invariants & idempotency)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-001** (Zero deferred markers: TODO/FIXME), **R-002** (No mock/synthetic data in production), **R-075** (Multi-tenant / multi-company record rule isolation), **R-220** (Exact fixed-point Decimal arithmetic; IEEE-754 floats strictly prohibited for currency), **R-221** ($\sum \text{Debit} \equiv \sum \text{Credit}$ general ledger invariant), **R-222** (Append-only immutable posted journal entries), **R-223** (Perpetual inventory FIFO cost layer queue invariant) |
| **Prohibited Actions** | ❌ Using IEEE-754 floating point numbers (`float`) for monetary amounts or tax calculations.<br>❌ Executing direct SQL `UPDATE` or `DELETE` on posted journal entries (`account.move` / `GL Entry`) bypassing ORM cancel/reversal workflows.<br>❌ Allowing negative inventory quantities without explicit negative-stock policy configuration.<br>❌ Mutating submittable Frappe documents after submission (`docstatus == 1`) without amend workflow.<br>❌ Omitting record-level security rules (`ir.rule` / Permission Query conditions) in multi-company setups. |
| **Mandatory Verification** | 1. Ledger Balance Assertion: Verify $\sum \text{debits} - \sum \text{credits} = 0$ on all posted entries.<br>2. Decimal Precision Check: Verify all monetary values use `Decimal` with quantized precision.<br>3. Unit & Integration Suite: `python -m pytest tests/` or `bench run-tests --app <app>` / `odoo-bin -i <module> --test-enable` (100% pass).<br>4. Security / Access Audit: Verify unprivileged users cannot read or mutate cross-company journals. |
 
---
 
### Archetype 13: Systems Programming, Linux Kernel & AOSP Customization
 
*Developing Linux kernel modules, character/platform device drivers, eBPF tracepoints, Android AOSP HALs, Treble AIDL services, SELinux policies, or modern C23/C++23 systems software.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. Target Subsystem: [`sections/systems-kernel/linux-kernel-driver.md`](sections/systems-kernel/linux-kernel-driver.md) *(Linux 6.6+ drivers, Device Tree, atomic contexts, eBPF)* OR [`frameworks/mobile/android-aosp.md`](frameworks/mobile/android-aosp.md) *(Android 14/15/16 Treble, AIDL HAL, Soong, SELinux)*<br>2. [`languages/c-cpp.md`](languages/c-cpp.md) *(Modern ISO C23/C++23, RAII lifetimes, concurrency, sanitizers)*<br>3. [`RULES.md`](RULES.md) *(Section 17: R-224 to R-227)*<br>4. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-001** (Zero deferred markers: TODO/FIXME), **R-002** (Zero mock placeholders), **R-224** (RAII & bounded systems memory safety), **R-225** (Atomic context no-sleep invariant inside spinlocks/ISRs), **R-226** (Kernel-user boundary `copy_from_user`/`copy_to_user` verification), **R-227** (AOSP Treble `@VintfStability` & SELinux `neverallow` compliance) |
| **Prohibited Actions** | ❌ Dereferencing user-space pointers directly in kernel space without `copy_from_user` / `copy_to_user`.<br>❌ Calling sleeping functions (`msleep`, `mutex_lock`, `kmalloc(..., GFP_KERNEL)`) while holding spinlocks or in atomic/interrupt context.<br>❌ Bypassing Android Treble Stable AIDL boundaries using raw, unstabilized binder interfaces across `/system` and `/vendor`.<br>❌ Modifying AOSP SELinux policies by adding permissive domains or violating upstream `neverallow` assertions.<br>❌ Using unconstrained C-style casts or manual memory allocation (`malloc`/`free`) where RAII smart pointers or C23 bounds are available. |
| **Mandatory Verification** | 1. Compilation Cleanliness: Kernel module builds with zero warnings (`-Wall -Werror`); AOSP modules compile cleanly with `m <module_name>`.<br>2. Sanitizer / Dynamic Checks: Clang AddressSanitizer / UndefinedBehaviorSanitizer (`-fsanitize=address,undefined`) clean run.<br>3. SELinux Policy Validation: `checkpolicy` / `secilc` compiles sepolicy with zero `neverallow` failures.<br>4. Driver Lifecycle Test: Verification of `insmod` / `rmmod` clean unload with zero kernel memory leaks or dangling sysfs nodes. |
 
---
 
### Archetype 14: Autonomous PR Delivery & Full-Send Shipping
 
*Executing end-to-end hands-free PR delivery (`full-send` or `full-stop`), verifying direct session proof, filing problem-first PRs, babysitting CI and review bots, and automating merge gate evaluation.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/full-send-delivery.md`](agents/full-send-delivery.md) *(7-step delivery loop, 5-point merge gate, full-stop handoffs)*<br>2. [`workflows/pr-lifecycle-babysitting.md`](workflows/pr-lifecycle-babysitting.md) *(Event-driven watchers, rate limit partitioning, bot triage)*<br>3. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Surgical diffs, observable CLI proof)*<br>4. [`RULES.md`](RULES.md) *(Rules R-201, R-202, R-205, R-209)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-201** (5-point Merge Gate verification on latest head), **R-202** (Direct observable proof over mocked tests), **R-205** (Event-driven PR watchers; zero tight polling loops), **R-206** (REST quota fallback when GraphQL rates expire), **R-209** (Problem-first PR descriptions; zero implementation inventories) |
| **Prohibited Actions** | ❌ Ending turn while CI checks, review bots, or merge queues are pending.<br>❌ Running tight `while sleep; do ...` polling loops that exhaust GitHub rate limits.<br>❌ Merging through branch protection using administrative bypasses (`gh pr merge --admin`).<br>❌ Filing PRs that lead with file-by-file inventories instead of problem statements.<br>❌ Merging when the PR branch is BEHIND or DIRTY without rebasing first. |
| **Mandatory Verification** | 1. Direct Proof Assertion: Exit code 0 on reproduction test + real runtime check.<br>2. Merge Gate Evaluation: 100% checks green, bot findings triaged, 0 human blockers.<br>3. Base Synchronization: `git fetch origin && git status -uno` confirms 0 commits behind `main`.<br>4. Remote Status: Verify GitHub reports PR as `MERGED` (full-send) or `OPEN/READY` (full-stop). |
 
---
 
### Archetype 15: Multi-Model Consensus, Tri-Provider Council & Adversarial Review
 
*Convening cross-provider frontier model councils (`council`) or deep iterative review loops (`sol-loop`), enforcing finding severity taxonomies, and defending against review-induced scope creep.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/multi-model-council.md`](agents/multi-model-council.md) *(Tri-model selection, 3-round budget ceiling, findings ledger)*<br>2. [`agents/arena-evaluator.md`](agents/arena-evaluator.md) *(Adversarial debate & arbiter scoring)*<br>3. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Surgical diffs, minimal intervention)*<br>4. [`RULES.md`](RULES.md) *(Rules R-198, R-203, R-204)*<br>5. Target language and framework guides |
| **Key Invariant Rules** | **R-198** (Adversarial debate for high-stakes modifications), **R-203** (Three frontier models from distinct independent providers), **R-204** (Review scope-creep defense; triage into blocker/should/nit), **R-182** (Minimal surgical diffs), **R-195** (Hard ceiling of $\le 3$ rounds; 5 for security/auth/concurrency) |
| **Prohibited Actions** | ❌ Appeasing reviewers by adding speculative helpers, extra adapters, or unneeded guards.<br>❌ Looping past 3 rounds (or 5 for auth/security) without escalating disputes to human decision.<br>❌ Fabricating numerical ratings or scores when delegates provided only qualitative feedback.<br>❌ Allowing reviewer subagents to mutate files directly or spawn nested child agents.<br>❌ Duplicating models from the same provider when three distinct providers were requested. |
| **Mandatory Verification** | 1. Provider Diversity Audit: Confirm 3 distinct AI provider models participated.<br>2. Budget Check: Verify round count $\le 3$ (or $\le 5$ for auth/data-loss/concurrency).<br>3. Scope-Creep Diff Check: `git diff --stat` confirms diff did not inflate by $>20\%$.<br>4. Ledger Reconciliation: 100% of blockers/shoulds resolved or declined with written evidence. |
 
---
 
### Archetype 16: Performance Hillclimbing & Scientific Optimization
 
*Sustained empirical optimization of latency, throughput, or resource consumption against a target, vetting benchmarks via the 7-Question Audit, freezing measurement harnesses, and maintaining decision ledgers.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/hillclimbing-optimization.md`](agents/hillclimbing-optimization.md) *(7-question audit, frozen harness, decision.tsv ledger)*<br>2. [`sections/frontend/web-performance.md`](sections/frontend/web-performance.md) OR target subsystem guide<br>3. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Surgical diffs, minimal intervention)*<br>4. [`RULES.md`](RULES.md) *(Rules R-202, R-212)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-212** (7-Question Benchmark Audit: limiter named, production tuning matched, Amdahl's law verified, $\ge 5$ alternating A/B runs), **R-164** (Atomic commits: 1 commit per accepted hypothesis), **R-202** (Direct proof over synthetic simulation), **R-015** (Surgical diffs: stage only touched files with `git add <file>`) |
| **Prohibited Actions** | ❌ Stacking multiple untested speculative optimizations into a single commit.<br>❌ Comparing untuned configurations or debug builds against optimized release builds.<br>❌ Claiming a performance win from code inspection without executing the frozen benchmark harness.<br>❌ Keeping optimizations that fail to exceed the statistical noise threshold of the benchmark.<br>❌ Discarding or ignoring regressions in the primary test gate. |
| **Mandatory Verification** | 1. 7-Question Benchmark Audit: All 7 questions answered with empirical data.<br>2. Baseline Comparison: Median of $\ge 5$ alternating A/B runs showing statistically significant gain.<br>3. Regression Gate: Full test suite passing with 0 errors.<br>4. Decision Ledger Audit: `decision.tsv` contains complete chronological trail of kept/reverted attempts. |
 
---
 
### Archetype 17: Blast-Radius Analysis & Cross-Boundary Verification
 
*Analyzing systemic impact of risky or cross-cutting changes, discovering hidden failure modes beyond symbol grep (wire formats, serialization schemas, DB columns, microtask lifecycles), and proving single safety facts.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/blast-radius-verification.md`](agents/blast-radius-verification.md) *(5-level certainty scale, single-fact safety proof, dark blast radius)*<br>2. [`workflows/unslop-code-hygiene.md`](workflows/unslop-code-hygiene.md) *(Structural encoding of invariants over comments)*<br>3. Target architecture guide (e.g. [`sections/backend/api-design.md`](sections/backend/api-design.md) or [`sections/database/schema-migrations.md`](sections/database/schema-migrations.md))<br>4. [`RULES.md`](RULES.md) *(Rules R-211, R-213, R-214)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-211** (Single safety fact proof at Certainty Level $\ge 4$ via executable test), **R-213** (Encode constraints into types/schemas rather than comment warnings), **R-003** (Zero unverified assumptions), **R-018** (Backward compatibility of public/wire interfaces) |
| **Prohibited Actions** | ❌ Relying solely on raw symbol grep to claim a change is safe.<br>❌ Presenting convincing written blast-radius descriptions without executing standalone proof probes.<br>❌ Modifying wire-format serialization fields or database column types without checking external consumers.<br>❌ Adding defensive comments (`// do not remove`) instead of structural compiler/schema constraints. |
| **Mandatory Verification** | 1. Single-Fact Executable Probe: Standalone probe script exits with code 0 proving safety invariant.<br>2. Certainty Scale Assertion: Evidence reaches Level 4 (executed test) or Level 5 (live repro).<br>3. Wire & DB Contract Check: Validation of backward compatibility across serialization boundaries.<br>4. Clean Unslop Pass: 0 forbidden commentary sermons or workaround justifications in diff. |
 
---
 
### Archetype 18: The Ralph Reconciler Loop (Default Non-Stop Execution)
 
*Autonomous, non-stop closed-loop execution. Running continuously against a disk-backed task backlog until all tasks pass verification gates with Exit Code 0 and all changes are committed.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/ralph-reconciler-loop.md`](agents/ralph-reconciler-loop.md) *(Ralph Wiggum loop, fresh-context iteration, disk memory)*<br>2. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Minimal diffs, prove-it-works evidence)*<br>3. [`agents/tdd-reproduction.md`](agents/tdd-reproduction.md) *(Reproduction-first defect isolation)*<br>4. [`RULES.md`](RULES.md) *(Rules R-001, R-004, R-181, R-201, R-215)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-215** (Non-stop closed-loop execution until Exit Code 0 across all gates), **R-004** (Anti-Fake Green: never commit without passing tests), **R-164** (Atomic commits: 1 commit per completed checklist item), **R-001** (Zero TODOs/placeholders), **R-182** (Surgical minimal diffs) |
| **Prohibited Actions** | ❌ Stopping mid-task or asking the user to run tests when shell tools are available.<br>❌ Marking a task `[x]` in the backlog before running tests and observing Exit Code 0.<br>❌ Yielding execution with conversational excuses ("It should work now", "Try this").<br>❌ Leaving broken or dirty uncommitted changes across iteration cycles.<br>❌ Emitting unfinished stub functions or mock fallbacks. |
| **Mandatory Verification** | 1. Backlog Verification: 100% of tasks in `IMPLEMENTATION_PLAN.md` marked `[x]`.<br>2. Clean Git State: `git status --porcelain` is empty (all progress committed).<br>3. Quality Gate Scan: Strict typecheck (0 errors) + Linter (0 warnings) + Tests (100% pass).<br>4. Completion Sentinel: Terminal output concludes with `<promise>COMPLETE</promise>` and verbatim `prove-it-works` scorecard. |
 
---
 
### Archetype 19: Adversarial Single-Model Review Loop (Sol Loop)
 
*Tight, iterative code hardening using a single flagship reasoning model (OpenAI Sol/o1/o3-mini, Claude Opus, or Gemini Pro) across a strict 3-to-5 round budget with an immutable finding ledger.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/sol-loop.md`](agents/sol-loop.md) *(Adversarial review loop, budget cap, finding ledger)*<br>2. [`agents/poteto-discipline.md`](agents/poteto-discipline.md) *(Surgical diffs, anti-slop)*<br>3. [`RULES.md`](RULES.md) *(Rules R-204, R-216)*<br>4. Target domain or framework guide<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-216** (Max 3 rounds, extendable to 5 only for auth/data-loss/concurrency; immutable ledger; dedicated test per blocker), **R-204** (Scope-creep defense: reject speculative guards), **R-015** (Surgical diffs: stage only touched files) |
| **Prohibited Actions** | ❌ Exceeding round budgets without authorization.<br>❌ Blindly implementing speculative edge-case guards requested by the reviewer.<br>❌ Re-sending the entire repository on rounds 2 and 3 instead of delta diffs.<br>❌ Agreeing with reviewer hallucinations just to receive an `APPROVE` verdict.<br>❌ Allowing the review loop to expand the total diff size significantly. |
| **Mandatory Verification** | 1. Ledger Verification: All findings tracked with stable IDs and explicit outcomes (`fixed:`, `disagree:`, `declined:`).<br>2. Reproduction Proof: Failing-then-passing test added for every accepted blocker.<br>3. Diff Delta Check: `git diff --shortstat` verifies surgical containment.<br>4. PR Description Trailer: Verbatim note `Reviewed with sol-loop: <N> rounds with <model>. Sol verdict: approved`. |
 
---
 
### Archetype 20: Formal Verification & State Machine Model Checking
 
*Formally verifying mission-critical distributed systems, concurrent protocols, financial ledgers, and complex state machines over bounded state spaces using TLA+ and TLC, extracting shortest-path counterexamples and Mermaid statecharts.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/formal-verification-statecharts.md`](agents/formal-verification-statecharts.md) *(TLA+ spec, TLC runner, Mermaid statecharts)*<br>2. [`agents/tdd-reproduction.md`](agents/tdd-reproduction.md) *(Replaying counterexamples as unit tests)*<br>3. [`RULES.md`](RULES.md) *(Rules R-003, R-188, R-217)*<br>4. Target language or concurrency guide (e.g. [`languages/golang.md`](languages/golang.md) or [`languages/rust.md`](languages/rust.md))<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-217** (Mathematical verification over bounded state space; shortest-path counterexample extraction; replayable code test), **R-003** (Zero unverified assumptions), **R-188** (Goroutine and async lifecycle bounding) |
| **Prohibited Actions** | ❌ Weakening an invariant when TLC surfaces a counterexample trace.<br>❌ Declaring a model verified without first proving that mutating the invariant causes TLC to fail.<br>❌ Using unbounded integer ranges or sets that cause TLC memory exhaustion.<br>❌ Disconnecting TLA+ variable names from actual source code symbol identifiers. |
| **Mandatory Verification** | 1. Falsification Verification: Invariant proven capable of failing on a broken variant.<br>2. TLC Clean Pass: Model checker evaluates $\ge 10$ distinct states with 0 errors.<br>3. Replayable Test: Extracted counterexample trace verified as a real test in codebase.<br>4. Mermaid Statechart: Clean state diagram generated and rendered. |
 
---
 
### Archetype 21: PR Modernization, Triage & Contributor Takeover
 
*Auditing, rebasing, and taking over stale branches or existing PRs; establishing a formal disposition (MODERNIZE, REWORK, or CLOSE); preserving human contributor credit and verifying intent via git range-diff.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`workflows/pr-modernize-takeover.md`](workflows/pr-modernize-takeover.md) *(Tri-disposition, range-diff, author attribution)*<br>2. [`workflows/pr-lifecycle-babysitting.md`](workflows/pr-lifecycle-babysitting.md) *(PR babysitting, bot triage)*<br>3. [`RULES.md`](RULES.md) *(Rules R-207, R-208, R-218)*<br>4. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-218** (Mandatory disposition selection: `MODERNIZE`, `REWORK`, or `CLOSE`; `git range-diff` validation), **R-208** (Preserve original Git author and `Co-authored-by:` trailers), **R-207** (Push exclusively with `--force-with-lease` tied to pre-rebase head SHA) |
| **Prohibited Actions** | ❌ Mechanically rebasing a stale branch without checking what landed on `main` since divergence.<br>❌ Replacing human author identities with AI agent model names in Git commits.<br>❌ Using unqualified `git push --force` that overwrites upstream progress.<br>❌ Closing another contributor's PR without human authorization and documented evidence.<br>❌ Re-introducing deleted or superseded code through careless merge conflict resolution. |
| **Mandatory Verification** | 1. Disposition Justification: Documented rationale for `MODERNIZE`, `REWORK`, or `CLOSE`.<br>2. Authorship Audit: `git log -1` verifies original contributor identity and co-author trailers.<br>3. Range-Diff Check: `git range-diff` confirms commit series integrity.<br>4. Leased Push: Successful push with `--force-with-lease` matching recorded pre-rebase SHA. |
 
---
 
### Archetype 22: Dynamic Model Discovery & Multi-Provider Workload Orchestration
 
*Discovering runtime model capabilities, profiling empirical strengths, routing DAG subtasks to optimal models (Deep Reasoning, Architectural, High-Context, Fast Runner), and ensuring transparent Git commit attribution.*
 
| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/model-capability-orchestration.md`](agents/model-capability-orchestration.md) *(Model discovery, capability matrix, task routing)*<br>2. [`agents/orchestrator.md`](agents/orchestrator.md) *(Multi-agent DAGs, fencing leases)*<br>3. [`agents/multi-model-council.md`](agents/multi-model-council.md) *(Tri-provider council)*<br>4. [`RULES.md`](RULES.md) *(Rules R-203, R-208, R-219)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-219** (Mandatory pre-flight discovery via `orchestrator_capabilities` or provider API; workload-strength matching; model commit disclosure), **R-208** (Preserve human author identity), **R-173** (Workspace directory sandboxing), **R-228** (OWASP Agentic AI least agency) |
| **Prohibited Actions** | ❌ Hardcoding model IDs without querying live orchestrator capabilities.<br>❌ Attempting to delegate tasks to disabled or constrained provider instances.<br>❌ Assigning high-reasoning models to mechanical styling edits, or low-tier models to formal concurrency proofs.<br>❌ Erasing human contributor identities in favor of AI model names in Git history. |
| **Mandatory Verification** | 1. Discovery Verification: Pre-flight capability scan successfully evaluated active providers.<br>2. Strength Alignment: Concurrency/security tasks routed to Reasoning tier; refactors to Architectural tier; tests to High-Throughput tier.<br>3. Clean Execution: All subagent delegate tasks completed with Exit Code 0.<br>4. Commit Attribution: Git commit message contains verified model and human co-authorship trailers. |
 
---

### Archetype 23: MCP Server, A2A Agent Interoperability & Agentic AI Systems

*Building Model Context Protocol (MCP) tool servers, Agent2Agent (A2A) peer services, LLM gateways, RAG pipelines, or hardening autonomous agentic workflows against OWASP ASI01–ASI10 & AST10.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/mcp-a2a-protocols.md`](agents/mcp-a2a-protocols.md) *(MCP 2026 Stateless Streamable HTTP, OAuth 2.1 + RFC 8707, A2A Agent Cards)*<br>2. [`sections/ai-ml/llm-integration.md`](sections/ai-ml/llm-integration.md) *(LLM Gateway, structured outputs, evals, OTel GenAI telemetry)*<br>3. [`security.md`](security.md) *(Section 3: OWASP Agentic ASI01–ASI10 & AST10)*<br>4. [`RULES.md`](RULES.md) *(Section 18: R-228, R-229, R-232, R-233, R-234, R-235)*<br>5. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-060** (Strict tool argument schema validation), **R-078** (Prompt injection defense & untrusted output quarantine), **R-151** (OpenTelemetry GenAI semantic conventions), **R-228** (OWASP Agentic least agency & tool sandboxing), **R-229** (Stateless MCP Streamable HTTP & OAuth 2.1 RFC 8707 audience scoping), **R-232** (Fail-closed exception handling), **R-235** (MCP & model supply chain provenance) |
| **Prohibited Actions** | ❌ Exposing generic raw-SQL or arbitrary shell execution tools over remote MCP endpoints.<br>❌ Passing through ambient broad user JWTs without RFC 8707 `resource`/`aud` validation.<br>❌ Pinning MCP servers to stateful in-memory local sessions behind multi-replica load balancers.<br>❌ Concatenating untrusted RAG/tool output raw into privileged system instructions.<br>❌ Allowing unbounded A2A agent recursion without hop limits or cost/time ceilings. |
| **Mandatory Verification** | 1. AuthZ Contract Test: Token with mismatched `aud` or missing scope rejected fail-closed (`401`/`403`).<br>2. Schema Fuzzing: Malformed/extra tool parameters rejected by strict Zod/Pydantic schemas.<br>3. Stateless Replay Test: Identical MCP requests succeed across independent stateless worker instances.<br>4. Telemetry Audit: Verify OTel `gen_ai.*` spans emitted with scrubbed secrets and propagated `traceparent`. |

---

### Archetype 24: Pre-Code Discovery, Codebase Forensics & Architecture Review (`/how`, `/why`, `/interrogate`, `/architect`)

*Investigating unfamiliar subsystems, tracing execution paths, verifying Chesterton's Fence via git archaeology, grilling ambiguous product specs, and locking down module boundaries before writing code.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/code-forensics-interrogation.md`](agents/code-forensics-interrogation.md) *(`/how`, `/why`, `/interrogate`, `/architect`, `file-pr`, failed-theory cleanup)*<br>2. [`agents/unified-agent-stacks.md`](agents/unified-agent-stacks.md) *(`gstack` scope modes, `superpowers` two-stage review, `compound-engineering` loop)*<br>3. [`sections/architecture-foundations/software-design-craft.md`](sections/architecture-foundations/software-design-craft.md) *(Ousterhout deep modules, Beck Tidy First, Hyrum's Law)*<br>4. [`decisions.md`](decisions.md) *(Trade-off matrices)* |
| **Key Invariant Rules** | **R-003** (Zero unverified assumptions), **R-236** (Deep modules over shallow wrappers), **R-245** (Chesterton's Fence git archaeology before deletion), **R-248** (Two-stage review: spec compliance before code quality), **R-249** (Explicit scope mode & problem-first PR narrative), **R-250** (Compound lessons into repo memory) |
| **Prohibited Actions** | ❌ Editing source files during read-only `/how` or `/why` forensics.<br>❌ Deleting guards, locks, or shims without checking `git log -S` / `git blame -w -C -C`.<br>❌ Writing implementation bodies before settling types, boundaries, and explicit scope mode.<br>❌ Submitting PRs that list raw modified files instead of explaining the problem and CLI proof. |
| **Mandatory Verification** | 1. Trace Brief: Exact file paths + line numbers mapped from ingress to storage sink.<br>2. Archaeology Proof: Relevant commit SHAs cited when altering/removing legacy guards.<br>3. Scope & Spec Sign-off: Explicit scope mode declared and 6 forcing questions answered.<br>4. Clean Tree: `git status --short` confirms zero edits during read-only discovery phase. |

---

### Archetype 25: Legacy System Modernization, Safe Refactoring & Architectural Fitness

*Modernizing untested legacy codebases, separating structural tidying from behavioral changes, replacing brittle mocks with characterization tests, migrating via Strangler Fig / Branch by Abstraction, and adding CI fitness functions.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/architecture-foundations/software-design-craft.md`](sections/architecture-foundations/software-design-craft.md) *(Feathers characterization tests & seams, Beck Tidy First, Fowler Strangler Fig & Mikado Method)*<br>2. [`sections/architecture-foundations/evolutionary-delivery-architecture.md`](sections/architecture-foundations/evolutionary-delivery-architecture.md) *(Automated architectural fitness functions, connascence, DORA)*<br>3. [`agents/blast-radius-verification.md`](agents/blast-radius-verification.md) *(Caller & contract blast-radius check)*<br>4. [`agents/code-forensics-interrogation.md`](agents/code-forensics-interrogation.md) *(Chesterton's Fence & failed-theory cleanup)* |
| **Key Invariant Rules** | **R-015** (Surgical diff discipline), **R-236** (Deep modules), **R-237** (Separate structural tidying commits from behavioral commits), **R-239** (Characterization tests before legacy edits), **R-240** (Test public behavior, not internal mocks), **R-244** (Automated architectural fitness functions), **R-246** (Failed-theory diff cleanup), **R-247** (Git worktree isolation) |
| **Prohibited Actions** | ❌ Mixing structural refactoring and behavioral bug fixes in the same commit.<br>❌ Editing untested legacy functions without first writing passing characterization tests.<br>❌ Attempting a big-bang rewrite instead of Strangler Fig or Branch by Abstraction.<br>❌ Writing brittle change-detector tests tightly coupled to private method call order. |
| **Mandatory Verification** | 1. Characterization Baseline: New characterization tests pass on unmodified legacy code (Exit Code 0).<br>2. Commit Separation: `git log --stat` confirms structural tidying commit(s) separated from behavioral commit(s).<br>3. Fitness Gate: Layer/boundary/API compatibility fitness check passes in CI.<br>4. Full Regression: Complete test suite green with zero weakened assertions (`R-011`). |

---

### Archetype 26: Kubernetes Cluster Forensics, Auditing & SRE Operations (`kstack`)

*Diagnosing live Kubernetes outages, CrashLoopBackOff/OOMKilled pods, RBAC/Pod Security posture, NetworkPolicies, resource right-sizing/FinOps cost audits, deprecated API scans, and distributed reliability reviews.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`sections/devops-infrastructure/kstack-cluster-operations.md`](sections/devops-infrastructure/kstack-cluster-operations.md) *(Read-only `/cluster-status`, `/investigate`, 4-pillar audits, zero-leak `/cleanup`)*<br>2. [`sections/architecture-foundations/distributed-systems-reliability.md`](sections/architecture-foundations/distributed-systems-reliability.md) *(Bulkheads, load shedding, retry budgets, SLI/SLO error budgets, Transactional Outbox)*<br>3. [`sections/devops-infrastructure/kubernetes-cloud.md`](sections/devops-infrastructure/kubernetes-cloud.md) *(K8s manifests, PDBs, HPA, securityContext)*<br>4. [`workflows/incident-response.md`](workflows/incident-response.md) *(SEV triage & blameless postmortems)* |
| **Key Invariant Rules** | **R-153**–**R-162** (Deployment & infrastructure resilience), **R-200** (Human confirmation for mutating/destructive prod actions), **R-232** (Fail-closed defaults), **R-241** (Transactional Outbox / zero dual-writes), **R-242** (Bulkheads, load shedding & retry budgets), **R-243** (SLI/SLO error budgets & burn-rate alerts) |
| **Prohibited Actions** | ❌ Running `kubectl` without first verifying `kubectl config current-context`.<br>❌ Deleting crashing pods before capturing `describe`, Warning `events`, and `--previous` logs.<br>❌ Leaving ephemeral debug pods/jobs running after troubleshooting (must run `/cleanup`).<br>❌ Running mutating cluster patches or `--profile=sysadmin` shells without operator confirmation (`R-200`). |
| **Mandatory Verification** | 1. Context Confirmation: `kubectl config current-context` recorded in forensic log.<br>2. Correlated Evidence: Pod conditions, Warning events, `--previous` logs, metrics, and rollout history correlated.<br>3. Audit Report: Security (RBAC/PSS), NetworkPolicies, Resource requests/limits, and Pluto/Trivy findings documented.<br>4. Zero-Leak Check: `kubectl get all -A -l app.kubernetes.io/managed-by=devskill-debug` returns empty. |

---

### Archetype 27: Universal Frontend Design Systems, Multi-Framework Web UI & Styling

*Designing or building production web UIs, design systems, and token architectures across React 19.2 / Next.js 16, Vue 3.5 / Nuxt 4, Svelte 5 / SvelteKit 2, Angular 19/20 Zoneless, Astro 5 Server Islands, SolidJS / SolidStart, and Tailwind CSS v4.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`FRONTEND.md`](FRONTEND.md) *(Universal Frontend Constitution & Framework Selection Matrix)*<br>2. [`sections/frontend/design-systems-ui-craft.md`](sections/frontend/design-systems-ui-craft.md) *(OKLCH Tokens, Modern CSS `@layer`/`@container`/Popover/View Transitions, Headless Primitives, Anti-Slop Rubric)*<br>3. Target Framework Guide in [`frameworks/frontend/`](frameworks/frontend/) (`react.md`, `nextjs.md`, `vue-nuxt.md`, `sveltekit.md`, `angular.md`, `astro.md`, `solidjs.md`, `tailwindcss.md`)<br>4. [`sections/frontend/accessibility.md`](sections/frontend/accessibility.md) & [`sections/frontend/web-performance.md`](sections/frontend/web-performance.md) |
| **Key Invariant Rules** | **R-129**–**R-141** (Frontend, a11y & Core Web Vitals), **R-251** (Semantic design tokens & zero-slop UI craft), **R-252** (Web platform first & zero-JS default), **R-253** (Framework-native reactivity & zero SSR request leaks), **R-259** (Tailwind CSS v4 CSS-first tokenization), **R-260** (Frontend security hardening) |
| **Prohibited Actions** | ❌ Hardcoding hex colors, magic pixels, or dynamic Tailwind template strings (`bg-${color}-500`).<br>❌ Storing session JWTs/tokens in `localStorage` or duplicating remote server data into client stores.<br>❌ Declaring mutable module-scoped user/request singletons on SSR servers.<br>❌ Shipping unverified UIs with missing focus rings, `axe-core` WCAG 2.2 AA violations, or horizontal overflow. |
| **Mandatory Verification** | 1. Type & Lint: Strict framework checker (`tsc --noEmit` / `svelte-check` / `astro check` / `ng build`) exits `0`.<br>2. Accessibility & E2E: Playwright + `axe-core` verifies 0 WCAG 2.2 AA violations and 0 console/network errors.<br>3. Performance Budget: Lighthouse Performance ≥ 90, LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1.<br>4. Responsive Check: Visual layout verified at 320px, 768px, and 1280px with dark mode & reduced motion. |

---

### Archetype 28: Cross-Platform & Native Mobile Engineering (Flutter, React Native/Expo, Android Kotlin/Compose, iOS SwiftUI)

*Building production mobile applications using Flutter 3.35+ (Impeller/Riverpod 3), React Native 0.79–0.81+ New Architecture / Expo SDK 53–54+, Native Android (Kotlin 2.x + Jetpack Compose), or Native iOS (Swift 6 + SwiftUI).*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. Target Mobile Guide: [`frameworks/mobile/flutter.md`](frameworks/mobile/flutter.md), [`frameworks/mobile/react-native-expo.md`](frameworks/mobile/react-native-expo.md), [`frameworks/mobile/android-kotlin-compose.md`](frameworks/mobile/android-kotlin-compose.md), or [`frameworks/mobile/ios-swiftui.md`](frameworks/mobile/ios-swiftui.md)<br>2. [`security.md`](security.md) *(Mobile secret storage, TLS pinning, OAuth PKCE)*<br>3. [`RULES.md`](RULES.md) *(Section 20: R-256, R-257, R-258; R-064 Zero Hardcoded Secrets)*<br>4. [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) |
| **Key Invariant Rules** | **R-064** (Zero hardcoded keys; Keychain/KeyStore only), **R-256** (Flutter Impeller, Riverpod 3 `Ref.mounted` & `Isolate.run`), **R-257** (React Native New Architecture, Reanimated UI-thread & FlashList), **R-258** (Swift 6 `@MainActor`/Sendable & Kotlin `collectAsStateWithLifecycle`) |
| **Prohibited Actions** | ❌ Storing auth tokens or database encryption keys in `SharedPreferences`, `UserDefaults`, or `AsyncStorage`.<br>❌ Blocking the UI thread with heavy JSON parsing, image processing, or JS-thread animations.<br>❌ Using unbounded `ScrollView`/`Column` for large lists or ignoring async lifecycle cancellation (`Ref.mounted`, `.task`, `collectAsStateWithLifecycle`).<br>❌ Shipping release binaries without obfuscation/R8/symbol uploads or running `expo-doctor` / `flutter analyze`. |
| **Mandatory Verification** | 1. Static Gate: `flutter analyze` / `npx expo-doctor && tsc --noEmit` / `./gradlew lint` / `xcodebuild` Swift 6 clean (Exit `0`).<br>2. Automated Tests: Unit + Widget/Component + Golden/Snapshot + E2E (Maestro / Integration / XCUITest) pass.<br>3. Frame & Startup Profile: 60/120fps verified in release/profile build with zero frame drops > 16ms.<br>4. Security Audit: Confirm zero plaintext credentials on device storage and valid Universal/App Links. |

---

### Archetype 29: Complex Multi-Requirement Delivery, Long-Horizon Execution & Context Engineering

*Executing complex, detail-dense, or multi-session tasks (≥ 4 requirements, cross-cutting constraints, strict negative rules) without silent requirement omission, Context Rot, checklist tampering, or premature happy-path completion.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/zero-missed-requirements.md`](agents/zero-missed-requirements.md) *(6-Layer Anti-Omission Architecture, frozen JSON ledger, SatisFix deviation check, attention recitation, context hygiene)*<br>2. [`agents/unified-agent-stacks.md`](agents/unified-agent-stacks.md) *(Two-stage review, worktree isolation, compound engineering)*<br>3. [`MISTAKES.md`](MISTAKES.md) *(Failure modes #31–#36: Silent Omission, Premature Victory, Checklist Tampering, Specification Satisficing)*<br>4. [`RULES.md`](RULES.md) *(Section 21: R-261 to R-266; R-248 Two-Stage Review)*<br>5. Target domain/framework guide for the implementation slice |
| **Key Invariant Rules** | **R-248** (Two-stage review: spec compliance before code quality), **R-261** (Frozen atomic JSON requirement ledger with SHA-256 `spec_hash`), **R-262** (Single-slice incremental execution), **R-263** (Attention recitation & Context Rot hygiene), **R-264** (Proof-bound Default-FAIL completion gate), **R-265** (Fresh-context read-only evaluator audit), **R-266** (Objective-aligned deviation elicitation against specification satisficing) |
| **Prohibited Actions** | ❌ Holding ≥ 4 requirements solely in chat prose or mutable Markdown checkboxes.<br>❌ Editing, weakening, or deleting frozen requirements without `--amend --reason`.<br>❌ Flipping `passes: true` without concrete command, `exit_code == 0`, and non-empty observed evidence.<br>❌ Flooding context with > 150-line raw logs or loading > 5 unrelated DevSkill guides.<br>❌ Declaring completion while `req-ledger.py gate --require-frozen` exits non-zero. |
| **Mandatory Verification** | 1. Frozen Spec Contract: `python3 scripts/req-ledger.py status .devskill/requirements.json --json` shows `frozen: true` and `integrity_errors: []`.<br>2. Milestone Recitation: `python3 scripts/req-ledger.py recite .devskill/requirements.json` confirms all `negative` constraints respected.<br>3. SatisFix & Fresh-Context Audit: Run `python3 scripts/req-ledger.py audit-prompt .devskill/requirements.json` and verify every `REQ-001..REQ-NNN` against `git diff` and execution logs.<br>4. Mechanical Gate: `python3 scripts/req-ledger.py gate .devskill/requirements.json --require-frozen` exits `0`. |

---

### Archetype 30: Production Agentic Harness Engineering, Zero-Trust Containment & SDLC Governance

*Designing, deploying, or auditing production AI coding harnesses, deterministic blueprint factories, neuro-symbolic verification stacks, microVM/sandbox containment, autonomous SRE safety bounds, and token portfolio FinOps.*

| Dimension | Specification |
|---|---|
| **Mandatory Reading List (In Order)** | 1. [`agents/agentic-sdlc-harness-architecture.md`](agents/agentic-sdlc-harness-architecture.md) *(5-layer architecture, Factored POMDP, Twin Absence, MAST & Static Claim Plane, 5-tier verification, microVMs, TNR SRE, FinOps)*<br>2. [`agents/zero-missed-requirements.md`](agents/zero-missed-requirements.md) *(Living Specs, protected blocks, SatisFix, structural compaction)*<br>3. [`agents/mcp-a2a-protocols.md`](agents/mcp-a2a-protocols.md) *(MCP Policy Gateway, OAuth 2.1 + RFC 8707, A2A)*<br>4. [`security.md`](security.md) *(OWASP Top 10:2025 + Agentic ASI01–ASI10 + supply chain)*<br>5. [`RULES.md`](RULES.md) *(Section 22: R-267 to R-272; R-228, R-229)* |
| **Key Invariant Rules** | **R-228** (OWASP Agentic least agency), **R-229** (MCP OAuth 2.1 + RFC 8707), **R-267** (Deterministic non-LLM control plane), **R-268** (Minimal single-agent & read-parallel topology over swarms), **R-269** (Mutation/PBT/hybrid SAST & regression preservation), **R-270** (MicroVM/OS sandboxing, host-proxy secrets, SPIFFE/WIMSE, rule-file peer review), **R-271** (Read-only SRE & Transactional No-Regression), **R-272** (Token portfolio FinOps & human merge explainability) |
| **Prohibited Actions** | ❌ Enforcing authorization, scope locks, or retry caps solely via LLM prompts.<br>❌ Deploying uncoordinated peer-agent swarms, > 4 sequential handoffs, or concurrent shared-filesystem writers.<br>❌ Placing standing API/DB/Git secrets inside agent sandbox memory or skipping peer review on `.mcp.json` / `AGENTS.md` / `SKILL.md` diffs.<br>❌ Granting AI SRE agents unsupervised production write authority without deterministic undo operators (`TNR`).<br>❌ Relying solely on LLM-generated coverage tests or functional checks without regression/mutation/SAST gates. |
| **Mandatory Verification** | 1. Control-Plane Enforcement: Deterministic phase gates, turn/retry caps, and worktree/Claim-Plane locks verified in non-LLM code.<br>2. Isolation & Egress Audit: Local OS sandbox (`srt`) or Firecracker/Kata v4.3+ microVM verified with default-deny egress and zero in-sandbox credentials.<br>3. Neuro-Symbolic Gate: 100% pass-to-pass regressions + mutation/PBT tests + SAST (`CodeQL`/`Semgrep`) pass cleanly.<br>4. Governance & FinOps: Tiered model routing active, Living Spec + audit logs persisted, and human merge explainability enforced. |

---
 
## 4. Conflict Resolution Protocol

If two guides or rules appear to conflict in a specific context:
1. **Security & Data Integrity ALWAYS Wins**: `RULES.md` and `security.md` override any framework-specific convenience.
2. **Standard Library Over Third-Party**: When functionality exists natively in the target runtime (e.g., Node.js `crypto.timingSafeEqual` or Go `net/http`), prefer native implementation over adding an unverified micro-package.
3. **Explicit Typing Over Implicit Inference**: When type inference produces `unknown` or loose types, provide explicit schema parsing.
4. **Escalation**: If a genuine contradiction between project constraints is detected, invoke the **3-Strike Escalation Protocol** in [`agents.md`](agents.md) Section 7.
