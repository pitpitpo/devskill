# 🔁 Adversarial Single-Model Review Loop & Sol Protocol (`agents/sol-loop.md`)

> **Standard Identifier**: `AGENT-SOL-LOOP-001`  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Lead Orchestrator Subagents, Code Review Bots, Senior Engineers  
> **Classification**: Level 5 Adversarial Verification Standard  
> **Origin**: T3 Code / `tstack` Sol-Loop Pattern by Theo Browne & OpenAI GPT Sol Review Protocol  
> **Last Updated**: 2026-11-18

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/sol-loop.md` |
| **Capability Archetypes** | Single-Model Adversarial Review, Iterative Code Hardening, Scope-Creep Defense, Finding Ledger Governance |
| **Trigger Phrases** | `"sol loop"`, `"run sol loop"`, `"adversarial review loop"`, `"tight review cycle"` |
| **Governing Rules** | [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) (R-015 Minimal Diffs, R-182 Surgical Interventions, R-204 Scope-Creep Defense, R-216 Sol Review Ledger) |
| **Prerequisites** | Git repository, diff engine, strong reasoning model (OpenAI o1/o3-mini/Sol, Anthropic Claude Opus, or Gemini Pro), T3 Code orchestrator or CLI harness |

While the **Tri-Provider Model Council** ([`agents/multi-model-council.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/multi-model-council.md)) is reserved for high-stakes architectural pivots, schema migrations, and security consensus, day-to-day engineering requires a faster, tighter, and cost-effective review loop.

The **Sol Loop Protocol** deploys a single, highly critical reviewer model across iterative rounds with strict turn budgeting, an immutable findings ledger, and uncompromising resistance against review-induced scope creep.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of the Sol Loop**:
> *"Make the most minimal possible change to appease the reviewer. Never agree just to end the loop, and never let review findings inflate project scope."*  
> The lead agent's primary obligation during review is to defend the codebase against gratuitous refactors, unneeded edge-case guards, and speculative abstractions. Every finding must be checked against real code. If a finding is out of scope or an edge case callers will never hit, decline it with written evidence.

### The Five Invariants of the Sol Loop

1. **`strict-round-budget` Invariant**: Default budget is strictly **3 rounds**. Round 1 is full-file review; subsequent rounds review ONLY newly modified code and open findings. Extendable to **5 rounds** exclusively for auth, permissions, data-loss, or concurrency bugs.
2. **`immutable-finding-ledger` Invariant**: Every finding must receive a stable ID (`S1`, `S2`, `S3`), a triaged severity (`blocker`, `should`, `nit`), and a tracked outcome (`fixed:`, `disagree:`, `declined:`) with empirical code or test citations.
3. **`scope-creep-defense` Invariant**: The reviewer's job is to spot real bugs in the intended case. The agent MUST reject speculative edge-case guards, extra compatibility layers, or auxiliary utility functions.
4. **`surgical-remediation` Invariant**: When agreeing with a finding, prefer deleting code or narrowing types over adding new caches, locks, mutexes, helpers, or configuration flags.
5. **`falsifiable-test-proof` Invariant**: For every accepted `blocker` or `should` finding, the agent MUST write one focused reproduction test that fails without the fix and passes with it.

---

## 3. Architecture & Design Patterns

```
                          THE SOL REVIEW LOOP CYCLE
                          
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 1. SCOPE & BASELINE DETERMINATION                                      │
     │    Compute git merge-base against origin/main.                         │
     │    Isolate changed files; run baseline CI checks (tsc, tests, lint).   │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 2. ROUND 1: INITIAL ADVERSARIAL BRIEF                                  │
     │    Spawn read-only reviewer with exact diff, intent, and checks.       │
     │    Reviewer returns: VERDICT (APPROVE / CHANGES) + Stable IDs [S1, S2] │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 3. TRIAGE & ANSWER FINDINGS                                            │
     │    Evaluate each finding:                                              │
     │    - Agree: Apply minimal surgical fix + reproduction test.            │
     │    - Disagree: Provide counter-evidence (code link / test output).     │
     │    - Declined Nit: Log as follow-up; do NOT expand current diff.       │
     │    Update decision ledger.                                             │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                 [Open Blockers?]                 [No Blockers /
                 [Budget Remains?]                 Only Nits / Approved]
                         │                               │
                        YES                              │
                         ▼                               ▼
     ┌───────────────────────────────────────┐   ┌─────────────────────────────┐
     │ 4. SUBSEQUENT ROUND (Diff Delta Only) │   │ 5. STOP & SHIP              │
     │    Submit ONLY changed code & ledger. │   │    Verify zero diff bloat.  │
     │    Reviewer checks open IDs only.     │   │    Append review trailer.   │
     └───────────────────┬───────────────────┘   │    Hand off verified work.  │
                         │                       └─────────────────────────────┘
                         └───────────────────────►
```

### 3.1 Severity Tiers & Classification Matrix

| Severity | Definition | Mandatory Agent Action |
|---|---|---|
| **`blocker`** | The intended user case is broken, data is corrupted, or security is compromised. | **MUST FIX**: Apply minimal fix, add focused test, and trigger next review round. |
| **`should`** | Real bug that real callers will encounter under normal intended usage. | **MUST FIX OR PROVE UNREACHABLE**: Either fix surgically or provide executable proof that callers cannot trigger it. |
| **`nit`** | Style preferences, minor perf micro-optimizations, rare theoretical edge cases, or extra defensive guards. | **DECLINE OR DEFER**: Decline in one sentence; do NOT trigger a new review round for nits. |

---

## 4. Concrete Code Examples

### 4.1 Production Sol Loop Orchestration Script (`sol_loop_runner.py`)

```python
#!/usr/bin/env python3
"""sol_loop_runner.py: Production single-model adversarial review harness."""

from __future__ import annotations
import subprocess
import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class Finding:
    id: str
    severity: str  # blocker | should | nit
    file_path: str
    line: int
    claim: str
    outcome: str   # fixed | disagree | declined
    evidence: str

class SolLoopLedger:
    def __init__(self, base_sha: str, max_rounds: int = 3):
        self.base_sha = base_sha
        self.max_rounds = max_rounds
        self.current_round = 0
        self.findings: Dict[str, Finding] = {}

    def record_finding(self, finding: Finding) -> None:
        self.findings[finding.id] = finding

    def get_open_blockers(self) -> List[Finding]:
        return [f for f in self.findings.values() if f.severity in ("blocker", "should") and f.outcome != "fixed"]

    def export_summary(self) -> str:
        lines = [f"## Sol Loop Review Ledger (Rounds: {self.current_round}/{self.max_rounds})"]
        lines.append("| ID | Severity | File:Line | Outcome | Evidence / Rationale |")
        lines.append("|---|---|---|---|---|")
        for f in self.findings.values():
            lines.append(f"| {f.id} | `{f.severity}` | `{f.file_path}:{f.line}` | **{f.outcome}** | {f.evidence} |")
        return "\n".join(lines)

def run_cmd(cmd: str) -> str:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd}): {res.stderr}")
    return res.stdout.strip()

def get_merge_base() -> str:
    run_cmd("git fetch origin main")
    return run_cmd("git merge-base HEAD origin/main")

if __name__ == "__main__":
    base = get_merge_base()
    ledger = SolLoopLedger(base_sha=base, max_rounds=3)
    diff_stat = run_cmd(f"git diff --shortstat {base}")
    print(f"[+] Initialized Sol Loop on base: {base}")
    print(f"[+] Baseline diff: {diff_stat}")
```

### 4.2 Standard Prompt Template for Review Rounds

#### Round 1: Initial Adversarial Audit Prompt
```text
Review only. Do not edit, commit, push, comment on PRs, or start subagents.
Repository: /home/agy/.t3/userdata/attachments/project
Base Commit: 3a7f8b9 | Target Paths: src/services/billing/
Intent: Fix Stripe subscription proration webhook race condition.
Out of scope: Refactoring invoice PDF generator or tax calculation.

See: git diff 3a7f8b9 -- src/services/billing/
Read surrounding code. Find real bugs, broken callers, or intent mismatch.
Skip style unless it conceals a defect. Enforce the smallest possible change.
Flag code, tests, or defensive guards that the core intent does not need.
Severity definitions:
- blocker: The intended user case is wrong, race condition occurs, or data lost.
- should: Real bug that real callers will encounter in intended flow.
- nit: Rare edge case, minor perf, speculative guard, or style preference.

Reply format:
VERDICT: APPROVE or CHANGES
S1 [blocker|should|nit] src/services/billing/webhook.ts:45 <concise bug claim>. Fix: <minimal suggestion>
S2 [blocker|should|nit] src/services/billing/proration.ts:102 <concise bug claim>. Fix: <minimal suggestion>
```

#### Round 2+: Incremental Delta Review Prompt
```text
Round 2 Incremental Review.
Review ONLY the changes made since Round 1 and the open findings.
Base Diff: git diff 3a7f8b9..HEAD -- src/services/billing/

Previous Findings Ledger:
- S1 [blocker] webhook.ts:45 -> FIXED: Added idempotent database transaction lock. (Test: tests/webhook-race.test.ts passing).
- S2 [nit] proration.ts:102 -> DECLINED: Caller input is already validated by Zod at router boundary; duplicate guard adds unnecessary branch.

Check if S1 is genuinely resolved and confirm no regressions were introduced.
Reply format:
VERDICT: APPROVE or CHANGES
S1 [resolved | still open: <reason>]
```

---

## 5. Security & Performance Considerations

| Dimension | Risk / Vulnerability | Sol Loop Mandate |
|---|---|---|
| **Token Exhaustion & Context Rot** | Resending the entire codebase on rounds 2 and 3 | Send **only the delta diff** (`git diff HEAD~1..HEAD`) and the existing ledger. Do not re-transmit unchanged files. |
| **Review-Induced Diff Bloat** | Reviewer suggests 15 defensive wrappers and helpers, bloating the PR by 500 lines | Rule R-204: Reject defensive bloat. Check `git diff --shortstat` after every round. If diff expanded significantly, revert auxiliary changes. |
| **False-Positive Rubber-Stamping** | Agent agrees with hallucinated reviewer comments just to get an `APPROVE` verdict | Forbid fake fixes. If the reviewer claims a bug that doesn't exist, write an executable test proving it works and declare `disagree:`. |
| **Unbounded Review Cycles** | Agent and reviewer arguing indefinitely in an infinite loop | Hard cap of **3 rounds** (5 for auth/concurrency). If disputed after round 3, escalate directly to human lead. |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Manifestation | Root Cause | Remediated Behavior |
|---|---|---|---|
| **The Compliant Subordinate** | Agent mechanically applies every reviewer suggestion without verifying code validity | Lack of architectural spine | Check every finding against real code. Decline irrelevant nits in one sentence. |
| **The Stealth Refactor** | Reviewer suggests renaming a variable, and the agent reformats 300 lines | Lack of hunk containment | Apply edits exclusively to the single line containing the bug. Run `git diff` before committing. |
| **The Missing Ledger** | Findings addressed in code but lost in conversation memory | Ephemeral context drift | Record every finding in a persistent markdown table or `decision.tsv` ledger. |
| **Unneeded Guard Proliferation** | Adding `if (!obj) return;` to 10 functions where TypeScript already guarantees non-null | Fear of reviewer feedback | Cite compiler strictness: "Type `Order` is non-nullable; extra runtime branch is dead code." |

---

## 7. Verification Checklist

Before declaring a Sol Loop complete and ready to ship:

- [ ] **Budget Respected**: Total rounds $\le 3$ (or $\le 5$ with verified auth/data-loss rationale).
- [ ] **Complete Ledger**: Every finding (`S1`, `S2`, ...) has a recorded outcome (`fixed:`, `disagree:`, or `declined:`).
- [ ] **Reproduction Proof**: Every accepted `blocker` has a dedicated test that failed before the fix and passes now.
- [ ] **Zero Diff Bloat**: `git diff --shortstat` confirms the diff remained surgical and minimal.
- [ ] **Full Test Suite Clean**: Full regression tests pass cleanly with exit code 0.
- [ ] **PR Trailer Attached**: PR description contains `Reviewed with sol-loop: <N> rounds with <model>. Sol verdict: approved`.
