# 🏛️ Multi-Provider Model Council & Iterative Review Loops (`agents/multi-model-council.md`)

> **Classification**: Multi-Agent Consensus Protocol  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Lead Orchestrators, Adversarial Reviewers, Verification Agents  
> **Governing Rules**: **R-001** (Zero TODOs), **R-015** (Surgical Diffs), **R-182** (Minimal Diffs), **R-198** (Adversarial Debate), **R-203** (Tri-Model Multi-Provider Council Protocol), **R-204** (Review Scope-Creep Defense & Finding Triage)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/multi-model-council.md` |
| **Capability Archetypes** | Cross-Provider Consensus Review, Iterative Model Debates, Defect Triage & Scope-Creep Mitigation |
| **Trigger Phrases** | `"council"`, `"sol loop"`, `"run multi-model review"`, `"adversarial council"` |
| **Prerequisites** | Access to 3 distinct frontier model providers (e.g., Anthropic Claude Opus, OpenAI GPT Sol, Google Gemini Pro) via T3 Code `delegate_task` or native subagent runners |

Single-model code reviews suffer from confirmation bias and provider blind spots. The **Multi-Provider Model Council** brings three distinct frontier models from independent AI labs to evaluate code changes simultaneously. In parallel, the **Iterative Review Loop (`sol-loop`)** conducts deep multi-round verification with strict round budgets and an anti-scope-creep defense mechanism.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Review Scope-Creep Defense (Rule R-204)**:
> *Iterative review MUST converge toward correctness, not expand toward bloat.*
> Review loops naturally tend to inflate diffs by suggesting speculative helpers, redundant guards, defensive caches, and unneeded configuration flags. The lead agent's primary duty is to **fight scope creep**: resolve real blockers in the intended code path, decline speculative nits with written evidence, and prefer solutions that **delete or narrow code** over those that add complexity.

```
                     TRI-MODEL COUNCIL ARBITRATION FLOW
                     
                     [Working Tree Diff & Test Evidence]
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │  Delegate 1   │          │  Delegate 2   │          │  Delegate 3   │
    │ Anthropic Lab │          │  OpenAI Lab   │          │ DeepMind Lab  │
    │ (Claude Opus) │          │   (GPT Sol)   │          │ (Gemini Pro)  │
    └───────┬───────┘          └───────┬───────┘          └───────┬───────┘
            │                          │                          │
            ▼                          ▼                          ▼
     [Score: 8/10]              [Score: 9/10]              [Score: 8/10]
     [Findings: S1]             [Findings: S2]             [Findings: S3]
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │ Lead Agent Triage & Ledger    │
                       │ - Blocker: Real break in path │
                       │ - Should: Caller-facing bug   │
                       │ - Nit: Out-of-scope / decline │
                       └───────────────┬───────────────┘
                                       │
                         [Apply Minimal Surgical Fix]
                                       │
                                       ▼
                         [Round 2 Diff (Open Items Only)]
```

---

## 3. Architecture & Design Patterns

### 3.1 Council Composition & Model Selection

When convening a Council:
1. **Three Providers, Three Flagships**: Select the highest-reasoning model from three independent providers:
   - **Provider A (Anthropic)**: Claude 3.5 / 3.7 Sonnet or Claude Opus.
   - **Provider B (OpenAI)**: GPT-4o, o1, o3-mini, or GPT Sol.
   - **Provider C (Google DeepMind)**: Gemini 1.5 Pro, 2.0 Flash/Pro, or Gemini 3.
2. **Read-Only Sandbox**: Council delegates operate strictly in read-only mode (`mode: "async"`, `role: "review"`). They MUST NOT edit files, commit git state, or launch nested subagents.
3. **No Substitute Quotas**: If a designated provider is unavailable, report the outage honestly rather than silently duplicating another model.

### 3.2 Iteration Budget Ceilings

To eliminate infinite loops and token hemorrhaging:
- **Default Budget**: Maximum **3 rounds** total.
  - *Round 1*: Full review of the entire scoped change and context.
  - *Round 2 & 3*: Focused verification checking *only* the modified lines and previously open findings.
- **Extended Budget (Up to 5 Rounds)**: Permitted ONLY when an open `blocker` or `should` finding directly involves:
  1. Cryptographic security or authentication bypasses.
  2. Data corruption or general ledger imbalances.
  3. Distributed state concurrency or race conditions.
- **Early Termination**: If a round yields only `nit` findings, the loop terminates immediately.

### 3.3 The Three-Tier Finding Severity Taxonomy

All findings reported by delegates or review bots MUST be classified into one of three strict buckets:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FINDING SEVERITY TAXONOMY                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. BLOCKER   │ The intended user scenario is broken, panics, or corrupts    │
│              │ state. Mandatory fix before merge.                           │
├──────────────┼──────────────────────────────────────────────────────────────┤
│ 2. SHOULD    │ Real defect that callers will trigger under valid inputs,    │
│              │ but outside the primary happy path. Mandatory fix or test.   │
├──────────────┼──────────────────────────────────────────────────────────────┤
│ 3. NIT       │ Stylistic preference, speculative future case, micro-perf    │
│              │ without benchmarks, or unneeded guards. DECLINE with reason. │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Structured Review Ledger & Council Coordinator (`council_runner.py`)

```python
#!/usr/bin/env python3
"""Multi-Model Council Review Coordinator and Ledger Reconciler."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import json
import sys
from typing import List, Dict, Optional

class Severity(Enum):
    BLOCKER = "blocker"
    SHOULD = "should"
    NIT = "nit"

class FindingStatus(Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DECLINED = "declined"

@dataclass
class Finding:
    finding_id: str
    reviewer: str
    severity: Severity
    file_path: str
    line_number: int
    claim: str
    suggestion: str
    status: FindingStatus = FindingStatus.OPEN
    disposition_reason: Optional[str] = None

@dataclass
class CouncilRound:
    round_number: int
    scores: Dict[str, str] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)

class ReviewLedger:
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
        self.rounds: List[CouncilRound] = []

    def add_round(self, round_num: int, scores: Dict[str, str]) -> CouncilRound:
        c_round = CouncilRound(round_number=round_num, scores=scores)
        self.rounds.append(c_round)
        return c_round

    def record_finding(self, c_round: CouncilRound, finding: Finding):
        c_round.findings.append(finding)

    def resolve_finding(self, finding_id: str, reason: str):
        for r in self.rounds:
            for f in r.findings:
                if f.finding_id == finding_id:
                    f.status = FindingStatus.RESOLVED
                    f.disposition_reason = reason
                    return

    def decline_finding(self, finding_id: str, reason: str):
        for r in self.rounds:
            for f in r.findings:
                if f.finding_id == finding_id:
                    f.status = FindingStatus.DECLINED
                    f.disposition_reason = reason
                    return

    def generate_markdown_scorecard(self) -> str:
        """Render standard markdown table for PR descriptions."""
        if not self.rounds:
            return "No review rounds recorded."

        reviewers = sorted(list(self.rounds[0].scores.keys()))
        headers = ["Delegate"] + [f"Round {r.round_number}" for r in self.rounds]
        
        lines = [
            "## Council review",
            f"Rounds: {len(self.rounds)}\n",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |"
        ]

        for rev in reviewers:
            row = [rev]
            for r in self.rounds:
                score = r.scores.get(rev, "no score")
                row.append(score)
            lines.append("| " + " | ".join(row) + " |")

        lines.append("\n### Findings Ledger")
        for r in self.rounds:
            for f in r.findings:
                status_icon = "✅" if f.status == FindingStatus.RESOLVED else ("⛔" if f.status == FindingStatus.DECLINED else "⏳")
                lines.append(f"- {status_icon} **[{f.finding_id}]** (`{f.severity.value}` in `{f.file_path}:{f.line_number}`): {f.claim}")
                if f.disposition_reason:
                    lines.append(f"  *Disposition*: {f.disposition_reason}")

        return "\n".join(lines)

if __name__ == "__main__":
    ledger = ReviewLedger(max_rounds=3)
    r1 = ledger.add_round(1, {"Claude Opus": "7/10", "GPT Sol": "8/10", "Gemini Pro": "7/10"})
    
    f1 = Finding("F-01", "Claude Opus", Severity.BLOCKER, "src/auth.py", 42, "Missing JWT expiration check", "Add exp claim validation")
    f2 = Finding("F-02", "GPT Sol", Severity.NIT, "src/auth.py", 88, "Consider adding LRU cache for keys", "Add lru_cache decorator")
    ledger.record_finding(r1, f1)
    ledger.record_finding(r1, f2)

    # Triage decisions
    ledger.resolve_finding("F-01", "Fixed in commit c4a123: added exp check against current unix epoch.")
    ledger.decline_finding("F-02", "Declined: key rotation occurs infrequently; adding cache introduces stale-read risk.")

    r2 = ledger.add_round(2, {"Claude Opus": "9/10", "GPT Sol": "10/10", "Gemini Pro": "9/10"})
    print(ledger.generate_markdown_scorecard())
```

---

## 5. Security & Performance Considerations

- **Context Window Protection**: Never dump raw 100K-token execution logs into reviewer prompts. Provide the concise git diff (`git diff origin/main...HEAD`), test execution output, and the exact architectural intent.
- **Hallucination Checking**: Every finding cited by a model MUST be verified against actual line numbers and file contents by the lead agent before taking action. Never edit code based on a nonexistent hallucinated file or method.
- **Budget Exhaustion**: If the budget reaches 3 rounds (or 5 rounds in security cases) without consensus, the lead agent MUST NOT unilaterally loop forever. Summarize the remaining dispute in 3 lines and escalate to human decision.

---

## 6. Common Pitfalls & Anti-Patterns

### ❌ Anti-Pattern 1: The Appeasement Spiral (Yielding to Scope Creep)
```markdown
<!-- BAD: Accepting speculative model suggestions that bloat the PR -->
Reviewer: "You should also add a pluggable storage interface, Redis clustering support, and 4 fallback adapters."
Developer: "Agreed! Adding all 4 adapters to appease the reviewer."
```
```markdown
<!-- GOOD: Defending the minimal surgical scope -->
Lead Agent: "Declined finding F-04: The task scope is single-node SQLite persistence. Redis clustering represents unsolicited architectural bloat violating R-015 and R-204. Logged as future consideration."
```

### ❌ Anti-Pattern 2: Inventing Scores
```markdown
<!-- BAD: Fabricating numerical ratings when models gave only textual feedback -->
| Delegate | Round 1 |
| Claude Opus | 8/10 (inferred by agent) |
```
```markdown
<!-- GOOD: Explicitly recording 'no score' when a model did not provide a rating -->
| Delegate | Round 1 |
| Claude Opus | no score |
```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Tri-Provider Diversity** | 3 independent AI lab models | Verify model IDs belong to distinct providers |
| **2. Round Ceiling** | $\le 3$ rounds ($\le 5$ for security/auth) | Assert `len(ledger.rounds) <= max_rounds` |
| **3. Scope-Creep Audit** | Diff size did not increase by $>20\%$ | Compare `git diff --stat` before and after review rounds |
| **4. Findings Resolution** | Zero unresolved `blocker` or `should` items | Assert all blockers are either `resolved` or `declined` with proof |
| **5. Scorecard Integrity** | Table embedded in PR description | Markdown table matches canonical format |

---

*See also*: [`agents/arena-evaluator.md`](arena-evaluator.md) for architectural trade-off evaluations and [`workflows/pr-lifecycle-babysitting.md`](../workflows/pr-lifecycle-babysitting.md) for PR submission and bot monitoring.
