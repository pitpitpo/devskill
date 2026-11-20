# 🚀 Autonomous End-to-End PR Delivery & Merge Gate Engine (`agents/full-send-delivery.md`)

> **Classification**: Core Agent Execution Protocol  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Lead Orchestrator Subagents, CI/CD Automation Engineers  
> **Governing Rules**: **R-001** (Zero TODOs), **R-002** (Zero Mock Data), **R-004** (Anti-Fake Green), **R-164** (Atomic Commits), **R-182** (Minimal Surgical Diffs), **R-201** (Full-Send Merge Gate), **R-202** (Direct Proof Over Synthetic Simulation)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/full-send-delivery.md` |
| **Capability Archetypes** | Autonomous PR Shipping, Hands-Free Engineering, Automated Merge Gate Evaluation |
| **Trigger Phrases** | `"full send"`, `"full stop"`, `"ship it end-to-end"`, `"take to merged PR"` |
| **Prerequisites** | Authenticated GitHub CLI (`gh`), Git 2.40+, Pytest/Jest/Cargo/Go test runner, T3 Code harness or subagent runners |

When a developer triggers `"full send"`, they explicitly grant the agent full autonomy to execute the work end-to-end: prove the change, request adversarial review, rebase onto latest default, file the PR, babysit CI and review bots, and execute the final merge without human prompting. Conversely, when the user triggers `"full stop"`, the agent executes identical rigorous proofs, reviews, and babysitting, but halts at the 5-point Merge Gate, handing off the verified, open PR for the human engineer to merge.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Full-Send Autonomy**:
> *Autonomy is earned through undeniable proof, not assumed through lack of errors.*
> An agent running in full-send mode MUST NOT terminate its turn while CI checks, review bots, or merge queues are pending. Once `"full send"` is authorized, the agent owns the thread until the PR is merged or an explicit blocking human boundary is hit. A question asked in a normal message goes unseen; human escalation MUST invoke modal question tools.

```
                     FULL-SEND vs FULL-STOP EXECUTION MATRIX
                     
   [User Request: "full send"]                     [User Request: "full stop"]
               │                                               │
               ▼                                               ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 1. Minimal Surgical Implementation (R-015, R-182)                      │
   │ 2. Direct Observable Proof (reproduce defect -> test pass -> runtime) │
   │ 3. Adversarial Model Review (agents/multi-model-council.md)           │
   │ 4. Rebase & Problem-First PR Filing (workflows/pr-lifecycle.md)        │
   │ 5. Event-Driven CI & Bot Babysitting (watch_pull_request / pr-wait)    │
   │ 6. Evaluate 5-Point Merge Gate (R-201)                                 │
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          [Mode == "full send"]               [Mode == "full stop"]
                     │                                   │
                     ▼                                   ▼
          Execute Merge Command               Handoff to Human Lead
          - Re-check base freshness           - Unwatch PR in harness
          - Fast-forward / Squash merge       - Report direct proof & checks
          - Verify remote merged status       - PR stays open & unmerged
```

---

## 3. Architecture & Design Patterns

### 3.1 The 7-Step Autonomous Delivery Lifecycle

1. **Finish the Change**: Solve the root defect or requested feature with the minimal viable diff. If on the default branch (`main`), immediately switch to a feature branch (`feat/...` or `fix/...`).
2. **Prove It Directly**: Collect irrefutable execution evidence. Mocked tests alone DO NOT constitute proof.
3. **Multi-Model Feedback**: Invoke an adversarial review round (via [`agents/multi-model-council.md`](multi-model-council.md) or [`agents/arena-evaluator.md`](arena-evaluator.md)).
4. **Rebase & File PR**: Fetch `origin/main`, rebase cleanly with `git rebase origin/main`, and open a problem-first pull request via [`workflows/pr-lifecycle-babysitting.md`](../workflows/pr-lifecycle-babysitting.md).
5. **Event-Driven Babysitting**: Monitor CI jobs and review bots (Greptile, Macroscope, CodeRabbit). Fix genuine defects; dismiss false positives with written citations.
6. **Evaluate the Merge Gate**: Enforce the 5 non-negotiable merge criteria.
7. **Merge or Handoff**: In `"full send"`, execute the merge through branch protection. In `"full stop"`, remove watchers, disengage auto-merge, and present the completion card.

### 3.2 The 5-Point Merge Gate Protocol (Rule R-201)

Before executing a merge or declaring readiness, the following five criteria MUST be verified on the latest remote commit SHA:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           5-POINT MERGE GATE CRITERIA                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Proof Completeness    │ Observed direct session evidence covering 100%   │
│                          │ of the modified logical paths.                   │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 2. CI Required Checks    │ 100% of required status checks report 'SUCCESS'.  │
│                          │ Zero failed, canceled, or hanging workflows.     │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 3. Bot & Review Triage   │ All gating bots (Greptile, Macroscope) finished. │
│                          │ Every finding is either fixed or dismissed.      │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 4. Zero Unresolved Blocs │ Zero open change requests from human reviewers.   │
│                          │ All review comment threads marked resolved.      │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ 5. Base Freshness        │ PR is up to date with origin/main (not BEHIND),  │
│                          │ mergeable (not DIRTY), with clean git range-diff.│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Strict Escalation Boundaries (When to Interrupt the User)

In autonomous mode, ordinary chat updates are unread. The agent MUST NOT pause or ask questions unless an absolute boundary is reached. When reaching a boundary, the agent MUST use interactive input modal tools (`ask_question` / `request_user_input`):

- **Boundary 1 [Proof Impasse]**: The change cannot be proved via CLI reproduction, tests, or visual rendering.
- **Boundary 2 [Destructive Actions]**: Deleting remote repositories, dropping production databases, or altering DNS/infrastructure.
- **Boundary 3 [Contradictory Requirements]**: Ambiguity in business logic where two mutually exclusive architectural directions exist.
- **Boundary 4 [Superseded PR]**: Another commit or PR landed on `main` that rendered this change obsolete.

---

## 4. Concrete Code Examples

### 4.1 Autonomous Delivery Controller (`delivery_orchestrator.py`)

```python
#!/usr/bin/env python3
"""Autonomous PR Delivery and Merge Gate Controller."""

from __future__ import annotations
import json
import subprocess
import sys
import time
from typing import Dict, Any, List

def run_cmd(cmd: List[str], check: bool = True) -> str:
    """Run a shell command and return stdout."""
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()

class FullSendController:
    def __init__(self, pr_number: int, repo: str, mode: str = "full-send"):
        self.pr_number = pr_number
        self.repo = repo
        self.mode = mode.lower()  # "full-send" or "full-stop"

    def fetch_pr_details(self) -> Dict[str, Any]:
        """Fetch current PR state using gh CLI GraphQL / REST."""
        out = run_cmd([
            "gh", "pr", "view", str(self.pr_number),
            "--repo", self.repo,
            "--json", "headRefOid,baseRefName,mergeStateStatus,reviewDecision,statusCheckRollup"
        ])
        return json.loads(out)

    def evaluate_merge_gate(self) -> tuple[bool, List[str]]:
        """Verify the 5-point Merge Gate criteria."""
        pr = self.fetch_pr_details()
        violations = []

        # 1. Base freshness and conflict status
        state = pr.get("mergeStateStatus")
        if state in ("DIRTY", "CONFLICTING"):
            violations.append(f"PR branch has conflicts (mergeStateStatus={state}). Rebase required.")
        elif state == "BEHIND":
            violations.append("PR branch is BEHIND base branch. Rebase onto latest origin/main required.")

        # 2. Status checks
        checks = pr.get("statusCheckRollup", [])
        for c in checks:
            status = c.get("status")
            conclusion = c.get("conclusion")
            name = c.get("name") or c.get("context")
            if status != "COMPLETED":
                violations.append(f"Check '{name}' is still {status}.")
            elif conclusion not in ("SUCCESS", "NEUTRAL", "SKIPPED"):
                violations.append(f"Check '{name}' concluded with '{conclusion}'.")

        # 3. Human review decision
        decision = pr.get("reviewDecision")
        if decision == "CHANGES_REQUESTED":
            violations.append("Human reviewer has requested changes on the PR.")

        return (len(violations) == 0, violations)

    def execute_delivery(self):
        """Execute the autonomous delivery loop."""
        print(f"[*] Starting {self.mode.upper()} Controller for PR #{self.pr_number} in {self.repo}...")
        
        passed, violations = self.evaluate_merge_gate()
        if not passed:
            print(f"[-] Merge Gate FAILED with {len(violations)} blocking issues:")
            for v in violations:
                print(f"    ❌ {v}")
            sys.exit(1)

        print("[+] 5-Point Merge Gate PASSED with 0 violations.")

        if self.mode == "full-stop":
            print("[*] FULL-STOP mode active: Disengaging watchers and handing off verified PR to human.")
            print(f"👉 PR URL: https://github.com/{self.repo}/pull/{self.pr_number} (READY TO MERGE)")
            return

        print("[*] FULL-SEND mode active: Executing merge through configured branch protection...")
        run_cmd([
            "gh", "pr", "merge", str(self.pr_number),
            "--repo", self.repo,
            "--squash", "--delete-branch"
        ])
        print(f"🚀 PR #{self.pr_number} successfully merged into {self.repo}/main!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: delivery_orchestrator.py <repo> <pr_number> [full-send|full-stop]")
        sys.exit(2)
    repo_arg = sys.argv[1]
    pr_arg = int(sys.argv[2])
    mode_arg = sys.argv[3] if len(sys.argv) > 3 else "full-send"
    controller = FullSendController(pr_arg, repo_arg, mode_arg)
    controller.execute_delivery()
```

---

## 5. Security & Performance Considerations

- **Branch Protection & Administrative Bypasses**: Under no circumstances may an agent invoke `gh pr merge --admin` or force-merge through failing status checks. If branch protection blocks merge due to unsigned commits or human-only rule sets, transition to `full-stop` handoff.
- **Force-Push Lease Enforcement**: Whenever updating a rebased PR branch, the agent MUST use `git push --force-with-lease`. Never use bare `git push -f`, which risks clobbering upstream commits pushed by reviewers or automated bots.
- **Rate Limit Resilience**: Automated babysitting loops share the GitHub account GraphQL token bucket. Watchers MUST throttle requests and fall back to REST endpoints when GraphQL rates degrade.

---

## 6. Common Pitfalls & Anti-Patterns

### ❌ Anti-Pattern 1: The Phantom Wait Loop (Spin-Polling)
```bash
# BAD: Tight sleep loop that burns GitHub API rate limits and locks agent thread
while true; do
    status=$(gh pr view --json statusCheckRollup)
    if echo "$status" | grep -q "SUCCESS"; then break; fi
    sleep 5
done
```
```bash
# GOOD: Event-driven notification or backoff watcher with rate-limit persistence
workflows/scripts/pr-wait 142 --until ready
# Or in T3 Code: call watch_pull_request and terminate turn cleanly until woken
```

### ❌ Anti-Pattern 2: Merging with Unresolved Bot Findings
```markdown
<!-- BAD: Ignoring review bot findings because compilation succeeded -->
"CodeRabbit and Greptile left 4 comments about missing null checks, but my unit test passed so I merged it."
```
```markdown
<!-- GOOD: Verifying every bot finding against source code -->
"Investigated 3 Greptile findings:
- Finding 1 (Potential nil dereference in handler): Verified real. Fixed in commit abc1234.
- Finding 2 (Unchecked error on close): Verified real. Handled with explicit log.
- Finding 3 (Suggesting memoization on static lookup): Dismissed as premature optimization."
```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Direct Proof** | 100% evidence observed in session | Exit code 0 on reproduction test + real runtime check |
| **2. Merge Gate Status** | 5 of 5 checks passed | `python delivery_orchestrator.py <repo> <pr> full-send` exits code 0 |
| **3. Base Freshness** | 0 commits behind `origin/main` | `git fetch origin && git status -uno` shows branch up to date |
| **4. Git Authorship** | Retain original contributor trailers | `git log -1 --pretty=format:"%an <%ae> %B"` verifies credit |
| **5. Watcher Cleanup** | Zero dangling background pids | `unwatch_pull_request` called on handoff / `pr-wait` terminated |

---

*See also*: [`agents/unified-agent-stacks.md`](unified-agent-stacks.md) for cross-stack synthesis (`tstack`, `pstack`, `gstack`, `kstack`, `superpowers`, `compound-engineering`), [`agents/code-forensics-interrogation.md`](code-forensics-interrogation.md) for problem-first `file-pr` and `leaving-pr-comments`, [`agents/multi-model-council.md`](multi-model-council.md) for adversarial consensus, and [`workflows/pr-lifecycle-babysitting.md`](../workflows/pr-lifecycle-babysitting.md) for PR monitoring.
