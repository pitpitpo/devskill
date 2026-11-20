# 🏆 Definition of Done (DoD) & 100-Point Ship Gate (`DEFINITION_OF_DONE.md`)

> **Classification**: Mandatory Release & Merge Gate  
> **Applicability**: All Pull Requests, Agent Deliverables, Features, Bugfixes, and Production Releases  
> **Enforcement**: Automated CI/CD pipelines, Pre-commit hooks, and Mandatory Code Review gates.

---

## 1. The Dual-Threshold Ship Gate Policy

A task or pull request CANNOT be marked complete or merged into the primary branch unless it satisfies the **Dual-Threshold Ship Gate Rule**:

```
                              ┌──────────────────────────────────────────────┐
                              │          DUAL-THRESHOLD SHIP GATE            │
                              ├──────────────────────────────────────────────┤
                              │ 1. TOTAL SCORE >= 95 / 100 POINTS            │
                              │ 2. EVERY CATEGORY >= 9.0 / 10 RELATIVE SCORE │
                              └──────────────────────────────────────────────┘
```

> **The Zero-Defect Rule**: Achieving a total score of 95+ is insufficient if any single category falls below 9.0/10 (90% of its available category points). For instance, an 80% score in Security or Accessibility blocks deployment regardless of high scores elsewhere.

### Score Weights Overview

| # | Category | Max Points | Passing Threshold (>= 90%) | Focus Area |
|---|---|---|---|---|
| **1** | **Code Quality** | 20 pts | ≥ 18.0 pts | Type safety, clean architecture, SOLID, zero placeholders |
| **2** | **Testing & QA** | 20 pts | ≥ 18.0 pts | Pyramid balance, deterministic execution, negative paths |
| **3** | **Security & Privacy** | 15 pts | ≥ 13.5 pts | Schema validation, parameterization, auth/IDOR, secrets |
| **4** | **Performance & Efficiency** | 10 pts | ≥ 9.0 pts | Core Web Vitals, N+1 queries, pagination, memory bounds |
| **5** | **Documentation & Contracts** | 10 pts | ≥ 9.0 pts | API specs, domain models, docstrings, changelog |
| **6** | **Accessibility (a11y) & UX** | 10 pts | ≥ 9.0 pts | WCAG 2.2 AA, keyboard operability, responsive design |
| **7** | **Operations & Observability**| 10 pts | ≥ 9.0 pts | Structured JSON logs, health probes, tracing, graceful exit |
| **8** | **Git Hygiene & Process** | 5 pts | ≥ 4.5 pts | Conventional Commits, atomic PRs, clean history |
| **Σ** | **TOTAL** | **100 pts** | **≥ 95.0 pts** | **Mandatory Ship Gate Threshold** |

---

## 2. Detailed Category Rubric & Scoring Criteria

---

### Category 1: Code Quality & Architecture (Max: 20 Points)

*Threshold: ≥ 18.0 / 20 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **4 pts** | **Strict Static Typing**: TypeScript compiles with `"strict": true` and zero errors; Python passes `mypy --strict`; Go/Rust compile cleanly. Zero use of `any`, `as any`, `@ts-ignore`, or `# type: ignore` (R-033, R-034). | `npm run typecheck` or `mypy --strict .` |
| **4 pts** | **Zero Laziness & Placeholders**: Absolutely zero `TODO`, `FIXME`, `HACK`, `TBD`, or stub markers in production code. Zero mock, dummy, or fake data in production paths (R-001, R-002). | `./scripts/ci-gate.sh` |
| **4 pts** | **SOLID & Complexity Ceiling**: Cyclomatic complexity ≤ 10 per function (McCabe). Functions ≤ 40 lines. Single responsibility principle maintained (R-027, R-035, R-036). | `eslint` / `ruff` with complexity rules enabled |
| **4 pts** | **Robust Fail-Closed Error Handling**: Zero swallowed exceptions (`catch {}` or `except: pass`). All errors fail closed (OWASP A10:2025 / R-232) using typed custom domain exceptions with cause chaining (R-046, R-047, R-049). | `./scripts/ci-gate.sh` |
| **4 pts** | **Clean Separation of Concerns**: Transport handlers (HTTP/gRPC) do not query databases directly. Hexagonal / Clean layered architecture strictly preserved (R-041). | Architecture linter / PR diff inspection |

---

### Category 2: Testing & Quality Assurance (Max: 20 Points)

*Threshold: ≥ 18.0 / 20 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **4 pts** | **Test Pyramid & Flake-Free**: ~70% unit tests, ~20% integration tests, ~10% E2E tests. Deterministic execution: zero arbitrary `sleep()` statements; all async assertions use polling predicates (R-084, R-087). | `git grep -EIn "sleep\([0-9]+\)" tests/` |
| **4 pts** | **Non-Tautological Assertions**: Every test verifies real state changes or return values. Zero tautological assertions (`expect(true).toBe(true)` or `assert 1 == 1`) (R-085). | Automated test AST inspection |
| **4 pts** | **Real Database Integration**: Integration tests run against actual database instances (Testcontainers or ephemeral PostgreSQL/MySQL), never mocked in-memory database engines (R-088). | `docker ps` during integration test run |
| **4 pts** | **Negative & Boundary Path Coverage**: Comprehensive tests for 4xx/5xx responses, malformed schemas, boundary edge cases (null, 0, empty lists, max integers, unicode) (R-091, R-092). | Test suite execution report |
| **4 pts** | **Coverage Ratchet & Red-Green Proof**: Test suite passes with exit code 0. Test coverage percentage did not regress. For bugfixes, test failure was proven before applying code fix (R-004, R-005, R-094). | CI coverage report & exit code check |

---

### Category 3: Security & Privacy (Max: 15 Points)

*Threshold: ≥ 13.5 / 15 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **3 pts** | **Runtime Boundary Validation**: All external inputs (bodies, params, headers, webhooks, MCP tool args) validated with strict runtime schemas (Zod, Pydantic, Valibot) before business logic (R-060). | Code review & schema validation tests |
| **3 pts** | **100% Parameterized Queries**: Zero string concatenation or template interpolation into SQL, NoSQL, LDAP, or shell commands. Prepared statements used exclusively (OWASP A05:2025, R-061). | Semgrep SQL injection scan rule |
| **3 pts** | **Defense-in-Depth Auth, IDOR & Least Agency**: Authenticate every protected route, enforce tenant ownership (OWASP A01:2025, R-062, R-063), and scope MCP/agent tokens via OAuth 2.1 + RFC 8707 (R-228, R-229). | Auth middleware, IDOR & MCP scope tests |
| **3 pts** | **Zero Secrets & Supply Chain Integrity**: Zero credentials committed to git (R-064); frozen installs, SBOM, and CVSS ≥ 7.0 CVE gate active (OWASP A03:2025, R-118–R-125). | `gitleaks detect`, `trivy fs .`, `./scripts/ci-gate.sh` |
| **3 pts** | **NIST 800-63B-4 Auth, Headers, Hashing & PQC Agility**: Argon2id hashing, NIST SP 800-63B-4 password/blocklist policy (R-230), OWASP security headers (CSP, HSTS), and hybrid PQC TLS readiness (R-065, R-071, R-231). | HTTP header scanner & auth integration tests |

---

### Category 4: Performance & Efficiency (Max: 10 Points)

*Threshold: ≥ 9.0 / 10 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **3 pts** | **Core Web Vitals & Latency Budgets**: Frontend meets CWV (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1). Backend API p99 latency within budget (< 200ms for OLTP queries) (R-131). | Lighthouse CI / load test benchmark |
| **3 pts** | **Zero N+1 Queries & Pagination**: ORM relationships eager-loaded (`select_related`, `include`). Mandatory `LIMIT` and cursor pagination on all list queries (R-104, R-105). | SQL query counter in tests |
| **2 pts** | **Bounded Resource Allocation**: In-memory buffers, caches, and queues have explicit capacity ceilings and TTL expirations to prevent memory leaks (R-044, R-116). | Memory profile / code review |
| **2 pts** | **Bundle Budgets & Asset Optimization**: Initial JS bundle ≤ 170 KB gzipped. Images served in AVIF/WebP with explicit dimensions; below-the-fold images lazy-loaded (R-132, R-133). | Webpack/Vite bundle analyzer |

---

### Category 5: Documentation & Contracts (Max: 10 Points)

*Threshold: ≥ 9.0 / 10 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **3 pts** | **Updated Specs & Contracts**: Technical specifications ([`specs.md`](specs.md)) and OpenAPI/JSON schemas updated to reflect all new and modified endpoints and data models. | Schema diff verification |
| **3 pts** | **Self-Documenting Code & Docstrings**: Public interfaces, classes, and complex algorithms have descriptive docstrings explaining the design rationale (*why*), not just behavior (R-017). | Linter docstring check |
| **2 pts** | **Architecture Decision Records (ADR)**: Architectural choices and framework selections documented in [`decisions.md`](decisions.md) with trade-off analysis. | File inspection |
| **2 pts** | **Changelog Maintenance**: `CHANGELOG.md` updated adhering to *Keep a Changelog* (Added, Changed, Fixed, Security) and SemVer 2.0.0 (R-166, R-170). | Git diff on CHANGELOG.md |

---

### Category 6: Accessibility (a11y) & UX (Max: 10 Points)

*Threshold: ≥ 9.0 / 10 points (Relative: ≥ 9.0/10)*

*(For backend-only services, points are evaluated against API accessibility: RFC 9457 problem details, clear validation errors, and predictable status codes).*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **3 pts** | **WCAG 2.2 Level AA Compliance**: Color contrast ratios ≥ 4.5:1 for normal text, ≥ 3:1 for large text. Automated accessibility scan passes with zero critical/serious violations (R-129). | `axe-core` / Playwright accessibility scan |
| **3 pts** | **Full Keyboard Operability**: All interactive UI elements focusable via `Tab`, operable via `Enter`/`Space`, with unobstructed, visible focus rings (R-130). | Keyboard navigation test suite |
| **2 pts** | **Accessible Forms & ARIA**: Form inputs programmatically linked to `<label>` tags. Inline validation errors linked via `aria-describedby` and `aria-invalid` (R-137). | DOM tree assertion tests |
| **2 pts** | **Semantic HTML & Mobile-First**: Native semantic tags used (`<button>`, `<main>`, `<dialog>`). Mobile-responsive layout functional from 320px up to 4K displays (R-135, R-136). | Viewport responsive tests |

---

### Category 7: Operations & Observability (Max: 10 Points)

*Threshold: ≥ 9.0 / 10 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **3 pts** | **Structured JSON Logging**: Logs emitted as structured JSON to stdout/stderr with ISO 8601 UTC timestamp, level, message, service name, and trace context. Zero raw `console.log` (R-142). | Log output verification test |
| **2 pts** | **Health & Readiness Probes**: Verified `/healthz` (liveness) and `/readyz` (readiness with database/cache connectivity checks) endpoints implemented (R-145). | HTTP GET on `/healthz` and `/readyz` |
| **2 pts** | **Distributed Tracing & OTel Semantic Conventions**: W3C Trace Context (`traceparent`) propagated across HTTP, queues, and MCP/A2A hops with OpenTelemetry (incl. `gen_ai.*`) semantic attributes (R-143, R-149, R-151). | OpenTelemetry trace propagation test |
| **2 pts** | **PII & Credential Scrubbing**: Automated log masking strips authorization headers, passwords, credit card numbers, and PII before writing to log streams (R-144). | Logger redaction test cases |
| **1 pt** | **Graceful Shutdown**: Service handles `SIGTERM`/`SIGINT`, drains inflight requests within timeout, closes database pools, and exits cleanly (R-147). | Process termination test |

---

### Category 8: Git Hygiene & Process (Max: 5 Points)

*Threshold: ≥ 4.5 / 5 points (Relative: ≥ 9.0/10)*

| Points | Verification Criteria | Automated Check / Command |
|---|---|---|
| **2 pts** | **Conventional Commits 1.0.0**: All commit messages strictly follow `<type>(<scope>): <summary>` format (R-163). | `commitlint` pre-commit hook |
| **2 pts** | **Atomic PR & Minimal Diffs**: Changes are focused on a single logical feature/fix. PR size ≤ 400 lines of code. Unrelated files untouched (R-015, R-164, R-165). | `git diff --stat` inspection |
| **1 pt** | **Clean Linear History**: Branch rebased on latest primary trunk. Zero merge conflict markers or unintended merge bubbles (R-167). | `git log --graph --oneline` |

---

## 3. Scorecard Self-Assessment Calculation Worksheet

Every deliverable must compute and include this scorecard in its Phase 8 Final Report:

```markdown
### 📊 Definition of Done Scorecard

| Category | Available Pts | Earned Pts | Relative Score (/10) | Gate Status |
|---|---|---|---|---|
| 1. Code Quality & Architecture | 20 | [  ] | [ Earned / 20 * 10 ] | PASS / FAIL (Min 9.0) |
| 2. Testing & Quality Assurance | 20 | [  ] | [ Earned / 20 * 10 ] | PASS / FAIL (Min 9.0) |
| 3. Security & Privacy | 15 | [  ] | [ Earned / 15 * 10 ] | PASS / FAIL (Min 9.0) |
| 4. Performance & Efficiency | 10 | [  ] | [ Earned / 10 * 10 ] | PASS / FAIL (Min 9.0) |
| 5. Documentation & Contracts | 10 | [  ] | [ Earned / 10 * 10 ] | PASS / FAIL (Min 9.0) |
| 6. Accessibility & UX | 10 | [  ] | [ Earned / 10 * 10 ] | PASS / FAIL (Min 9.0) |
| 7. Operations & Observability | 10 | [  ] | [ Earned / 10 * 10 ] | PASS / FAIL (Min 9.0) |
| 8. Git Hygiene & Process | 5 | [  ] | [ Earned / 5 * 10 ] | PASS / FAIL (Min 9.0) |
| **TOTAL** | **100** | **[  ]** | **[ Total / 10 ]** | **SHIP / BLOCK** |

**Final Ship Gate Assessment**:
- Total Score: [  ] / 100 (Required: >= 95.0)
- Lowest Relative Category Score: [  ] / 10.0 (Required: >= 9.0)
- **GATE VERDICT**: [APPROVED FOR SHIP / BLOCKED FOR REMEDIATION]
```
