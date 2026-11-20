# 🧬 Evolutionary Architecture, Continuous Delivery & Team Cognitive Load (`evolutionary-delivery-architecture.md`)

> **Standard Identifier**: `SEC-FOUNDATIONS-EVOLUTION-001`  
> **Status**: Active / Production Standard  
> **Canonical Sources**: Neal Ford, Rebecca Parsons & Patrick Kua (*Building Evolutionary Architectures*), Mark Richards & Neal Ford (*Fundamentals of Software Architecture*; *Software Architecture: The Hard Parts*), Jez Humble & David Farley (*Continuous Delivery*), Nicole Forsgren, Jez Humble & Gene Kim (*Accelerate*), Matthew Skelton & Manuel Pais (*Team Topologies*), Fred Brooks (*The Mythical Man-Month*)  
> **Enforced Rules**: [`RULES.md`](../../RULES.md) (`R-153`–`R-170`, `R-244`)

---

## 1. Automated Architectural Fitness Functions (*Building Evolutionary Architectures* — Ford, Parsons, Kua)

Architecture diagrams rot the week after they are drawn. An **architectural fitness function** is an **automated, executable test** in CI that objectively guards an architectural characteristic against drift (`R-244`):

| Architectural Characteristic | Concrete Automated Fitness Function (CI Gate) |
| :--- | :--- |
| **Layer Isolation / Zero Circular Imports** | `dependency-cruiser` (TS/JS), `import-linter` (Python), `ArchUnit` (Java), or `go vet` forbidding `domain/` from importing `infra/` or `http/` |
| **Frontend Bundle & Performance Budget** | CI fails if main JS chunk exceeds budget (e.g., `> 180 KB` gzipped) or Lighthouse LCP/CLS regresses |
| **API Backward Compatibility** | OpenAPI diff (`oasdiff breaking`) or `buf breaking` blocking removal/renaming of published fields |
| **Database Query & Index Safety** | Automated migration linter (`squawk` / `strong_migrations`) blocking lock-heavy DDL (`ALTER TABLE ... ADD COLUMN ... NOT NULL` without safe default) |
| **Security & Hygiene Invariants** | `scripts/ci-gate.sh`, `trivy`, `gitleaks`, and `scripts/validate-skill.py` enforcing zero secrets, zero `any`, zero broken links |
| **Resilience Under Chaos** | Scheduled GameDays / chaos fault injection verifying circuit breakers trip and fallback responses stay within SLO |

> **Rule (`R-244`)**: Any architectural rule important enough to write in an ADR SHOULD be backed by an automated CI fitness function within the same milestone.

---

## 2. Managing Coupling & Distributed Trade-Offs (*Software Architecture: The Hard Parts* — Ford & Richards)

### 2.1 Connascence Taxonomy (Measure & Reduce Coupling)
Two components are **connascent** if a change in one requires a change in the other. Always refactor **dynamic connascence → static connascence** and keep strong connascence strictly **local** (inside one module), never across service boundaries:
- **Weakest (Acceptable across boundaries)**: Connascence of **Name** (calling a named function/field) and **Type** (strict static types/schemas).
- **Moderate (Keep local)**: Connascence of **Position** (positional function args > 3 → convert to named options object!), **Meaning** (magic numbers/status codes → convert to explicit enums/constants, `R-038`).
- **Strongest (Dangerous across services)**: Connascence of **Execution Order**, **Timing** (race conditions), **Value** (distributed consistency), and **Identity** (shared mutable cache/DB table between two services).

### 2.2 Modularity Before Microservices (The Decomposition Checklist)
Before splitting a modular monolith into distributed services, verify at least one hard **disintegrator** outweighs distributed systems tax (network latency, partial failures, distributed transactions, observability overhead):
- **Valid Disintegrators**: Independent scaling profiles (100× throughput delta), strict security/compliance blast-radius isolation, independent deployment cadence across autonomous teams, or distinct runtime/hardware requirements (e.g., GPU ML inference vs. Node API).
- **Invalid Disintegrators**: "Microservices are modern" or premature splitting of tightly coupled entities that still require synchronous distributed transactions.
- **Distributed Workflows (Sagas)**: When a workflow genuinely spans multiple data stores, choose **Orchestrated Sagas** for complex multi-step business workflows with compensating rollbacks (`R-194`), and **Choreographed Events** only for simple, loosely coupled fan-out reactions.

---

## 3. High-Velocity Delivery: *Continuous Delivery* (Humble & Farley) & *Accelerate* (DORA)

Empirical DORA research proves that **delivery speed and operational stability are NOT trade-offs**—elite engineering organizations excel at both simultaneously through small batch sizes, trunk-based development, and automated verification:

| DORA Metric | Elite Benchmark | Primary Engineering Enablers |
| :--- | :--- | :--- |
| **Deployment Frequency** | On-demand (multiple deploys per day) | Small PRs (< 300 LOC), feature flags (`workflows/feature-flags.md`), automated CI/CD |
| **Lead Time for Changes** | < 1 hour (commit to production) | Trunk-based development (short-lived branches < 24h), fast hermetic test suites (< 10 min CI) |
| **Change Failure Rate** | ≤ 5% | Pre-merge TDD, contract tests, canary rollouts, expand/contract DB migrations |
| **Failed Deployment Recovery Time (MTTR)** | < 1 hour | Instant rollback (immutable artifacts), feature-flag kill switches, structured OTel observability |

### Continuous Delivery Invariants
- **Build Binaries Once**: Promote the exact same immutable, digest-pinned container artifact (`sha256:...`) from Staging to Production—never rebuild per environment (`R-233`).
- **Keep `main` Always Releasable**: If `main` breaks, fixing or reverting the offending commit is the team's #1 priority above all feature work.

---

## 4. Conceptual Integrity & Cognitive Load (*The Mythical Man-Month* — Brooks; *Team Topologies* — Skelton & Pais)

- **Essential vs. Accidental Complexity** (*Fred Brooks, "No Silver Bullet"*):
  - *Essential complexity* is inherent to the real-world business problem (tax law, double-entry accounting, clinical safety).
  - *Accidental complexity* is self-inflicted friction (over-engineered abstractions, boilerplate, flaky build tools, inconsistent conventions). Ruthlessly eliminate accidental complexity (`/deslop`, `R-182`).
- **Conceptual Integrity**: A system designed with a coherent, unified set of patterns (one error envelope RFC 9457, one auth middleware pattern, one logging schema) is dramatically easier for both humans and AI agents to reason about than a patchwork of five competing styles.
- **Inverse Conway Maneuver & Cognitive Load** (*Team Topologies*):
  - Conway's Law dictates that software architecture mirrors organizational communication paths. Deliberately shape modular boundaries so each **Stream-Aligned Team** owns an end-to-end domain slice without waiting on handoffs from 4 other teams.
  - Minimize **extraneous cognitive load** (cryptic build scripts, undocumented setup, bespoke CI hacks) via **Platform Engineering golden paths** (`scaffolding/`), freeing team capacity for **germane domain complexity**.

---

## 5. Verification Checklist

- [ ] Key architectural boundaries (layer isolation, API compatibility, migration safety) are enforced by automated CI fitness functions (`R-244`).
- [ ] Cross-service interfaces use weak static connascence (named schemas/types), never shared mutable database tables.
- [ ] Functions with > 3 positional parameters use named option/parameter objects.
- [ ] Delivery pipeline builds immutable, digest-pinned artifacts once and promotes across environments.
- [ ] Branches are short-lived (< 24–48h) and hidden behind feature flags for incomplete multi-PR capabilities.
- [ ] Accidental complexity and redundant abstractions are pruned before merging (`R-182`, `R-236`).
