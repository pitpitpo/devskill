# 🔁 The Ralph Loop & Non-Stop Reconciler Protocol (`agents/ralph-reconciler-loop.md`)

> **Standard Identifier**: `AGENT-RALPH-RECONCILER-001`  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, LLM Orchestrator Engines, Background Subagents, Harness Developers  
> **Classification**: Level 5 Non-Stop Execution Standard  
> **Origin**: Geoffrey Huntley's Ralph Wiggum Loop Technique (`"Ralph is a Bash loop"`) & Control Theory Reconciler Patterns  
> **Last Updated**: 2026-11-17

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/ralph-reconciler-loop.md` |
| **Capability Archetypes** | Autonomous Reconciler Loop, Non-Stop Execution, Git-Backed Task Progress, Fresh-Context Iteration |
| **Trigger Phrases** | `"ralph loop"`, `"run until finished"`, `"no stop"`, `"loop until done"`, `"reconcile to completion"` |
| **Governing Rules** | [`RULES.md`](../RULES.md) (R-001 No TODOs, R-004 Anti-Fake Green, R-181 Zero Hallucinated Commands, R-201 5-Point Gate, R-215 Non-Stop Reconciler Invariant) |
| **Prerequisites** | Shell CLI execution (`bash`), Git repository, project task backlog (`IMPLEMENTATION_PLAN.md` or `prd.json`), test runner |

In standard interactive sessions, AI agents suffer from **context rot and conversational degradation**: as tokens accumulate, models lose prompt instructions, hallucinate phantom implementations, or stop prematurely with conversational excuses ("It should work now!").

The **Ralph Loop Protocol** replaces ephemeral conversational context with **persistent disk state and Git checkpoints**. By treating LLM context like volatile memory (`malloc`/`free`) and the repository as durable memory, the agent executes in a continuous loop—either via outer shell iteration or internal tool recursion—until every task is completed, proven with Exit Code 0, and committed.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of the Ralph Reconciler**:
> *"Ralph is a Bash Loop. Context is Ephemeral; The Codebase and Git are Persistent Memory."*  
> An agent running under the Ralph protocol is **strictly forbidden from stopping** until all tasks in the implementation plan are satisfied, validated with passing tests, and committed. It is not allowed to say "it should work now" or ask the user to verify its code. The loop terminates ONLY when the stop condition (`<promise>COMPLETE</promise>` and Exit Code 0) is satisfied.

### The Five Invariants of the Ralph Loop

1. **`non-stop-reconciler` Invariant**: When an instruction is given, the agent MUST NOT yield execution back to the user while tasks remain uncompleted, failing tests exist, or compiler errors persist.
2. **`file-backed-state` Invariant**: All progress, pending tasks, defect logs, and decisions MUST be written to disk (`IMPLEMENTATION_PLAN.md` or `scratchpad.md`). The agent never relies on conversational memory across turns.
3. **`fresh-iteration-cleanliness` Invariant**: Each cycle reads the state directly from the filesystem and `git log`. If a step breaks the build, the next iteration observes the failure on disk and applies immediate corrective surgery.
4. **`atomic-commit-checkpoints` Invariant**: Each completed subtask MUST conclude with a passing test suite and an atomic Git commit (`git commit -m "feat/fix: ..."`). Failed experiments MUST be cleanly reverted (`git reset --hard`) before the next attempt.
5. **`hard-exit-condition` Invariant**: The agent may ONLY terminate its execution when the entire verification matrix (unit, integration, lint, strict typecheck) exits with code 0 and all checklist items are marked `[x]`.

---

## 3. Architecture & Design Patterns

```
                         THE RALPH RECONCILER STATE MACHINE
                         
                ┌───────────────────────────────────────────────┐
                │ 1. INITIALIZATION & BACKLOG INGESTION         │
                │    Inspect IMPLEMENTATION_PLAN.md / prd.json │
                │    Identify highest-priority pending task [ ] │
                └───────────────────────┬───────────────────────┘
                                        │
                                        ▼
    ┌───► ┌─────────────────────────────────────────────────────────────┐
    │     │ 2. TDD REPRODUCTION & PROBE                                 │
    │     │    Write failing reproduction test for selected item.       │
    │     │    Run test -> Prove failure (Exit Code != 0).             │
    │     └─────────────────────────────┬───────────────────────────────┘
    │                                   │
    │                                   ▼
    │     ┌─────────────────────────────────────────────────────────────┐
    │     │ 3. SURGICAL CODE EDIT (`unslop`)                            │
    │     │    Apply minimal diff to satisfy the specific invariant.    │
    │     │    Zero comment sermons, zero speculative refactors.       │
    │     └─────────────────────────────┬───────────────────────────────┘
    │                                   │
    │                                   ▼
    │     ┌─────────────────────────────────────────────────────────────┐
    │     │ 4. DIRECT VERIFICATION GATE                                 │
    │     │    Run test runner + strict typechecker + linter.           │
    │     └─────────────────────────────┬───────────────────────────────┘
    │                                   │
    │                 ┌─────────────────┴─────────────────┐
    │                 ▼                                   ▼
    │          [Exit Code != 0]                    [Exit Code == 0]
    │                 │                                   │
    │                 ▼                                   ▼
    │      Analyze failure on disk.             ┌───────────────────────────────────┐
    │      Rollback dirty state if              │ 5. ATOMIC COMMIT & PLAN UPDATE    │
    │      hopelessly corrupted.                │    git commit -m "..."            │
    │      Loop back to Step 2/3.               │    Mark task [x] in PLAN.md       │
    │                                           └─────────────────┬─────────────────┘
    │                                                             │
    │                                                             ▼
    │                                           ┌───────────────────────────────────┐
    └───────────────────────────────────────────┤ Are there remaining items in     │
                     YES                        │ IMPLEMENTATION_PLAN.md?           │
                                                └─────────────────┬─────────────────┘
                                                                  │ NO
                                                                  ▼
                                                ┌───────────────────────────────────┐
                                                │ 6. FINAL PROOF & EMIT STOP TOKEN  │
                                                │    Run full regression test suite.│
                                                │    Emit: <promise>COMPLETE</promise>│
                                                └───────────────────────────────────┘
```

### 3.1 Headless Harness vs. Agent-Native Loop

The Ralph Loop functions in two complementary modes:

* **Outer Harness Loop (Shell / CI Level)**: An external bash script continuously invokes the agent binary (`cursor-agent`, `claude`, `amp`, or custom runner) with a clean context window until a completion sentinel is emitted.
* **Inner Agent Loop (Session / Tool Level)**: Within a tool-capable agent harness (such as T3 Code / Antigravity), the agent internally maintains the reconciler loop across multiple tool calls without returning control to the user until all verification gates pass.

---

## 4. Concrete Code Examples

### 4.1 Production Ralph Loop Shell Script (`ralph.sh`)

```bash
#!/usr/bin/env bash
# Production Ralph Loop Orchestration Script
set -euo pipefail

PLAN_FILE="IMPLEMENTATION_PLAN.md"
MAX_ITERATIONS=${MAX_ITERATIONS:-50}
ITERATION=0
SENTINEL="<promise>COMPLETE</promise>"

if [ ! -f "$PLAN_FILE" ]; then
  echo "[-] ERROR: Missing $PLAN_FILE. Create the task backlog first."
  exit 1
fi

echo "[+] Starting Ralph Loop for: $(pwd)"
echo "[+] Target backlog: $PLAN_FILE (Max iterations: $MAX_ITERATIONS)"

while [ "$ITERATION" -lt "$MAX_ITERATIONS" ]; do
  ITERATION=$((ITERATION + 1))
  echo ""
  echo "================================================================================"
  echo " Ralph Iteration #$ITERATION / $MAX_ITERATIONS"
  echo "================================================================================"

  # Check if all tasks in plan are complete
  if ! grep -q "\[ \]" "$PLAN_FILE"; then
    echo "[+] All tasks in $PLAN_FILE marked complete ([x])!"
    echo "[+] Running final verification gate..."
    npm test && npx tsc --noEmit
    echo "[+] Verification passed. Ralph Loop finished successfully."
    exit 0
  fi

  # Execute agent iteration with prompt piped or via CLI
  # Notice: Context is completely fresh on each run; memory is in Git and PLAN_FILE
  AGENT_OUTPUT=$(cursor-agent --non-interactive --prompt "
You are running under the Ralph Reconciler Loop.
1. Read $PLAN_FILE and git status.
2. Select the FIRST unchecked task [ ].
3. Implement it with minimal surgical diffs.
4. Execute test suites and typecheckers to verify it.
5. If tests pass: commit changes to git, mark the task [x] in $PLAN_FILE.
6. If tests fail: inspect errors and fix them. Do NOT stop until tests pass.
7. If ALL tasks are finished, output: $SENTINEL.
" 2>&1 | tee /dev/stderr)

  # Check for completion token
  if echo "$AGENT_OUTPUT" | grep -q "$SENTINEL"; then
    echo "[+] Sentinel $SENTINEL detected in output."
    echo "[+] Verifying clean working tree and tests..."
    npm test && npx tsc --noEmit
    echo "[+] Complete! Ralph successfully satisfied all specifications."
    exit 0
  fi

  # Safeguard against hanging dirty state
  if [ -n "$(git status --porcelain)" ]; then
    echo "[!] Warning: Working tree dirty after iteration. Running test gate..."
    if ! npm test; then
      echo "[-] Tests broken on dirty tree. Reverting uncommitted broken changes..."
      git checkout -- .
    fi
  fi
done

echo "[-] ERROR: Ralph Loop reached max iterations ($MAX_ITERATIONS) without completion."
exit 1
```

### 4.2 Standard Task Specification File (`IMPLEMENTATION_PLAN.md`)

```markdown
# 📋 Autonomous Implementation Plan

> **Instructions for Agent**: Read this file on every iteration. Pick the top-most unchecked task `[ ]`. Implement it, run tests, commit to git, and update `[ ]` to `[x]`. Never mark an item `[x]` without exit code 0 test proof.

### Backlog

- [ ] **Task 1: Model Schema Definition**
  - Implement Zod schema for `UserProfile` in `src/types/user.ts`.
  - Add unit tests in `tests/types/user.test.ts`.
  - Verify with `npm test tests/types/user.test.ts` (Exit Code 0).

- [ ] **Task 2: Repository Persistence Layer**
  - Implement PostgreSQL query mapper in `src/repo/user-repo.ts`.
  - Add integration tests using Testcontainers in `tests/repo/user-repo.test.ts`.
  - Verify with `npm test tests/repo/user-repo.test.ts` (Exit Code 0).

- [ ] **Task 3: REST API Controller & Route Handlers**
  - Expose `/api/v1/users` endpoint in `src/routes/users.ts`.
  - Enforce authentication middleware and rate-limiting.
  - Verify with `npm test tests/routes/users.test.ts` (Exit Code 0).

- [ ] **Task 4: Full Quality Gate & Regression Scan**
  - Run full test suite: `npm test`.
  - Run typecheck: `npx tsc --noEmit`.
  - Run linter: `npx biome check src/`.
  - Emit `<promise>COMPLETE</promise>`.
```

---

## 5. Security & Performance Considerations

| Dimension | Risk / Vulnerability | Ralph Loop Protocol Mitigation |
|---|---|---|
| **Infinite Tool Loops** | Agent cycling on identical failing syntax errors indefinitely | Outer harness enforces `MAX_ITERATIONS` (default 50). Inner loop enforces exponential backoff or git reset if 3 consecutive iterations fail on identical error signatures. |
| **Silent Failures & Fake Commits** | Agent commits failing code just to check off `[x]` | Rule R-004 (`Anti-Fake Green`): Commit commands MUST be conditioned on shell test status: `npm test && git commit -am "..."`. |
| **Token Cost Explosion** | Dumping huge files repeatedly into fresh agent context | Agents must load target files with line-bounded slices (`StartLine`, `EndLine`), not full repository dumps. |
| **Destructive Commands** | Headless agent running `git clean -fdx` or dropping tables | Prohibit destructive commands via sandbox policy or pre-flight shell linter. |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Manifestation | Root Cause | Remediated Behavior |
|---|---|---|---|
| **The "Try This" Surrender** | Agent stops and asks the user: "Please run `npm test` and let me know." | Premature termination default | Forbid termination while shell tools are available. Agent MUST run the command itself. |
| **Premature Checklist Marking** | Marking `[x]` in `IMPLEMENTATION_PLAN.md` before tests pass | Sycophancy / token optimization | Mark `[x]` ONLY in the same step as a passing test run and git commit. |
| **Context Leaking Across Tasks** | Agent keeps all conversation history from Task 1 when starting Task 10 | Monolithic session decay | Wipe context or reset subagent state per task; read current progress exclusively from git and disk. |
| **Uncommitted Drift** | Multiple tasks implemented on a dirty tree without intermediate commits | Lazy git hygiene | Enforce 1 atomic git commit per checkbox item. Clean git trees are mandatory before picking next task. |

---

## 7. Verification Checklist

Before an agent operating under the Ralph Loop may declare completion:

- [ ] **Zero Remaining Backlog**: All items in `IMPLEMENTATION_PLAN.md` are marked `[x]`.
- [ ] **Clean Working Tree**: `git status --porcelain` is empty (all changes committed).
- [ ] **Strict Typecheck**: Strict compiler passes with 0 errors (`tsc --noEmit`, `mypy --strict`, or `cargo check`).
- [ ] **Full Regression Suite**: All test suites pass cleanly with exit code 0 (`npm test`, `pytest`, or `go test ./...`).
- [ ] **Linter / Formatter**: Zero warnings or errors under repository linter.
- [ ] **Sentinel Emitted**: Final output contains the explicit completion promise `<promise>COMPLETE</promise>`.
