# 🔎 Pre-Code Forensics, Interrogation & Architecture Settling (`code-forensics-interrogation.md`)

> **Standard Identifier**: `AGT-FORENSICS-001`  
> **Status**: Active / Production Standard  
> **Synthesizes**: `pstack` (`/how`, `/why`, `/interrogate`, `/architect`, failed-theory rollback), `gstack` (`/office-hours`, `/plan-eng-review`), `tstack` (`file-pr`, `leaving-pr-comments`), and *Software Engineering at Google* (Chesterton's Fence)  
> **Cross-References**: [`RULES.md`](../RULES.md) (`R-003`, `R-015`, `R-182`, `R-245`–`R-249`), [`agents/poteto-discipline.md`](poteto-discipline.md), [`agents/unified-agent-stacks.md`](unified-agent-stacks.md)

---

## 1. Why Pre-Code Discipline Eliminates 80% of Engineering Waste

Most defective PRs and AI-generated regressions do not fail during coding—they fail in the **first 5 minutes**, when an engineer or agent edits code without understanding:
1. **How** the existing system actually executes at runtime (`/how`).
2. **Why** a seemingly awkward constraint, guard, or workaround was originally introduced (`/why` — Chesterton's Fence).
3. **What** hidden failure modes and ambiguous edge cases lurk inside the request (`/interrogate` / `/office-hours`).
4. **Where** the exact module boundaries, types, and invariants belong (`/architect`).

This guide operationalizes four strict, read-only pre-code protocols plus two post-code hygiene protocols.

---

## 2. `/how` — Read-Only Execution Path Forensics

**Trigger**: Before modifying unfamiliar code, diagnosing a subtle bug, or planning a refactor.  
**Hard Constraint**: **100% Read-Only.** Zero file edits allowed during `/how`.

### Execution Protocol
1. **Entrypoint-to-Sink Trace**: Trace the exact data flow from ingress (HTTP handler, CLI arg, queue consumer, UI event) through every transformation, validation boundary, state mutation, and storage/network sink.
2. **Verify Runtime Truth, Not Comments**: Comments drift; code and tests are truth. Inspect actual type definitions, SQL schemas, middleware order, and configuration defaults (`R-003`).
3. **Map Side Effects & Implicit Coupling**: Identify shared mutable state, caches, triggers, event listeners, environment variables, and external callers (Hyrum's Law: every observable behavior may be depended upon).
4. **Output Format (Concise Trace Brief)**:
   - Exact file paths + line numbers for the execution chain.
   - Data shape transformations at each boundary.
   - Observed invariants and hidden assumptions.

---

## 3. `/why` — Git & Decision Archaeology (Chesterton's Fence, `R-245`)

> **Chesterton's Fence**: Never remove, simplify, or rewrite a guard, lock, retry, compatibility shim, or unusual abstraction until you can articulate the exact failure mode it was built to prevent.

**Hard Constraint**: **100% Read-Only.**

### Archaeology Commands
```bash
# 1. Find the commit that introduced or altered a specific line/symbol
git log -S "<symbol_or_literal>" --oneline -n 10
git log -L <start_line>,<end_line>:<path/to/file>

# 2. Blame ignoring whitespace-only and moved-code noise
git blame -w -C -C -L <start>,<end> <path/to/file>

# 3. Inspect full commit context & linked PR/issue rationale
git show --stat <commit_sha>
```

### Decision Rule
- If archaeology reveals the original constraint still holds (e.g., race condition, third-party API bug, legacy client compatibility), **preserve the invariant** or prove mathematically why the new design eliminates it.
- If the original constraint is demonstrably obsolete (e.g., deleted upstream service, deprecated runtime removed), cite the commit/PR evidence in your commit message when removing it.

---

## 4. `/interrogate` & `/office-hours` — Adversarial Requirements Grill

**Trigger**: Ambiguous feature requests, high-risk changes, greenfield architectures, or specifications with unstated failure modes.

### 4.1 The Six Forcing Questions (`gstack /office-hours`)
Before writing a specification for a new product capability or subsystem, answer all six concisely:
1. **Concrete User & Pain**: Who experiences this failure/need today, and what exact workaround are they using?
2. **Narrowest Wedge**: What is the smallest vertical slice that delivers verifiable end-to-end value?
3. **Explicit Non-Goals**: What is deliberately *out of scope* for this iteration?
4. **Data & State Ownership**: Which store is the single source of truth, and what happens during partial failure?
5. **Blast Radius & Reversibility**: If this ships broken, how fast can we detect it and roll back without data corruption?
6. **Direct Proof Criterion**: What exact observable command, HTTP trace, or browser check proves it works?

### 4.2 Adversarial Failure-Mode Interrogation (`pstack /interrogate`)
Cross-examine every design proposal against six adversarial probes:
- **Concurrency**: What happens when two requests execute this operation at the exact same millisecond?
- **Empty / Zero / Extreme Scale**: What happens with 0 items, 1 item, 1,000,000 items, or a 10MB payload?
- **Network / Dependency Partition**: What happens if the DB, Redis, or downstream API times out after 5s or returns HTTP 500?
- **AuthN / AuthZ / Multi-Tenancy**: Can User A read, mutate, or infer the existence of Tenant B's resource?
- **Backward Compatibility**: Will in-flight requests from the previous deployment version break during a rolling deploy?
- **Idempotency & Retries**: What happens if the client or queue delivers the exact same request twice?

---

## 5. `/architect` — Pre-Code Boundary & Signature Settling

**Trigger**: Any task touching $\ge 3$ files, introducing a new module/API, or modifying persistent schemas.

Before writing implementation bodies, settle and freeze:
1. **Deep Module Interfaces** (*Ousterhout*, `R-236`): Define narrow, expressive public signatures that hide implementation complexity rather than shallow pass-through wrappers.
2. **Exact Types, Schemas & Error Contracts**: Write the TypeScript interfaces / Zod schemas / Pydantic models / Rust enums / SQL DDL first. Let the type checker validate boundary shapes before implementing internals.
3. **Dependency Direction**: Verify strict inward dependency flow (Transport → Use Case / Domain ← Infrastructure Adapters) with zero circular imports (`R-031`, `R-041`).
4. **Separate Structural Tidying from Behavioral Changes** (*Kent Beck, Tidy First?*, `R-237`): If existing code needs preparatory refactoring before adding the feature, plan Commit 1 (pure structural tidy, behavior unchanged, tests green) and Commit 2 (behavioral feature/fix).

---

## 6. Failed-Theory Cleanup (`pstack`, `R-246`)

When debugging or exploring a solution, agents frequently test Hypothesis A (adding logging, helper flags, or defensive guards), discover Hypothesis A was wrong, and pivot to Hypothesis B—leaving Hypothesis A's dead edits inside the working tree.

**Mandatory Cleanup Gate**:
1. Before finalizing any fix, inspect `git diff` hunk-by-hunk.
2. Revert EVERY line added for an exploratory hypothesis that did not prove to be the root cause.
3. Remove all temporary debug instrumentation (`console.log`, `print`, debug flags, commented-out attempts).
4. Re-run the full verification suite *after* cleanup to confirm the minimal diff alone fixes the defect.

---

## 7. Problem-First PR Authoring (`tstack` `file-pr` & `leaving-pr-comments`)

### 7.1 `file-pr` Structure (Problem First, Never File Inventory)
A pull request description MUST NOT be an auto-generated list of touched files (reviewers can read `git diff --stat`). Lead with *why*:
```markdown
## Problem
[1-3 sentences describing the exact user/system failure or requirement and its root cause.]

## Solution
[Concise explanation of the mechanism chosen and why alternatives were rejected.]

## Verification Proof
- Reproduction test failed before fix: `<exact command>` (exit 1)
- Verification passed after fix: `<exact command>` (exit 0, N/N passed)
- Lint / Typecheck / CI Gate: `<exact command>` (exit 0)

## Risk & Rollback
[Blast radius, migration reversibility, or feature flag kill-switch.]
```

### 7.2 `leaving-pr-comments` Discipline
When an agent posts comments on a PR (replying to reviewers or summarizing bot triage):
- Lead with the direct conclusion (`Fixed in <sha>`, `Declined — out of scope because ...`, `False positive — verified at <file:line>`).
- Never post verbose apologetic filler ("Great catch! Thank you so much for pointing this out!").
- Cite exact commit SHAs, file paths, and observed test outputs.

---

## 8. Verification Checklist

- [ ] Executed read-only `/how` trace before editing unfamiliar execution paths.
- [ ] Verified Chesterton's Fence via `git log` / `git blame` before removing existing guards (`R-245`).
- [ ] Answered forcing questions & failure-mode probes before writing non-trivial specs.
- [ ] Settled types, boundaries, and deep module signatures before writing implementation bodies (`R-236`).
- [ ] Stripped 100% of failed exploratory theories and temporary instrumentation before commit (`R-246`).
- [ ] Authored PR description problem-first with concrete CLI verification proof.
