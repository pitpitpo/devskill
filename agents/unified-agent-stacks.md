# 🧩 Unified AI Coding Agent Stacks & Harness Architecture (`unified-agent-stacks.md`)

> **Standard Identifier**: `AGT-STACKS-001`  
> **Status**: Active / Production Standard (2026 Unified Synthesis)  
> **Synthesizes**: `pstack` (poteto), `tstack` (t3dotgg), `gstack` (Garry Tan), `kstack` (kubetail-org), `superpowers` (obra), `compound-engineering` (Every), `spec-kit` (GitHub), `Beads` / `Gas Town` (Steve Yegge), `BMad-METHOD`, and Harness Engineering  
> **Cross-References**: [`RULES.md`](../RULES.md) (`R-181`–`R-250`), [`agents/orchestrator.md`](orchestrator.md), [`agents/code-forensics-interrogation.md`](code-forensics-interrogation.md), [`agents/full-send-delivery.md`](full-send-delivery.md)

---

## 1. The Core Thesis: `Agent = Model + Harness + Institutional Memory`

In production software engineering, raw model intelligence is no longer the primary bottleneck. The bottleneck is **verification, context discipline, and workflow structure**.

The evolution of AI-assisted engineering moved through three layers:
1. **Prompt Engineering (2022–2024)**: Optimizing single-turn textual instructions.
2. **Context Engineering (2025)**: Curating the working memory window—progressive disclosure via `SKILL.md` / `AGENTS.md`, KV-cache-friendly static prefixes, scoped file retrieval, and pointer-based handoffs (`R-192`).
3. **Harness Engineering (2026)**: Treating the surrounding runtime—deterministic hooks, isolated git worktrees, live verifiers, multi-model reviewers, persistent repo task graphs, and post-task memory compounding—as first-class software infrastructure.

> **Operational Law**: A disciplined engineering harness with deterministic verification gates, isolated worktrees, and strict pre-code investigation consistently outperforms an unconstrained frontier model running in a loose chat loop.

---

## 2. Cross-Stack Capability Map (Complete Taxonomy)

DevSkill unifies the highest-leverage primitives from every major production agent stack so engineers and autonomous agents never suffer fragmented workflows:

| Stack / Framework | Primary Strength | Core Primitives Integrated into DevSkill | DevSkill Home |
| :--- | :--- | :--- | :--- |
| **`pstack`** (`backnotprop/pstack`, Lauren Tan / `@poteto`) | Rigorous investigation, anti-slop minimalism, scientific iteration | `/how` & `/why` read-only forensics, `/interrogate` stress-testing, `/architect` boundary settling, `/arena` competing candidates, `/swarm` parallel tracks, `/deslop` cleanup, hillclimbing, failed-theory rollback | [`poteto-discipline.md`](poteto-discipline.md), [`code-forensics-interrogation.md`](code-forensics-interrogation.md), [`arena-evaluator.md`](arena-evaluator.md), [`hillclimbing-optimization.md`](hillclimbing-optimization.md) |
| **`tstack`** (`t3dotgg/tstack`, Theo Browne) | End-to-end PR shipping, cross-provider model consensus, event-driven CI babysitting | `full-send` (autonomous to merge), `full-stop` (halt before merge for human approval), `council` (tri-model consensus), `sol-loop`, `babysit-pr` (`scripts/pr-wait.py`), `file-pr` (problem-first narrative), `takeover`, `modernize`, `leaving-pr-comments` | [`full-send-delivery.md`](full-send-delivery.md), [`multi-model-council.md`](multi-model-council.md), [`sol-loop.md`](sol-loop.md), [`pr-lifecycle-babysitting.md`](../workflows/pr-lifecycle-babysitting.md), [`pr-modernize-takeover.md`](../workflows/pr-modernize-takeover.md) |
| **`gstack`** (`garrytan/gstack`, Garry Tan / YC) | Virtual engineering org personas & founder-mode product-to-ship gates | `/office-hours` (6 forcing questions), `/plan-ceo-review` (4 explicit scope modes), `/plan-eng-review` (architecture/diagram/footgun lock), `/plan-design-review`, `/review`, `/qa` + `/browse` (live browser dogfooding -> regression test), `/ship`, `/retro` | [`code-forensics-interrogation.md`](code-forensics-interrogation.md), §3 below |
| **`kstack`** (`kubetail-org/kstack`) | Agentic Kubernetes cluster monitoring, forensics & 4-pillar auditing | `/cluster-status`, `/events`, `/investigate` (events + logs + metrics correlation), `/audit-security`, `/audit-network`, `/audit-cost`, `/audit-outdated`, zero-leak `/cleanup` & `/forget` | [`kstack-cluster-operations.md`](../sections/devops-infrastructure/kstack-cluster-operations.md) |
| **`superpowers`** (`obra/superpowers`, Jesse Vincent) | Meta-skill gating, worktree isolation & two-stage subagent review | Mandatory pre-action skill check, `using-git-worktrees` isolation, strict Red-Green-Refactor TDD, **Two-Stage Review** (1. Spec Compliance → 2. Code Quality) | §4 below, [`tdd-reproduction.md`](tdd-reproduction.md) |
| **`compound-engineering`** (`EveryInc`, Kieran Klaassen) | Institutional memory compounding across sessions | **5-Step Compound Loop** (`Brainstorm → Plan → Build → Review → Compound`), durable solution docs (`MISTAKES.md`, ADRs, `_coordination/`), autonomous `/lfg` span | §5 below |
| **Spec-Driven & Persistent Graph Harnesses** (`spec-kit`, `Beads` / `Gas Town`, `BMad-METHOD`) | Eliminating cross-session context amnesia & multi-agent coordination drift | **8-Phase SDD Pipeline**, **Stateless Agents + Stateful Repo Documents**, local dependency-tracked issue/task graph, KV-cache static prefix discipline, diff-centric auditing | §6 below, [`specs.md`](../specs.md), [`orchestrator.md`](orchestrator.md) |

---

## 3. `gstack` Virtual Engineering Organization Gates

When building product-facing features or architectural initiatives—not just fixing an isolated bug—run explicit role-separated passes so product assumptions, technical footguns, and UX defects are caught before code is written.

### 3.1 The 7-Stage Product-to-Ship Pipeline
```
/office-hours ──► /plan-ceo-review ──► /plan-eng-review ──► Build (TDD) ──► /review ──► /qa + /browse ──► /ship ──► /retro
```

### 3.2 Four Explicit Scope Modes (`/plan-ceo-review`)
Before implementing any feature request, declare the active scope posture explicitly so agents never silently over-build or under-build (`R-249`):
1. **Scope Expansion**: Redesign around the highest-leverage 10× user workflow; challenge the initial framing.
2. **Selective Expansion**: Hold the core deliverable tight, but accept 1–2 high-ROI adjacent improvements surfaced during review.
3. **Hold Scope** *(Default for production engineering tasks)*: Zero feature creep; maximize correctness, security, and operational rigor within the stated boundary.
4. **Scope Reduction**: Strip non-essential surfaces ruthlessly to hit an urgent deadline or de-risk a critical incident.

### 3.3 Engineering Lock-Down (`/plan-eng-review`)
Before writing code, lock down five concrete artifacts:
- **ASCII Data-Flow & State Diagram** (inputs, state transitions, storage writes, failure edges).
- **Explicit Invariants & Footgun Check** (concurrency races, N+1 queries, partial failures, authz boundaries).
- **Test Matrix** (unit, integration, negative/boundary paths, and live verification command).
- **Rollback Plan** (feature flag kill-switch or expand/contract migration reversibility).

### 3.4 Live Dogfooding & Regression Capture (`/qa` + `/browse`) & Sprint Reflection (`/retro`)
- **Live Verification**: Never trust mocked unit tests to prove UI, routing, or end-to-end user flows (`R-202`). Drive the running application directly, capture concrete evidence, and convert every bug discovered during manual/browser QA into an automated regression test before shipping.
- **Retrospective (`/retro`)**: After shipping a multi-PR milestone, aggregate real git metrics (commit count, revert/fixup ratio, CI failure causes, review round count) and convert recurring friction into permanent rules, linters, or harness hooks.

---

## 4. `superpowers` Discipline: Worktree Isolation & Two-Stage Review

### 4.1 Mandatory Pre-Action Skill Gate
Before writing code or running mutating commands, the agent MUST classify the task against [`ROUTING.md`](../ROUTING.md) and load the prescribed skill files (`R-190`). Skipping directly to implementation on non-trivial tasks is a protocol violation.

### 4.2 Git Worktree Isolation (`R-247`)
For any multi-file feature, speculative experiment, or parallel subagent swarm, isolate execution in a dedicated Git worktree rather than mutating the main working tree:
```bash
git worktree add ../wt-feature-xyz -b feat/feature-xyz origin/main
# Verify clean baseline inside worktree BEFORE editing
cd ../wt-feature-xyz && <run test command>
# Clean up deterministically after merge or abandonment
git worktree remove ../wt-feature-xyz
```
Worktree isolation prevents cross-task merge collisions, preserves clean `git diff` baselines, and enables safe parallel execution (`pstack /swarm`, `Gas Town`).

### 4.3 Two-Stage Subagent Review (`R-248`)
Never combine functional specification auditing and code-style nitpicking in a single review pass. Run two sequential, isolated reviewer passes:
1. **Stage 1 — Spec Compliance Review**: Compare the diff strictly against the written specification / acceptance criteria. Did the code build *everything requested* and *nothing unrequested*? If Stage 1 fails, fix spec drift immediately—do NOT waste tokens polishing code that solves the wrong problem.
2. **Stage 2 — Code Quality, Security & Architecture Review**: Only after Stage 1 passes, audit the diff for OWASP security defects, module depth, error handling, test rigor, and AI slop (`R-182`, `R-236`).

---

## 5. `compound-engineering`: The 5-Step Compound Loop (`R-250`)

Standard agent sessions are **ephemeral**: once the chat closes, hard-won debugging insights evaporate and the next session repeats the exact same mistake. Compound Engineering closes the loop:

```
1. Brainstorm (/office-hours, /interrogate)
       │
       ▼
2. Plan (/architect, /plan-eng-review, specs.md)
       │
       ▼
3. Build (Worktree + Red-Green TDD + Surgical Diffs)
       │
       ▼
4. Review (Two-Stage Review + /deslop + Council if high-stakes)
       │
       ▼
5. COMPOUND ──► Persist the non-obvious lesson into the repository!
```

### What MUST Be Compounded After Non-Trivial Fixes or Decisions
Every non-trivial bug, subtle library quirk, or architectural trade-off MUST leave behind **one durable, concise repo artifact**:
- **Recurring Failure Mode / Trap** → Append a structured root-cause + guardrail entry to [`MISTAKES.md`](../MISTAKES.md).
- **Architectural Trade-off** → Record an ADR in [`decisions.md`](../decisions.md) or `docs/adr/`.
- **Mechanical Invariant** → Encode it as an automated check in `scripts/ci-gate.sh`, `.claude/settings.json`, ESLint/Ruff, or an architectural fitness test (`R-244`) so future agents *cannot* reintroduce the defect.

> **Compounding Criterion**: *"Does this commit leave the repository easier and safer for the next engineer or agent than it was before?"*

---

## 6. Harness Engineering, `spec-kit`, `Beads` & Context Economics

### 6.1 Stateless Agents, Stateful Repository Artifacts (`Beads` / `BMad-METHOD`)
Treat every LLM context window as **ephemeral and stateless**. Never keep critical plans, dependency graphs, or progress state solely inside chat history:
- Persist active plans, task dependencies, and handoff state in lightweight repository files (`_coordination/STATUS.md`, `specs.md`, or a local issue graph).
- Shard large specifications by domain so each subagent reads only its exact slice (< 10–15% of context window).
- Hand off **file paths and line ranges** rather than pasting raw transcripts (`R-192`).

### 6.2 KV-Cache-Friendly Instruction Hierarchy
Modern LLM runtimes achieve massive latency and cost reductions via prompt prefix caching:
- Keep static repository laws (`AGENTS.md`, `CLAUDE.md`, `SKILL.md`, `RULES.md`) stable and free of volatile timestamps or dynamic status counters.
- Place dynamic task context, diffs, and tool outputs at the *end* of the prompt—never mutate the top system prefix mid-session.

### 6.3 8-Phase Spec-Driven Development (`spec-kit`)
For greenfield systems or complex cross-cutting epics, execute the full SDD chain:
`Constitution (RULES.md) → Specify (Problem & Given-When-Then) → Clarify (/interrogate) → Plan (/architect) → Checklist (Edge Cases & Security) → Tasks (Atomic DAG) → Analyze (Consistency Audit) → Implement (TDD + Prove-It-Works)`.

### 6.4 Diff-Centric Auditing
Conversational agent summaries frequently omit subtle changes or overstate verification. Humans and orchestrators MUST audit ground truth exclusively from:
1. `git status` and `git diff --stat` / `git diff`
2. Real CLI execution outputs with exit codes (`R-181`, `R-202`)
3. Failing-then-passing reproduction tests (`R-005`, `R-183`)

---

## 7. Quick-Reference Command & Mode Selector

| Situation | Recommended Protocol Stack | Primary Mode |
| :--- | :--- | :--- |
| Unfamiliar codebase or mysterious legacy behavior | `pstack` (`/how` + `/why`) | Read-only forensics & git archaeology before any edit |
| Ambiguous feature request or greenfield product | `gstack` (`/office-hours` + `/plan-ceo-review`) + `spec-kit` | Lock scope mode + 6 forcing questions + written spec |
| Complex refactor or contested architecture | `pstack` (`/architect` + `/arena`) + `superpowers` (Worktree) | Competing prototypes in isolated worktrees + Two-Stage Review |
| Bug fix or production regression | `pstack` (root cause) + `superpowers` (Red-Green TDD) + `compound` | Failing test first → minimal diff → compound into `MISTAKES.md` / linter |
| Ready-to-land PR (human wants final merge click) | `tstack` (`file-pr` + `full-stop` + `babysit-pr`) | Problem-first PR + event-driven CI watch → halt before merge |
| Ready-to-land PR (explicit autonomous merge authorized) | `tstack` (`full-send` + `council`) | 5-point Merge Gate + tri-model consensus on latest commit |
| Kubernetes outage, pod crashloop, or cluster audit | `kstack` (`/cluster-status` + `/investigate` + `/audit-*` + `/cleanup`) | Read-only forensics → correlated root cause → zero leaked debug resources |

---

## 8. Verification Checklist

- [ ] Task classified against [`ROUTING.md`](../ROUTING.md) before modifying source files (`R-190`).
- [ ] Scope mode declared explicitly (`Expansion`, `Selective`, `Hold`, or `Reduction`) for non-trivial features (`R-249`).
- [ ] Isolated Git worktree used for parallel tracks or speculative explorations (`R-247`).
- [ ] Two-Stage Review completed: Spec Compliance passed BEFORE Code Quality polish (`R-248`).
- [ ] Failed exploratory theories reverted cleanly before final diff (`R-246`).
- [ ] Non-obvious lessons compounded into `MISTAKES.md`, ADRs, or automated lint/CI checks (`R-250`).
