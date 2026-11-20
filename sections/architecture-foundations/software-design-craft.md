# 🏛️ Software Design Craft, Legacy Modernization & Google-Scale Engineering (`software-design-craft.md`)

> **Standard Identifier**: `SEC-FOUNDATIONS-CRAFT-001`  
> **Status**: Active / Production Standard  
> **Canonical Sources**: John Ousterhout (*A Philosophy of Software Design*), Kent Beck (*Tidy First?*), Michael Feathers (*Working Effectively with Legacy Code*), Martin Fowler (*Refactoring*, 2nd Ed.), Eric Evans & Vaughn Vernon (*Domain-Driven Design*), Andrew Hunt & David Thomas (*The Pragmatic Programmer*), Titus Winters et al. (*Software Engineering at Google*)  
> **Enforced Rules**: [`RULES.md`](../../RULES.md) (`R-027`–`R-045`, `R-236`–`R-240`, `R-245`)

---

## 1. Managing Complexity: *A Philosophy of Software Design* (John Ousterhout)

Complexity manifests in three observable symptoms: **Change Amplification** (a tiny requirement change forces edits across 15 files), **Cognitive Load** (how much context an engineer must hold to safely edit one line), and **Unknown Unknowns** (the worst symptom: it is non-obvious which files must change to preserve invariants).

### 1.1 Deep Modules Over Shallow Modules (`R-236`)
```
   DEEP MODULE (Good)                     SHALLOW MODULE (Anti-Pattern)
  ┌─────────────────┐                 ┌───────────────────────────────────┐
  │ Narrow Interface│                 │ Wide, Leaky Interface (12 params) │
  ├─────────────────┤                 ├───────────────────────────────────┤
  │                 │                 │ Thin pass-through delegation      │
  │ Rich, Hidden    │                 └───────────────────────────────────┘
  │ Implementation  │                 (Interface complexity ≈ Implementation)
  │ (File I/O,      │
  │  Buffering,     │
  │  Locking,       │
  │  Retries)       │
  └─────────────────┘
```
- **Rule**: Prefer **deep modules** (simple, small public interface hiding substantial internal machinery—like Unix `open/read/write/close` or a cohesive `LedgerService.postEntry()`) over **classitis** (dozens of tiny shallow wrappers, pass-through methods, and 1-line indirections that multiply cognitive load without hiding complexity).
- **Information Leakage**: Never expose internal storage formats, cache keys, or SQL join structures across module boundaries. If two modules must know the exact same hidden detail (e.g., a binary file header or JSON key convention), merge them or encapsulate that detail behind one module.
- **Pull Complexity Downward**: It is better for a module author to absorb 30 lines of tricky edge-case handling *once* inside a library/service than to force 50 callers to pass configuration flags or repeat boilerplate checks.
- **Define Errors Out of Existence (`R-238`)**: Before adding a new exception branch, ask whether the API semantics can make the edge case harmless and well-defined (e.g., `unset(key)` succeeding idempotently when `key` is already absent; `substring(start, end)` clamping gracefully where domain-appropriate; rejecting truly invalid financial/security states strictly at ingress).
- **Strategic vs. Tactical Programming**: Tactical "just make it work fast" programming creates *tactical tornadoes*—accumulating complexity debt that slows every future commit. Invest 10–20% of every feature cycle in clean abstractions so complexity stays bounded.

---

## 2. Economics of Change: *Tidy First?* (Kent Beck)

> **"Make the change easy (warning: this may be hard), then make the easy change."**

### 2.1 Separate Structural Changes from Behavioral Changes (`R-237`)
Never mix preparatory refactoring (renaming, extracting helpers, introducing guard clauses, normalizing cohesion) with behavioral changes (bug fixes, new features) in the **same commit or PR hunk**:
1. **Commit 1 (Structural Tidying)**: Behavior is 100% unchanged; existing tests pass without modification. Trivial to review and trivially reversible.
2. **Commit 2 (Behavioral Change)**: Clean, surgical diff implementing only the feature or bug fix on top of the tidied structure.

### 2.2 Cohesion & Coupling Laws
- **Constantine's Equivalence**: $\text{Cost(software)} \approx \text{Cost(change)}$, and $\text{Cost(change)}$ is dominated by **coupling** (changing Module A cascades into Module B, C, D).
- **Tidy Only What You Touch**: Apply small, local tidying (guard clauses to flatten nesting, dead code deletion, explaining helper variables, cohesive chunking) strictly on the path of the current task—never embark on speculative repo-wide rewrites (`R-015`, `R-016`).

---

## 3. Safe Legacy Modernization: *Working Effectively with Legacy Code* (Feathers) & *Refactoring* (Fowler)

Michael Feathers defines **legacy code** simply as **code without tests**. Editing untested production code directly is gambling.

### 3.1 The Legacy Change Algorithm (`R-239`)
1. **Identify Change Points**: Locate exact functions/modules needing modification via read-only forensics (`/how`, `/why`).
2. **Find Test Points & Seams**: A **seam** is a place where you can alter behavior without editing the code in place (dependency injection interface, clock/network adapter, environment boundary).
3. **Break Dependencies Safely**: Extract pure functions or inject minimal interfaces using *automated* safe refactorings (Extract Method, Parameterize Constructor).
4. **Write Characterization Tests FIRST**: Write tests that pin down **what the system actually does today** (including quirks), NOT what you wish it did. Run them green before changing behavior.
5. **Apply Changes & Refactor**: Make the minimal behavioral change under the characterization safety net.

### 3.2 Large-Scale Safe Migration Patterns
- **Strangler Fig Pattern** (*Fowler*): Route traffic incrementally from the legacy module to the new module behind a facade/router—never attempt a big-bang rewrite.
- **Branch by Abstraction**: Introduce an abstraction interface over the legacy component, migrate callers to the interface, implement the new backend behind the interface, flip traffic via feature flag, then delete the legacy implementation.
- **Mikado Method**: When a refactor triggers cascading compiler/test breakages, record the prerequisite as a leaf node in a dependency graph, **`git reset --hard`** back to green, and solve leaves bottom-up so `main` never stays broken.

---

## 4. Domain Modeling: *Domain-Driven Design* (Evans & Vernon)

- **Ubiquitous Language**: Code identifiers (`Invoice`, `JournalEntry`, `Shipment`, `CreditMemo`) MUST match the exact vocabulary used by domain experts—eliminating lossy mental translation layers (`R-037`).
- **Bounded Contexts**: Do not force one monolithic `User` or `Product` model across Billing, Auth, Fulfillment, and Analytics. Each Bounded Context owns its own model, schema, and invariants.
- **Anti-Corruption Layer (ACL)**: When integrating with an external legacy ERP, third-party SaaS API, or upstream bounded context, translate foreign payloads into your domain model at a dedicated adapter boundary so foreign schema quirks never leak into core domain logic.
- **Aggregate Consistency Rules** (*Vaughn Vernon*):
  1. Model true transactional invariants inside small Aggregates.
  2. Reference other Aggregates strictly by **ID** (not direct object graph references).
  3. Modify **one Aggregate per database transaction**; update other Aggregates asynchronously via Domain Events + Transactional Outbox.
  4. Protect invariants with optimistic concurrency (`version` column) or explicit locking.

---

## 5. Engineering at Scale: *Software Engineering at Google* (Winters et al.) & *The Pragmatic Programmer*

| Law / Principle | Definition | Concrete Engineering Mandate |
| :--- | :--- | :--- |
| **Hyrum's Law** | With enough users of an API, every observable behavior (ordering, error strings, timing) will be depended on by somebody. | Treat undocumented side effects as implicit contracts; version breaking changes formally (`R-018`) and check callers before changing output shape. |
| **Chesterton's Fence** (`R-245`) | Never tear down a fence until you know why it was built. | Run `git log -S` / `git blame -w -C -C` before deleting guards, retries, or compatibility shims. |
| **Test Behavior, Not Implementation** (`R-240`) | Tests tightly coupled to private methods or mock call order break on harmless refactors (**change-detector tests**). | Assert public outputs and observable state transitions; prefer real fakes/Testcontainers over brittle internal mocks (`R-088`, `R-090`). |
| **Shift Left** | Finding a bug in design/lint costs 1×; in CI 10×; in production 100×. | Encode invariants into types, strict schemas, pre-commit hooks, and CI gates rather than relying on manual code review memory. |
| **Beyoncé Rule** | *"If you liked it, you should have put a CI test on it."* | Any behavior not guarded by an automated test is not guaranteed to survive future infrastructure or library upgrades. |
| **Tracer Bullets** (*Pragmatic Programmer*) | Build a thin, end-to-end working vertical slice early (UI → API → DB → Test) rather than perfecting isolated layers in the dark. | Prove architectural assumptions end-to-end before fleshing out secondary features. |
| **Broken Windows Theory** (*Pragmatic Programmer*) | One ignored hack, disabled lint rule, or flaky test signals permission for rapid entropy. | Fix broken builds, flaky tests, and lint suppressions immediately—never let debt normalize. |

---

## 6. Verification Checklist

- [ ] New modules expose narrow, deep interfaces that hide internal complexity (`R-236`).
- [ ] Structural tidying commits are separated from behavioral bug-fix/feature commits (`R-237`).
- [ ] Unnecessary error branches are designed out where semantically safe; invalid domain/security inputs fail fast (`R-238`).
- [ ] Untested legacy code is locked down with characterization tests before behavioral edits (`R-239`).
- [ ] Tests verify observable public behavior rather than brittle private implementation calls (`R-240`).
- [ ] Existing guards/workarounds were audited via git archaeology before removal (`R-245`).
