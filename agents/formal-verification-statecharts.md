# 📐 Formal Verification, Statecharts & TLA+ Invariant Checking (`agents/formal-verification-statecharts.md`)

> **Standard Identifier**: `AGENT-FORMAL-VERIFICATION-001`  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Distributed Systems Engineers, Protocol Architects, Core Platform Leads  
> **Classification**: Level 5 Formal Systems Verification Standard  
> **Origin**: Lauren Tan's `pstack` Formal Verification & Statechart Protocol (TLA+ / TLC Model Checker / Mermaid Statecharts)  
> **Last Updated**: 2026-11-18

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/formal-verification-statecharts.md` |
| **Capability Archetypes** | TLA+ Specification, Formal Invariant Model Checking, Shortest-Path Counterexample Isolation, Statechart Visualization |
| **Trigger Phrases** | `"formal verification"`, `"model check this race"`, `"prove this invariant"`, `"tla+"`, `"statechart"`, `"verify state machine"` |
| **Governing Rules** | [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) (R-003 Zero Assumptions, R-188 Goroutine/Task Ownership, R-199 Reconciler Desired-State, R-217 Formal Verification Invariants) |
| **Prerequisites** | Java runtime (JRE 17+), TLA+ tools (`tlc.jar` or CLI wrapper), Python/TypeScript runtime for trace parsing |

Unit and integration tests only verify the execution paths that an engineer or AI agent thought to write. In distributed systems, concurrent protocols, financial ledgers, and complex state machines, race conditions hide in non-deterministic thread interleavings and network re-orderings that traditional tests almost never hit.

The **Formal Verification & Statechart Protocol** provides exhaustive mathematical proof over bounded state spaces using TLA+ and TLC, extracting exact shortest-path counterexamples when an invariant breaks, and visualizing system state transitions as human-readable Mermaid statecharts.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Formal Verification**:
> *"A Test Proves the Presence of Bugs in Sampled Paths; Formal Verification Proves the Absence of Bugs Across the Entire Bounded State Space."*  
> When dealing with concurrent leases, distributed two-phase commits, payment state machines, or retry loops, do not guess whether a race condition exists. Model the system as state variables, define the safety invariants mathematically, and let the model checker explore every possible permutation of events.

### The Five Invariants of Formal Verification

1. **`falsifiable-invariant` Invariant**: A formal invariant that has never been observed failing proves nothing about the model. The agent MUST verify that mutating the rule or introducing a known bug causes TLC to fail with a valid counterexample trace.
2. **`grounded-symbol-mapping` Invariant**: Every variable, action, and state in the TLA+ specification MUST correspond 1:1 to concrete lines of source code in the production repository. Indivisible TLA+ steps must match atomic primitives in code.
3. **`shortest-path-counterexample` Invariant**: When an invariant is violated, the model checker MUST report the minimal sequence of transitions from initial state to violation, translated into plain, human-auditable engineering terminology.
4. **`finite-state-bounding` Invariant**: To prevent state space explosion, models MUST bound constants (e.g. `MaxRetries = 3`, `Clients = {c1, c2}`, `BufferLimit = 2`) while strictly preserving protocol concurrency semantics.
5. **`replayable-code-proof` Invariant**: When TLC surfaces a counterexample trace, the agent MUST replay the exact trace against the production codebase as an executable regression test to confirm the bug exists in reality.

---

## 3. Architecture & Design Patterns

```
                     FORMAL VERIFICATION & STATECHART PIPELINE
                     
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 1. BOUNDARY & PROPERTY DEFINITION                                      │
     │    Identify critical concurrent invariant (e.g., Mutual Exclusion,     │
     │    At-Most-Once Execution, Non-Negative Account Balance).              │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 2. TLA+ SPECIFICATION & CONFIGURATION                                  │
     │    Write SPEC.tla (Init, Next, Actions, Invariants).                   │
     │    Write SPEC.cfg (Constants, Specification, Invariants).              │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 3. TLC MODEL CHECKER EXECUTION                                         │
     │    Execute TLC over bounded state space.                               │
     │    TLC evaluates all reachable states (BFS state graph exploration).   │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                 [Invariant Broken!]             [All States Clean]
                         │                               │
                         ▼                               ▼
     ┌───────────────────────────────────────┐   ┌─────────────────────────────┐
     │ 4. EXTRACT SHORTEST COUNTEREXAMPLE    │   │ 5. GENERATE STATECHART      │
     │    Parse trace -> Translate to steps. │   │    Produce clean Mermaid    │
     │    Replay trace as real unit test.    │   │    state diagram showing    │
     │    Apply surgical fix to source code. │   │    valid protocol paths.    │
     └───────────────────┬───────────────────┘   └──────────────┬──────────────┘
                         │                                      │
                         ▼                                      ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 6. FINAL VERIFICATION SCORECARD                                        │
     │    TLC: 0 errors across N distinct states explored.                    │
     │    Embed Mermaid statechart and mathematical proof in final report.    │
     └────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Production Distributed Lease Specification (`DistributedLease.tla`)

```tla
----------------------- MODULE DistributedLease -----------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Nodes, MaxTime

VARIABLES holder, leaseExpires, currentTime, nodeState

vars == <<holder, leaseExpires, currentTime, nodeState>>

TypeOK ==
    /\ holder \in Nodes \cup {"None"}
    /\ leaseExpires \in 0..MaxTime
    /\ currentTime \in 0..MaxTime
    /\ nodeState \in [Nodes -> {"IDLE", "ACQUIRING", "HOLDING", "EXECUTING"}]

Init ==
    /\ holder = "None"
    /\ leaseExpires = 0
    /\ currentTime = 0
    /\ nodeState = [n \in Nodes |-> "IDLE"]

(* Node attempts to acquire lease if expired *)
AcquireLease(n) ==
    /\ currentTime >= leaseExpires
    /\ holder' = n
    /\ leaseExpires' = currentTime + 3
    /\ nodeState' = [nodeState EXCEPT ![n] = "HOLDING"]
    /\ UNCHANGED <<currentTime>>

(* Node executes critical section only while lease valid *)
ExecuteCritical(n) ==
    /\ holder = n
    /\ currentTime < leaseExpires
    /\ nodeState' = [nodeState EXCEPT ![n] = "EXECUTING"]
    /\ UNCHANGED <<holder, leaseExpires, currentTime>>

(* Clock tick advancing global time *)
TimeTick ==
    /\ currentTime < MaxTime
    /\ currentTime' = currentTime + 1
    /\ UNCHANGED <<holder, leaseExpires, nodeState>>

Next ==
    \/ \E n \in Nodes : AcquireLease(n)
    \/ \E n \in Nodes : ExecuteCritical(n)
    \/ TimeTick

(* CRITICAL SAFETY INVARIANT: At most one node executing critical section *)
MutualExclusion ==
    \A n1, n2 \in Nodes :
        (nodeState[n1] = "EXECUTING" /\ nodeState[n2] = "EXECUTING") => n1 = n2

=============================================================================
```

### 4.2 TLC Configuration File (`DistributedLease.cfg`)

```text
SPECIFICATION Init /\ [][Next]_vars
CONSTANTS
    Nodes = {n1, n2}
    MaxTime = 6

INVARIANT
    TypeOK
    MutualExclusion
```

### 4.3 Automated TLC Runner & Statechart Generator (`tla_checker.py`)

```python
#!/usr/bin/env python3
"""tla_checker.py: Runs TLC model checker and parses counterexamples into Mermaid."""

import subprocess
import sys
import re

def run_tlc(spec_name: str) -> None:
    print(f"[+] Launching TLC Model Checker on {spec_name}.tla...")
    cmd = ["java", "-XX:+UseParallelGC", "-jar", "tla2tools.jar", "-deadlock", f"{spec_name}.tla"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if "Model checking completed. No error has been found." in res.stdout:
        states = re.search(r"([0-9]+) distinct states found", res.stdout)
        count = states.group(1) if states else "all"
        print(f"[✓] PASSED: Formally verified across {count} distinct states. Invariants hold.")
        generate_clean_mermaid()
        sys.exit(0)
    elif "Error: Invariant" in res.stdout or "Error: Deadlock" in res.stdout:
        print("[!] INVARIANT VIOLATION DETECTED!")
        print(extract_counterexample(res.stdout))
        sys.exit(1)
    else:
        print(f"[-] TLC execution error:\n{res.stderr or res.stdout}")
        sys.exit(2)

def extract_counterexample(output: str) -> str:
    lines = output.splitlines()
    trace = []
    capture = False
    for line in lines:
        if "The behavior up to this point is:" in line or "Error:" in line:
            capture = True
        if capture:
            trace.append(line)
    return "\n".join(trace[:40])

def generate_clean_mermaid() -> None:
    mermaid = """```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> ACQUIRING : Request Lease [Clock >= Expiry]
    ACQUIRING --> HOLDING : Lease Granted [Holder = Node]
    HOLDING --> EXECUTING : Execute [Clock < Expiry]
    EXECUTING --> IDLE : Complete Work / Yield
    HOLDING --> IDLE : Expiry Tick [Clock >= Expiry]
```"""
    print("[+] Statechart generated:\n" + mermaid)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tla_checker.py <spec_name>")
        sys.exit(1)
    run_tlc(sys.argv[1])
```

---

## 5. Security & Performance Considerations

| Dimension | Risk / Vulnerability | Formal Verification Mitigation |
|---|---|---|
| **State Space Explosion** | Unbounded sets or integer ranges causing TLC to run out of RAM | Bound all collections (e.g. `Nodes = {n1, n2}`, `MaxRetries = 3`). Add symmetry sets (`SYMMETRY Permutations(Nodes)`) to fold identical state graphs. |
| **Deadlock False Positives** | Terminal end states flagged as deadlocks by TLC | Define a terminal stuttering action (`Done == phase = "COMPLETED" /\ UNCHANGED vars`) to satisfy `Next` in legitimate terminal states. |
| **Model-Code Drift** | Production code changes while formal specification remains static | Pin the source commit SHA inside the `.tla` header (`Confirmed against commit: 0f4bf60`). In CI, verify that diffs touching the target code trigger model re-checking. |
| **False Negative Proofs** | Vacuous truth where `Next` is never satisfied, resulting in 0 states checked | Assert that TLC explored $\ge 10$ distinct states. If state count is 1, the initial condition or `Next` step has a logic flaw. |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Manifestation | Root Cause | Remediated Behavior |
|---|---|---|---|
| **The Unbroken Spec** | Spec passes on the first try with 0 errors and 0 tests | Flawed invariant definition | Intentionally comment out a check in production code; verify TLC flags the violation with an exact counterexample. |
| **Weakening the Invariant** | Modifying `MutualExclusion` to allow overlap when TLC complains | Laziness / fear of defects | Never weaken the invariant. Fix the underlying protocol state machine in production code. |
| **Over-Modeling** | Modeling HTTP headers, string payloads, and UI buttons in TLA+ | Missing abstraction boundary | Model ONLY the core concurrent state transitions and invariants. Exclude serialization formatting. |
| **The Disconnected Model** | TLA+ specification uses variables completely different from production code | Lack of semantic grounding | Mirror exact variable and method names from the production source repository. |

---

## 7. Verification Checklist

Before declaring formal verification complete:

- [ ] **Grounded Variables**: All TLA+ state variables map to concrete production code symbols.
- [ ] **Falsification Test**: Invariant failed with a counterexample trace when mutated.
- [ ] **TLC Clean Pass**: TLC completed with 0 errors and explored $> 1$ distinct states.
- [ ] **Replay Unit Test**: Counterexample trace was successfully converted into an executable unit test.
- [ ] **Mermaid Statechart**: Clean, human-auditable state transition diagram generated.
- [ ] **Sync Commit Pinned**: Target source commit SHA recorded in specification header.
