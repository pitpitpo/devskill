# 📈 Performance Hillclimbing & Scientific Optimization (`agents/hillclimbing-optimization.md`)

> **Classification**: Core Engineering Optimization Protocol  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Performance Engineers, Systems Architects, Optimization Subagents  
> **Governing Rules**: **R-001** (Zero TODOs), **R-004** (Anti-Fake Green), **R-015** (Surgical Diffs), **R-164** (Atomic Commits), **R-202** (Direct Proof Over Synthetic Simulation), **R-212** (Scientific Hillclimbing & Benchmark Discipline)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/hillclimbing-optimization.md` |
| **Capability Archetypes** | Sustained Performance Optimization, Rigorous Benchmarking, Empirical Hypothesis Testing |
| **Trigger Phrases** | `"hillclimb"`, `"optimize performance"`, `"benchmark checklist"`, `"reduce latency"` |
| **Prerequisites** | Profiler tools (`py-spy`, `perf`, `node --cpu-prof`), repeatable benchmark harness, Git 2.40+ |

Casual performance optimization frequently deteriorates software systems: engineers apply speculative micro-optimizations, compare debug builds with release builds, or introduce architectural complexity for unmeasured gains. **Performance Hillclimbing** enforces a strict scientific method: measure the baseline, freeze a validated harness, test one hypothesis per iteration, log decisions in an append-only ledger (`decision.tsv`), and keep only changes with verified statistical deltas while reverting everything else.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Performance Hillclimbing (Rule R-212)**:
> *You own the metric and the experiment's integrity. Measure before and after with a frozen harness; keep or revert.*
> Never stack multiple speculative optimizations into one commit. Every optimization loop MUST test exactly one hypothesis per iteration, compare the median of $\ge 5$ alternating runs against the baseline, verify that the regression test gate stays green, and commit strictly one accepted win at a time. If the metric fails to beat the noise threshold, the change MUST be reverted immediately.

```
                      SCIENTIFIC HILLCLIMBING LOOP
                      
        ┌──────────────────────────────────────────────────┐
        │ 1. Profile Workload & Identify Limiter (CPU/IO)  │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 2. Build, Validate & FREEZE Benchmark Harness    │
        │    (Pass the 7-Question Benchmark Audit)         │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 3. Record Baseline Metric & Green Gate Status    │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 4. Propose Single Grounded Hypothesis            │
        │    (Log in decision.tsv: id, hypothesis, intent) │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 5. Apply Minimal Surgical Change in Code         │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ 6. Measure 5+ Alternating A/B Runs with Harness  │
        └─────────────────────────┬────────────────────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
             [Metric Improved &        [Noise or Broken Gate]
              Gate Passed Clean]               │
                     │                         ▼
                     │                 REVERT TO CLEAN HEAD
                     │                 (Record REVERTED in log)
                     ▼                         │
            COMMIT EXACT FIX ONLY              │
            (git add <files>, not -A)          │
            (Record KEPT in log)               │
                     │                         │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     [Predicate Met or Exhausted?]
```

---

## 3. Architecture & Design Patterns

### 3.1 The 7-Question Benchmark Audit

Before trusting, reporting, or acting on any performance number, the agent MUST answer all seven audit questions with empirical evidence:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          7-QUESTION BENCHMARK AUDIT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Why not double?     │ Name the physical limiter: CPU saturation, memory  │
│                        │ bandwidth, I/O wait, lock contention, or network.  │
├────────────────────────┼────────────────────────────────────────────────────┤
│ 2. Was it tuned?       │ Release builds, production flags, warm caches,     │
│                        │ connection pools. Never compare debug vs release.  │
├────────────────────────┼────────────────────────────────────────────────────┤
│ 3. Did it break limits?│ Check Amdahl's Law: removing a component taking    │
│                        │ 10% of runtime can speed up the system by at most  │
│                        │ ~11%. Results violating physics are invalid.       │
├────────────────────────┼────────────────────────────────────────────────────┤
│ 4. Did it error?       │ Failures and fast rejects are fast; timeouts are   │
│                        │ slow. The harness MUST count errors and payload ok.│
├────────────────────────┼────────────────────────────────────────────────────┤
│ 5. Does it reproduce?  │ Minimum 5 alternating runs (A/B/A/B). Report       │
│                        │ median and range. Gap must exceed run noise.       │
├────────────────────────┼────────────────────────────────────────────────────┤
│ 6. Does it matter?     │ Measure end-to-end latency on the path user waits  │
│                        │ on. Micro-optimizing a 1% helper is negligible.    │
├────────────────────────┼────────────────────────────────────────────────────┤
│ 7. Did it even happen? │ Verify the code actually executed. Rule out dead   │
│                        │ code elimination, unawaited promises, or JIT no-ops│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 The Decision Ledger (`decision.tsv`)

The hillclimb loop tracks every attempt in an append-only TSV file ignored by git (`decision.tsv`):

| Column | Format | Description |
|---|---|---|
| `iteration_id` | `H-001`, `H-002` | Sequential iteration identifier |
| `hypothesis` | Plain text | Grounded architectural hypothesis naming the specific bottleneck |
| `change` | Plain text | Concrete surgical code modification |
| `before_metric` | Number with unit | Baseline median (e.g. `41.2ms`) |
| `after_metric` | Number with unit | Post-change median (e.g. `33.1ms`) |
| `delta_percent` | Percentage | Signed improvement (e.g. `-19.6%`) |
| `gate_status` | `PASS` / `FAIL` | Full regression test suite result |
| `verdict` | `KEPT` / `REVERTED` | Final action taken on the working tree |
| `notes` | Plain text | Limiter behavior or reason for rejection |

---

## 4. Concrete Code Examples

### 4.1 Hillclimbing Controller & Harness Evaluator (`hillclimb_runner.py`)

```python
#!/usr/bin/env python3
"""Scientific Hillclimbing Optimization Runner with Alternating A/B Sampling."""

from __future__ import annotations
import csv
import os
import statistics
import subprocess
import sys
import time
from typing import List, Callable

def run_sample(cmd: List[str]) -> float:
    """Execute one benchmark run and return measured duration in milliseconds."""
    start = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration_ms = (time.perf_counter() - start) * 1000.0
    if res.returncode != 0:
        raise RuntimeError(f"Harness failed with code {res.returncode}: {res.stderr}")
    return duration_ms

def measure_median(cmd: List[str], samples: int = 5) -> tuple[float, float, float]:
    """Measure median, min, and max over N runs."""
    results = [run_sample(cmd) for _ in range(samples)]
    return (statistics.median(results), min(results), max(results))

class HillclimbSession:
    def __init__(self, tsv_path: str = "decision.tsv"):
        self.tsv_path = tsv_path
        if not os.path.exists(self.tsv_path):
            with open(self.tsv_path, "w", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow([
                    "iteration_id", "hypothesis", "change",
                    "before_metric", "after_metric", "delta_percent",
                    "gate_status", "verdict", "notes"
                ])

    def log_attempt(self, iter_id: str, hypothesis: str, change: str,
                    before: float, after: float, gate_passed: bool,
                    verdict: str, notes: str):
        delta_pct = ((after - before) / before) * 100.0
        with open(self.tsv_path, "a", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow([
                iter_id, hypothesis, change,
                f"{before:.2f}ms", f"{after:.2f}ms", f"{delta_pct:+.1f}%",
                "PASS" if gate_passed else "FAIL", verdict, notes
            ])
        print(f"[*] Iteration {iter_id}: {before:.2f}ms -> {after:.2f}ms ({delta_pct:+.1f}%) | {verdict}")

if __name__ == "__main__":
    session = HillclimbSession("decision.tsv")
    print("Hillclimbing session initialized. Logging to decision.tsv.")
    
    # Example simulated iteration
    baseline = 45.2
    optimized = 34.1
    session.log_attempt(
        iter_id="H-001",
        hypothesis="Eliminate redundant JSON serialization in hot loop",
        change="Pass structured dict directly to worker pool",
        before=baseline,
        after=optimized,
        gate_passed=True,
        verdict="KEPT",
        notes="CPU bound on json.dumps; dropped from 45.2ms to 34.1ms"
    )
```

---

## 5. Security & Performance Considerations

- **Noise Floor & Thermal Throttling**: On laptops or shared CI agents, CPU thermal throttling can degrade later runs. Interleave A and B measurements (`A1, B1, A2, B2, A3, B3`) rather than running all A's then all B's.
- **Deadlock and Resource Exhaustion**: Concurrency optimizations (worker thread pools, connection pools) MUST have explicit upper bounds. Never allow unbounded thread creation under load.
- **Memory Growth Profiling**: Faster throughput must not come at the expense of memory leaks. Track RSS memory alongside latency metrics.

---

## 6. Common Pitfalls & Anti-Patterns

### ❌ Anti-Pattern 1: Claiming a Win from Untuned Comparisons
```bash
# BAD: Comparing an unoptimized debug build with an optimized release build
cargo test --bench my_bench           # debug build (slow)
cargo test --bench my_bench --release # release build (fast)
# "We achieved a 10x speedup by refactoring!" (NO: You just enabled compiler optimizations)
```
```bash
# GOOD: Comparing both variants under identical production flags
cargo bench --bench my_bench -- baseline  # release
cargo bench --bench my_bench -- candidate # release
```

### ❌ Anti-Pattern 2: Stacking Untested Hypotheses
```bash
# BAD: Bundling 4 speculative ideas into one massive commit
git commit -m "perf: add redis cache, rewrite query in raw SQL, use uvloop, and gzip responses"
# If latency degrades or regressions occur, which change caused it?
```
```bash
# GOOD: One hypothesis, one measurement, one commit
# 1. Benchmark SQL query rewrite -> KEPT (-14%) -> commit 1
# 2. Benchmark uvloop integration -> REVERTED (+2% noise) -> discarded
```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. 7-Question Audit** | All 7 questions answered with evidence | Documented audit table in PR or commit notes |
| **2. Harness Stability** | Harness frozen before code changes | Git diff shows zero changes to benchmark harness |
| **3. Statistical Sampling** | $\ge 5$ alternating runs per comparison | Report includes median, min, and max |
| **4. Decision Ledger** | `decision.tsv` populated with all iterations | Every kept and reverted attempt logged |
| **5. Atomic Win Commits** | Exactly 1 commit per accepted hypothesis | Git log shows isolated, surgical optimization hunks |

---

*See also*: [`sections/frontend/web-performance.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/frontend/web-performance.md) for Core Web Vitals and [`agents/blast-radius-verification.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/blast-radius-verification.md) for verifying change safety.
