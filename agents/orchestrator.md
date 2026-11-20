# 🎼 Autonomous Agent Orchestrator Skills (`agents/orchestrator.md`)

> **Classification**: Multi-Agent Orchestration Engine, Distributed Workflow Execution & Autonomous Systems Architecture  
> **Target Audience**: Lead Orchestrator Agents, Autonomous Swarm Controllers, System Architects, and Platform Engineers  
> **Inspirations**: Google Borg & Kubernetes Reconciler, Temporal.io & Uber Cadence Durable Execution, Netflix Conductor & AWS Step Functions DAGs, OpenAI Swarm Handoffs, LangGraph State Machines, Stripe Distributed Systems (Martin Kleppmann Fencing Tokens), Anthropic Multi-Agent Patterns, and MetaGPT Dialectic Consensus  
> **Core Objective**: Prescribe production-grade orchestration standards for partitioning, dispatching, monitoring, fencing, and synthesizing multi-agent execution graphs with zero hallucination, zero context starvation, and zero runaway execution loops.

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Skill Name** | `agent-orchestration-engine` |
| **Applicability Scope** | Multi-Agent Coordination, Parallel Worker Management, Hierarchical Task Decomposition, Distributed Saga Transactions, Reconciler State Convergence |
| **Prerequisites** | [`agents.md`](../agents.md), [`agents/poteto-discipline.md`](poteto-discipline.md), [`agents/arena-evaluator.md`](arena-evaluator.md), [`ROUTING.md`](../ROUTING.md), [`RULES.md`](../RULES.md) |
| **Governing Rules** | **R-001** (Zero TODOs), **R-015** (Surgical diffs), **R-181** (Prove-it-works), **R-187** (Jittered backoff), **R-188** (Task lifecycle ownership), **R-191** to **R-200** (Orchestrator Invariants) |
| **Version Standard** | SemVer 2.0.0 (Production Enterprise Standard) |
| **Last Updated** | 2026-11-17 (Frontier Labs & Big Tech Synthesis) |

---

## 2. Core Philosophy / Golden Rule

> **The Lead Orchestrator Never Implements; It Partitions, Budgets, Dispatches, Fences, Reconciles, and Synthesizes.**
> 
> *An orchestrator that writes application code directly loses its objective vantage point, pollutes its primary context window with implementation syntax, and triggers cascade hallucinations. An elite orchestrator operates as an air-traffic controller: maintaining the master DAG, managing cryptographic task leases, dispatching isolated child subagents with strict pointer references, and verifying execution proofs before marking any node complete.*

---

## 3. Architecture & Orchestration Topologies (Big Tech & Open Source Blueprints)

Production-grade multi-agent architectures draw from five battle-tested distributed computing patterns:

### Pattern 1: Hierarchical Supervisor-Worker (Anthropic & OpenAI Swarm)
A single Lead Supervisor maintains the high-level roadmap, partitions work into disjoint sub-scopes, delegates tasks to ephemeral, role-specialized worker agents, and receives structured execution artifacts.

```
                         ┌─────────────────────────────┐
                         │      LEAD ORCHESTRATOR      │
                         │   (Context: Roadmap & DAG)  │
                         └──────────────┬──────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
  │  RESEARCH WORKER    │    │ IMPLEMENTER WORKER  │    │  QA / AUDIT WORKER  │
  │ (Read-Only Sandbox) │    │ (Isolated Worktree) │    │ (Test Harness Gate) │
  └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
             │                          │                          │
             └──────────────────────────┼──────────────────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   STRUCTURED ARTIFACT BUS   │
                         │ (JSON Pointers & Git SHAs)  │
                         └─────────────────────────────┘
```

### Pattern 2: Kubernetes / Borg Reconciler Loop (Google SRE)
Instead of reacting blindly to ephemeral events, the orchestrator executes a continuous control loop comparing the **Observed State** ($S_{\text{observed}}$) against the **Desired State** ($S_{\text{desired}}$) defined in the task specification, applying idempotent mutations until convergence ($S_{\text{observed}} \equiv S_{\text{desired}}$).

```
   ┌────────────────────────────────────────────────────────┐
   │                                                        │
   ▼                                                        │
┌──────────────────┐     ┌──────────────────┐     ┌─────────┴────────┐
│ 1. OBSERVE       │ ──► │ 2. DIFF & PLAN   │ ──► │ 3. RECONCILE     │
│ Read files, git  │     │ Compute delta:   │     │ Execute surgical │
│ status, test runs│     │ Desired - Actual │     │ subagent action  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Pattern 3: Temporal.io / Cadence Durable Saga Orchestration (Uber & AWS)
Multi-step operations across heterogeneous services (e.g., database migration + API refactor + frontend sync) are executed as a **Saga**. If step $N$ fails after steps $1 \dots N-1$ succeed, the orchestrator triggers reverse **Compensating Transactions** ($C_{N-1} \dots C_1$) to guarantee atomic system consistency without dangling half-baked states.

```
Forward Flow:    [Step 1: DB Schema] ──► [Step 2: API Route] ──► [Step 3: UI Component] (FAILS ❌)
                                                                            │
Rollback Flow:   [Undo Step 1]       ◄── [Undo Step 2]       ◄──────────────┘
                 (Rollback Migration)    (Revert Route Diff)
```

### Pattern 4: LangGraph / Step Functions Dynamic DAG Engine (Netflix & AWS)
Task nodes with explicit dependencies are resolved via **Topological Sorting**. Independent tasks run concurrently up to a concurrency limit ($K$), while dependent tasks block until all prerequisite outputs are cryptographically verified.

```
       ┌──────────────┐
       │ Task A: Plan │
       └──────┬───────┘
              │
       ┌──────┴──────┐
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│ Task B: API │ │ Task C: Doc │  (Concurrent Fan-Out, K=2)
└──────┬──────┘ └──────┬──────┘
       │               │
       └──────┬────────┘
              ▼
       ┌──────────────┐
       │ Task D: E2E  │  (Join Barrier: Awaits B & C)
       └──────────────┘
```

### Pattern 5: Dialectic Multi-Agent Debate & Arbiter (MetaGPT & AutoGen)
For critical architectural decisions, security audits, or performance tradeoffs, the orchestrator convenes an adversarial debate between two peer agents:
- **Agent A (Proposer / Pentester)**: Formulates the design or attacks vulnerabilities.
- **Agent B (Architect / Arbiter)**: Defends production constraints, cost ceilings, and maintainability.
- **Orchestrator**: Weighs evidence against a mathematical scorecard and issues a binding final verdict.

---

## 4. Concrete Production Code & Orchestrator Implementation

### 4.1 Production-Grade TypeScript DAG Orchestration Engine

The following implementation provides a complete, strongly-typed, dependency-graph execution engine with cycle detection, concurrency-bounded worker pooling, Martin Kleppmann fencing tokens, and Saga compensation rollbacks.

```typescript
/**
 * @file Enterprise Multi-Agent DAG Orchestrator & Saga Engine
 * @description Production-grade orchestrator implementing topological resolution,
 * concurrency pooling, lease fencing, and backward compensation.
 */

import { randomUUID } from "node:crypto";
import { EventEmitter } from "node:events";

export type TaskStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "COMPENSATING" | "COMPENSATED";

export interface TaskContext {
  readonly executionId: string;
  readonly fencingToken: number;
  readonly workspaceRoot: string;
  readonly artifactStore: Map<string, unknown>;
  log(message: string, metadata?: Record<string, unknown>): void;
}

export interface TaskDefinition<TInput = unknown, TOutput = unknown> {
  readonly id: string;
  readonly name: string;
  readonly dependencies: readonly string[];
  readonly timeoutMs: number;
  readonly execute: (ctx: TaskContext, input?: TInput) => Promise<TOutput>;
  readonly compensate?: (ctx: TaskContext, output?: TOutput, error?: Error) => Promise<void>;
}

export interface ExecutionResult {
  readonly executionId: string;
  readonly success: boolean;
  readonly completedTasks: readonly string[];
  readonly failedTaskId?: string;
  readonly outputs: ReadonlyMap<string, unknown>;
  readonly durationMs: number;
}

export class AgentOrchestrationEngine extends EventEmitter {
  private fencingEpoch = 0;
  private readonly maxConcurrency: number;
  private readonly workspaceRoot: string;

  constructor(options: { maxConcurrency?: number; workspaceRoot: string }) {
    super();
    this.maxConcurrency = options.maxConcurrency ?? 4;
    this.workspaceRoot = options.workspaceRoot;
  }

  /**
   * Generates a strictly monotonically increasing fencing token.
   * Prevents split-brain state overwrite by delayed or zombie worker agents.
   */
  public allocateFencingToken(): number {
    return ++this.fencingEpoch;
  }

  /**
   * Topologically validates the task graph to guarantee absence of circular deadlocks.
   */
  public validateAcyclic(tasks: readonly TaskDefinition[]): readonly string[] {
    const adj = new Map<string, string[]>();
    const inDegree = new Map<string, number>();

    for (const task of tasks) {
      adj.set(task.id, []);
      inDegree.set(task.id, 0);
    }

    for (const task of tasks) {
      for (const dep of task.dependencies) {
        if (!adj.has(dep)) {
          throw new Error(`Orchestration Graph Error: Task '${task.id}' depends on non-existent task '${dep}'.`);
        }
        adj.get(dep)!.push(task.id);
        inDegree.set(task.id, (inDegree.get(task.id) ?? 0) + 1);
      }
    }

    const queue: string[] = [];
    for (const [id, deg] of inDegree.entries()) {
      if (deg === 0) queue.push(id);
    }

    const sorted: string[] = [];
    while (queue.length > 0) {
      const u = queue.shift()!;
      sorted.push(u);

      for (const v of adj.get(u) ?? []) {
        inDegree.set(v, inDegree.get(v)! - 1);
        if (inDegree.get(v) === 0) {
          queue.push(v);
        }
      }
    }

    if (sorted.length !== tasks.length) {
      throw new Error("Orchestration Graph Error: Circular dependency detected in agent execution DAG.");
    }

    return sorted;
  }

  /**
   * Executes the full task graph with bounded concurrency and automatic Saga rollback.
   */
  public async executePlan(tasks: readonly TaskDefinition[]): Promise<ExecutionResult> {
    const startTime = Date.now();
    const executionId = randomUUID();
    this.validateAcyclic(tasks);

    const taskMap = new Map<string, TaskDefinition>(tasks.map((t) => [t.id, t]));
    const taskStates = new Map<string, TaskStatus>(tasks.map((t) => [t.id, "PENDING"]));
    const outputs = new Map<string, unknown>();
    const completedTasks: string[] = [];
    const runningTasks = new Set<Promise<void>>();

    const sharedContext: TaskContext = {
      executionId,
      fencingToken: this.allocateFencingToken(),
      workspaceRoot: this.workspaceRoot,
      artifactStore: new Map(),
      log: (msg, meta) => {
        this.emit("agent:log", { executionId, timestamp: new Date().toISOString(), msg, meta });
      },
    };

    let failureError: Error | undefined;
    let failedTaskId: string | undefined;

    const isReady = (task: TaskDefinition): boolean => {
      if (taskStates.get(task.id) !== "PENDING") return false;
      return task.dependencies.every((dep) => taskStates.get(dep) === "COMPLETED");
    };

    while (completedTasks.length < tasks.length && !failureError) {
      const eligible = tasks.filter((t) => isReady(t));

      if (eligible.length === 0 && runningTasks.size === 0) {
        if (completedTasks.length < tasks.length) {
          throw new Error("Orchestrator Deadlock: No tasks eligible to run and no active workers.");
        }
        break;
      }

      for (const task of eligible) {
        if (runningTasks.size >= this.maxConcurrency) break;

        taskStates.set(task.id, "RUNNING");
        this.emit("task:start", { executionId, taskId: task.id, name: task.name });

        const taskPromise = (async () => {
          try {
            const timeoutPromise = new Promise<never>((_, reject) =>
              setTimeout(() => reject(new Error(`Timeout: Task ${task.id} exceeded limit of ${task.timeoutMs}ms`)), task.timeoutMs)
            );

            const result = await Promise.race([task.execute(sharedContext, outputs.get(task.dependencies[0])), timeoutPromise]);

            outputs.set(task.id, result);
            taskStates.set(task.id, "COMPLETED");
            completedTasks.push(task.id);
            this.emit("task:complete", { executionId, taskId: task.id });
          } catch (err) {
            taskStates.set(task.id, "FAILED");
            failedTaskId = task.id;
            failureError = err instanceof Error ? err : new Error(String(err));
            this.emit("task:failed", { executionId, taskId: task.id, error: failureError });
          }
        })();

        runningTasks.add(taskPromise);
        taskPromise.finally(() => runningTasks.delete(taskPromise));
      }

      if (runningTasks.size > 0) {
        await Promise.race(runningTasks);
      }
    }

    // Trigger Saga Compensating Transactions if failure occurred
    if (failureError && failedTaskId) {
      sharedContext.log(`Triggering Saga Rollback. Failed Task: ${failedTaskId}. Reason: ${failureError.message}`);
      this.emit("saga:compensating", { executionId, failedTaskId });

      // Rollback in reverse order of completion
      for (let i = completedTasks.length - 1; i >= 0; i--) {
        const taskIdToRollback = completedTasks[i];
        const taskDef = taskMap.get(taskIdToRollback);
        if (taskDef?.compensate) {
          taskStates.set(taskIdToRollback, "COMPENSATING");
          try {
            await taskDef.compensate(sharedContext, outputs.get(taskIdToRollback), failureError);
            taskStates.set(taskIdToRollback, "COMPENSATED");
            this.emit("task:compensated", { executionId, taskId: taskIdToRollback });
          } catch (compErr) {
            sharedContext.log(`CRITICAL: Compensation failed for ${taskIdToRollback}`, {
              error: compErr instanceof Error ? compErr.message : String(compErr),
            });
          }
        }
      }

      return {
        executionId,
        success: false,
        completedTasks,
        failedTaskId,
        outputs,
        durationMs: Date.now() - startTime,
      };
    }

    return {
      executionId,
      success: true,
      completedTasks,
      outputs,
      durationMs: Date.now() - startTime,
    };
  }
}
```

---

### 4.2 Production-Grade Python Reconciler & State Machine (Google SRE / Borg Style)

The following Python reconciler implements the level-triggered **Control Loop**, continuously driving observed file/system state toward the defined goal state with jittered exponential backoffs.

```python
"""
Enterprise Reconciler Controller for Autonomous Agent Workflows.
Implements level-triggered state convergence with jittered exponential backoff.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, Optional, TypeVar

logger = logging.getLogger("agent.orchestrator.reconciler")


class ReconcileStatus(str, Enum):
    CONVERGED = "CONVERGED"
    PROGRESSING = "PROGRESSING"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DesiredState:
    file_path: str
    required_exports: tuple[str, ...]
    min_test_coverage: float
    must_compile: bool = True


@dataclass(frozen=True)
class ObservedState:
    file_exists: bool
    actual_exports: tuple[str, ...]
    actual_test_coverage: float
    compiles_cleanly: bool


@dataclass
class ReconcileResult:
    status: ReconcileStatus
    iterations: int
    delta_description: str
    elapsed_seconds: float


T = TypeVar("T")


class AutonomousReconciler:
    def __init__(
        self,
        max_iterations: int = 10,
        base_backoff_ms: float = 200.0,
        max_backoff_ms: float = 5000.0,
    ) -> None:
        self.max_iterations = max_iterations
        self.base_backoff_ms = base_backoff_ms
        self.max_backoff_ms = max_backoff_ms

    def compute_backoff(self, attempt: int) -> float:
        """Full jitter exponential backoff: Uniform(0, min(max_backoff, base * 2^attempt))."""
        ceiling = min(self.max_backoff_ms, self.base_backoff_ms * (2 ** attempt))
        return random.uniform(0, ceiling) / 1000.0

    def compute_delta(self, desired: DesiredState, observed: ObservedState) -> Optional[str]:
        """Calculates exact delta between desired and observed reality."""
        deltas: list[str] = []
        if not observed.file_exists:
            deltas.append(f"Target file '{desired.file_path}' does not exist on disk.")
        if not observed.compiles_cleanly:
            deltas.append("Source code contains compilation or typecheck errors.")
        missing_exports = set(desired.required_exports) - set(observed.actual_exports)
        if missing_exports:
            deltas.append(f"Missing required interface exports: {sorted(missing_exports)}")
        if observed.actual_test_coverage < desired.min_test_coverage:
            deltas.append(
                f"Test coverage ({observed.actual_test_coverage:.1f}%) below required threshold ({desired.min_test_coverage:.1f}%)"
            )

        if not deltas:
            return None
        return "; ".join(deltas)

    def reconcile_loop(
        self,
        desired: DesiredState,
        observe_fn: Callable[[DesiredState], ObservedState],
        mutate_fn: Callable[[DesiredState, str], None],
    ) -> ReconcileResult:
        """
        Executes the continuous control loop until convergence or iteration exhaustion.
        """
        start_time = time.monotonic()
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            observed = observe_fn(desired)
            delta = self.compute_delta(desired, observed)

            if delta is None:
                logger.info(f"Reconciliation converged at iteration {iteration}.")
                return ReconcileResult(
                    status=ReconcileStatus.CONVERGED,
                    iterations=iteration,
                    delta_description="State fully reconciled.",
                    elapsed_seconds=time.monotonic() - start_time,
                )

            logger.warning(f"[Attempt {iteration}/{self.max_iterations}] Delta detected: {delta}")

            # Apply surgical mutation
            try:
                mutate_fn(desired, delta)
            except Exception as exc:
                logger.error(f"Surgical mutation failed during reconciliation: {exc}", exc_info=True)

            sleep_duration = self.compute_backoff(iteration)
            time.sleep(sleep_duration)

        final_observed = observe_fn(desired)
        final_delta = self.compute_delta(desired, final_observed)
        return ReconcileResult(
            status=ReconcileStatus.FAILED,
            iterations=iteration,
            delta_description=final_delta or "Exceeded max iterations without verification.",
            elapsed_seconds=time.monotonic() - start_time,
        )
```

---

## 5. Safety, Fencing, Blast-Radius & Security Guardrails

Multi-agent swarms without rigorous boundaries suffer from race conditions, token starvation, and split-brain corruption. Orchestrators MUST enforce four non-negotiable boundaries:

### 5.1 Martin Kleppmann Fencing Tokens (Anti-Zombie Overwrites)
When multiple subagents operate concurrently, network latency or slow LLM generations can cause an earlier agent (Worker A) to finish *after* a successor agent (Worker B) has already executed. Without fencing, Worker A overwrites Worker B's newer work with stale data.

Every orchestrator lease MUST include a strictly monotonically increasing token:
```
Orchestrator Lease Token: Epoch 42
Worker A assigned Token 42.
Worker A stalls. Lease expires.
Orchestrator increments Epoch to 43.
Worker B assigned Token 43. Worker B writes state to Storage with Token 43.
Worker A awakens and attempts to write with Token 42.
Storage Engine REJECTS Token 42 (42 < 43: Stale Lease Violation).
```

### 5.2 Pointer-Based Context Budgeting (Zero-Tsunami Protocol)
Never pass raw conversation transcripts or multi-megabyte source files between parent and child agents. Context window bloat degrades reasoning speed, causes prompt truncation, and spikes inference costs.

- **Forbidden (Context Tsunami)**:
  `invoke_subagent("Here is the entire 80,000-token chat transcript and full code repo...")`
- **Mandatory (Pointer Handoff)**:
  `invoke_subagent("Execute Task B. Read inputs at _coordination/artifacts/task-b.json. Target file is src/service.ts. Report outputs to _coordination/results/task-b.json.")`

### 5.3 Blast-Radius Containment (Sandboxing Matrix)

| Worker Archetype | Filesystem Permissions | Network Permissions | Shell Capabilities |
|---|---|---|---|
| **Research Subagent** | Read-Only (`r--`) | Restricted (Internal Docs / Approved domains) | Read commands only (`find`, `grep`, `cat`) |
| **Implementer Subagent** | Isolated Git Worktree | No external outbound traffic | Build & compile tools only (`tsc`, `cargo build`) |
| **QA / Tester Subagent** | Read + Test Directories | Local loopback only (`localhost:8080`) | Test runners only (`pytest`, `npm test`) |
| **Security Auditor** | Read-Only (`r--`) | Offline | Static AST scanners (`semgrep`, `bandit`) |

### 5.4 Deadlock Detection in Cyclic Graphs
If a multi-agent debate or collaborative workflow requires cycles (e.g., Code $\rightarrow$ Review $\rightarrow$ Revise $\rightarrow$ Review), the orchestrator MUST enforce:
1. **Hard Iteration Ceiling**: Maximum 3 iterations of review-revise.
2. **Diminishing Diffs Metric**: Diffs between iterations $k$ and $k+1$ must decrease ($\Delta_{k+1} < \Delta_k$). If $\Delta$ increases, halt and escalate to human.
3. **Arbiter Tie-Breaker**: If no consensus is reached after 3 rounds, an independent Arbiter agent computes the [`arena-evaluator.md`](arena-evaluator.md) weighted score and dictates the decision.

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: The Monolithic Lead (Orchestrator as Implementer)
- **Violation**: The orchestrator attempts to write 500 lines of code, run 20 tests, and edit 8 files in its own primary conversation turn.
- **Consequence**: The orchestrator runs out of output tokens, truncates code, loses track of its high-level plan, and fails to verify its work.
- **Remediation**: The orchestrator delegates each component to a specialized subagent, verifying each subagent's exit codes and test outputs before proceeding.

### Anti-Pattern 2: Unbounded Parallel Fan-Out (Thundering Swarm)
- **Violation**: The orchestrator spawns 30 subagents simultaneously for a 30-file codebase refactor without a concurrency semaphore.
- **Consequence**: Exhausts local system RAM, trips LLM rate limits (`429 Too Many Requests`), and causes uncoordinated merge conflicts in Git.
- **Remediation**: Bound concurrency to $K \le 4$ workers using an explicit semaphore pool with full-jitter backoff retries.

### Anti-Pattern 3: The Silent Task Drop (Swallowed Failure)
- **Violation**: A subagent crashes, returns an empty string, or throws an unhandled exception, but the orchestrator marks the node "complete" and moves to the next step.
- **Consequence**: Downstream dependent tasks fail mysteriously, creating cascade failures that waste hundreds of thousands of tokens.
- **Remediation**: Explicitly validate subagent return codes, assertion counts, and output files. Any missing output must trigger retry or Saga rollback.

### Anti-Pattern 4: Unfenced Zombie Overwrite (Split-Brain)
- **Violation**: An orchestrator restarts an apparently stalled worker without invalidating its credentials or lease token.
- **Consequence**: The original worker awakens and writes obsolete or conflicting state over the replacement worker's fresh commits.
- **Remediation**: Assign monotonically increasing fencing tokens; reject any storage or file operation carrying a stale token.

---

## 7. Verification Checklist & Orchestrator Scorecard

Before marking an orchestrated multi-agent task complete, the orchestrator MUST evaluate its execution against the following 10-point scorecard:

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Acyclic Graph Integrity** | $0$ cycles in DAG | Topological sort validation pass |
| **2. Concurrency Bound** | $\le 4$ active workers | Worker pool capacity assertion |
| **3. Fencing Epoch Token** | Monotonically increasing | Verification that all commits/writes match current epoch |
| **4. Pointer-Based Payloads** | $100\%$ pointer handoffs | Prompt inspection (zero embedded multi-page files) |
| **5. Subagent Verification** | Exit code $0$ + non-zero assertions | Inspection of stdout/stderr for every subagent task |
| **6. Saga Rollback Ready** | Compensation defined for all writes | Dry-run compensation path for mutating actions |
| **7. Reconciler Convergence** | Desired $\equiv$ Observed | Diff evaluation showing 0 delta remaining |
| **8. Git Tree Cleanliness** | Clean working tree on target branch | `git status -s` returns 0 modified/untracked files |
| **9. Test Suite Green** | Non-zero passing tests | `npm test` or `pytest -v` exits with code 0 |
| **10. Zero Deferred Markers** | 0 TODO / FIXME / HACK | `git grep -EIn "(TODO\|FIXME\|HACK)"` returns 0 hits |

---

*See also*: [`./poteto-discipline.md`](./poteto-discipline.md) for minimal surgical diffs, [`./arena-evaluator.md`](./arena-evaluator.md) for multi-agent trade-off scoring, and [`../ROUTING.md`](../ROUTING.md) for task routing matrices.
