# 🔄 8-Phase Engineering Workflow & Systematic Debugging Protocol (`workflows/WORKFLOW.md`)

> **Classification**: Core Engineering Lifecycle Standard  
> **Applicability**: Autonomous AI Agents, Coding Copilots, and Engineering Teams  
> **Enforcement**: Mandatory phase progression; no phase may be bypassed without documented justification.

---

## The 8-Phase Engineering Lifecycle

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   1. UNDERSTAND │ ───► │   2. RESEARCH   │ ───► │    3. PLAN      │ ───► │  4. IMPLEMENT   │
│ Ingest specs,   │      │ Inspect code,   │      │ Design schemas, │      │ Write strictly  │
│ scope & bounds  │      │ docs & packages │      │ tests & risks   │      │ typed code      │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └────────┬────────┘
                                                                                    │
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐               │
│   8. REPORT     │ ◄─── │   7. DOCUMENT   │ ◄─── │   6. REVIEW     │ ◄─── 5. TEST  │
│ Deliver proof   │      │ Update specs,   │      │ Score against   │      Run tests, │
│ & scorecard     │      │ API docs & log  │      │ DoD (>= 95 pts) │      types & CI │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────┘
```

---

## Phase 1: Understand

**Objective**: Establish a clear, unambiguous understanding of the task, its business context, operational boundaries, and acceptance criteria before writing or modifying any code.

### 1.1 Requirements Parsing & Scope Ingestion
- Read the user request or task description completely.
- Extract the core requirements, explicit constraints, and expected output deliverables.
- Identify implicit requirements (e.g., error handling, input validation, backwards compatibility, telemetry).

### 1.2 Boundary & Authority Check
- Verify write permissions and workspace sandboxing (stay strictly within the target repository root; R-173).
- Check the **Always / Ask / Never** boundaries in [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md#5-always--ask--never-boundaries).
- Determine whether the task requires any **ASK** actions (e.g., adding a new dependency, dropping columns, breaking API contracts).

### 1.3 Clarification Thresholds
- **When to Ask**: Ask a concise question ONLY if a missing user decision would materially change the architectural design, security model, or data schema.
- **When to Proceed**: Make reasonable, conservative assumptions if the ambiguity can be resolved using existing repository conventions, industry standards (RFC/OWASP), or defensive programming practices. Document all assumptions in the final report.

---

## Phase 2: Research

**Objective**: Gather ground-truth context from the local filesystem, package manifests, and authoritative standards to eliminate hallucinations.

### 2.1 Codebase Reconnaissance
- Consult [`index.json`](file:///home/agy/.t3/userdata/attachments/devskill/index.json) to locate relevant modules, language guides, and architectural patterns.
- Read existing implementations in related files to observe:
  - Naming conventions, directory organization, and module boundaries.
  - Error handling patterns, custom exceptions, and logging standards.
  - Data access patterns (ORM models, migration structures, repository patterns).

### 2.2 Dependency & Environment Verification
- Inspect package manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`) and lockfiles to determine exact installed library versions (R-003, R-006).
- Never assume an API or method exists without verifying against the installed version's type definitions or documentation.
- If a new dependency is required, verify its download count, release date, and registry URL to prevent typosquatting and slopsquatting attacks (R-007).

### 2.3 External Standard Grounding
- Cross-reference specifications against formal RFCs (e.g., RFC 7807 for API errors, RFC 9106 for Argon2id), OWASP guides, or WCAG accessibility criteria (R-009).

---

## Phase 3: Plan

**Objective**: Formulate a deterministic, test-first design and risk mitigation strategy prior to making code edits.

### 3.1 Architectural Alignment
- Consult [`decisions.md`](file:///home/agy/.t3/userdata/attachments/devskill/decisions.md) to choose the appropriate architectural pattern (Modular Monolith vs Microservices, synchronous REST vs asynchronous message queue).
- Ensure strict separation of concerns (Transport -> Application -> Domain -> Infrastructure; R-041).

### 3.2 Interface & Contract Specification
- Define domain models, request/response schemas, and validation rules in [`specs.md`](file:///home/agy/.t3/userdata/attachments/devskill/specs.md) format before implementation.
- Establish typed contracts (TypeScript interfaces, Pydantic schemas, Rust structs).

### 3.3 Threat Modeling & Security Review
- Consult [`security.md`](file:///home/agy/.t3/userdata/attachments/devskill/security.md) for potential vulnerability vectors (OWASP Top 10):
  - Will user input be parameterized?
  - Does the endpoint verify tenant ownership / IDOR authorization?
  - Are sensitive fields scrubbed from logs?

### 3.4 Test Strategy Formulation
- Define the test cases required across the test pyramid:
  - **Unit tests**: Pure business logic, edge cases, zero-value conditions.
  - **Integration tests**: Database transactions, API route responses, error codes.
  - **Negative tests**: Invalid payloads, missing headers, unauthorized tokens.

---

## Phase 4: Implement

**Objective**: Write clean, modular, strictly typed, production-grade code that satisfies the planned specifications and adheres to `RULES.md`.

### 4.1 Strict Adherence to Engineering Laws
- Follow all rules in [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) (R-001 through R-180+):
  - **R-001/R-002**: No `TODO`, `FIXME`, or mock data in production paths.
  - **R-033/R-034**: Strict type checks; zero `any` or type bypasses.
  - **R-046**: Zero swallowed errors; typed custom exceptions.
  - **R-060/R-061**: Runtime boundary validation and 100% parameterized queries.
  - **R-142/R-144**: Structured JSON logging; zero sensitive PII in log lines.

### 4.2 Surgical Diff Discipline
- Modify only the lines and files strictly necessary for the task (R-015).
- Do not reformat unaffected code, reorder imports in untouched files, or perform unsolicited refactoring (R-016).
- Preserve existing comments, docstrings, and license headers (R-017).

### 4.3 Atomic Code Writing
- Deliver complete files without placeholders, omission markers (`// rest of code here`), or truncation (R-008).
- Verify file creation and modification using file viewing or inspection tools after each write (R-176).

---

## Phase 5: Test

**Objective**: Prove code correctness, safety, and regression resistance through rigorous, automated test execution.

### 5.1 Red-Green Verification (Bugfixes)
- For bug repairs, run the reproduction test *before* applying the fix to prove it fails (Red; R-005).
- Apply the fix and re-run to confirm the test succeeds (Green).

### 5.2 Deterministic Test Execution
- Run unit and integration tests using local test runners (`npm test`, `pytest`, `cargo test`).
- Ensure all tests are deterministic: zero arbitrary delays or `sleep()` calls (R-087).
- Verify that assertions test real state and return values (no tautological `expect(true).toBe(true)`; R-085).

### 5.3 Full Verification Suite Execution
- Execute the project-wide verification command:
  ```bash
  # Node.js
  npm run lint && npm run typecheck && npm test
  # Python
  ruff check . && mypy --strict . && pytest -v
  ```
- Inspect stdout and stderr to confirm exit code 0 and non-zero test assertions (R-004, R-175).

---

## Phase 6: Review

**Objective**: Conduct an adversarial self-audit against the 100-point ship gate rubric.

### 6.1 Definition of Done Scorecard Audit
- Evaluate the changes against [`DEFINITION_OF_DONE.md`](file:///home/agy/.t3/userdata/attachments/devskill/DEFINITION_OF_DONE.md):
  - Code Quality (20 pts)
  - Testing (20 pts)
  - Security (15 pts)
  - Performance (10 pts)
  - Documentation (10 pts)
  - Accessibility (10 pts)
  - Operations (10 pts)
  - Git Hygiene (5 pts)
- **Mandatory Ship Gate Rule**: Every single category must score ≥ 9/10 relative score, and the total score must be ≥ 95/100.

### 6.2 Automated CI Gate Pattern Scan
- Run the automated scan script from `RULES.md` §14 to detect:
  - `TODO` / `FIXME` / `HACK` markers
  - Mock or dummy data in production files
  - Raw `console.log` statements
  - `any` or `# type: ignore` directives
  - Hardcoded secret patterns or API keys

---

## Phase 7: Document

**Objective**: Ensure system documentation, API contracts, architectural records, and changelogs accurately reflect code reality.

### 7.1 Specifications & Architecture Records
- Update [`specs.md`](file:///home/agy/.t3/userdata/attachments/devskill/specs.md) if new entities, endpoints, or data models were introduced.
- Update [`decisions.md`](file:///home/agy/.t3/userdata/attachments/devskill/decisions.md) if an architectural decision or trade-off was evaluated.

### 7.2 Self-Documenting Code & Docstrings
- Add descriptive docstrings to public interfaces and classes explaining the *why* and any non-obvious design rationale.
- Maintain existing comments without stripping context (R-017).

### 7.3 Changelog & Commit Preparation
- Format git commit message adhering to Conventional Commits 1.0.0 (R-163):
  ```
  feat(auth): implement argon2id password hashing with schema validation
  ```
- Update `CHANGELOG.md` under the appropriate section (Added, Changed, Fixed, Security) if required.

---

## Phase 8: Report

**Objective**: Deliver a comprehensive, verifiable final report to stakeholders.

### 8.1 Final Delivery Report Assembly
- Assemble the mandatory report template defined in [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md#10-mandatory-final-report-format).
- Include:
  1. Executive Summary & Status (COMPLETED / BLOCKED).
  2. Table of Verified File Changes (Created / Modified paths).
  3. Table of Verification Evidence (Linter, Typecheck, Tests, Scan commands, exit codes, and output summaries).
  4. Definition of Done Scorecard Self-Assessment (All categories and total).
  5. Security & Threat Analysis.
  6. Next Steps & Recommended Actions.

---

## Systematic Debugging Protocol

When a bug, test failure, or unexpected behavior is detected, engineers and agents MUST follow the **7-Step Scientific Debugging Method**:

```
[1. REPRODUCE]  ──► [2. ISOLATE]    ──► [3. HYPOTHESIZE] ──► [4. PROBE]
 Create minimal      Trace failure       Formulate causal     Inspect runtime
 failing test        to single unit      mechanism            state & logs
                                                                   │
                                                                   ▼
[7. PREVENT]    ◄── [6. REGRESS]    ◄── [5. FIX]         ◄─────────┘
 Record pattern      Run full test       Apply minimal
 in MISTAKES.md      suite clean         surgical fix
```

### Step 1: Reproduce Deterministically
- Never attempt to fix a bug you cannot reliably reproduce.
- Write a minimal failing test case or curl reproduction script that triggers the exact failure.
- Confirm that the failure is deterministic (fails 100% of the time under specified conditions).

### Step 2: Isolate the Defect Boundary
- Trace the failure from the external boundary (HTTP response, UI error) backwards through the stack.
- Use binary search / divide-and-conquer on code branches to isolate the exact function, query, or state mutation causing the defect.
- Inspect structured logs and correlation IDs (`trace_id`).

### Step 3: Formulate Causal Hypotheses
- List plausible root causes:
  - Type coercion or unhandled null/undefined values.
  - Concurrency, race condition, or TOCTOU timing gaps.
  - Database schema mismatch, missing index, or uncommitted transaction.
  - Incorrect assumption regarding external API response shape.
- Rank hypotheses by likelihood.

### Step 4: Probe & Validate Hypothesis
- Add targeted assertions or inspect variable values at the point of failure.
- Verify whether the hypothesized condition actually exists before modifying logic.
- Avoid guessing or changing random lines of code hoping for a fix.

### Step 5: Apply Minimal Surgical Fix
- Make the smallest possible change that directly resolves the root cause.
- Adhere strictly to `RULES.md` (no hacks, no workarounds, no suppressing type errors).
- Do not refactor surrounding unaffected logic while applying a bugfix.

### Step 6: Verify & Regression Test
- Execute the reproduction test created in Step 1 to prove it now passes (Green).
- Run the entire test suite (`npm test`, `pytest`) to verify zero regressions across existing functionality.
- Run linters and typecheckers to guarantee code hygiene.

### Step 7: Prevent Recurrence (Post-Mortem)
- If the bug represents a recurring failure pattern or AI agent blind spot:
  - Add an entry to [`MISTAKES.md`](file:///home/agy/.t3/userdata/attachments/devskill/MISTAKES.md) detailing the pattern name, description, example, and automated guard.
  - If appropriate, add a static analysis rule (ESLint rule, Semgrep rule, or pre-commit regex) to prevent the pattern from ever returning.
