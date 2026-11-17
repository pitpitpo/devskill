# 🎯 Blast-Radius Analysis & Cross-System Verification (`agents/blast-radius-verification.md`)

> **Classification**: Core Agent Verification Protocol  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Senior Systems Engineers, Security Auditors  
> **Governing Rules**: **R-001** (Zero TODOs), **R-003** (Zero Unverified Assumptions), **R-004** (Anti-Fake Green), **R-015** (Surgical Diffs), **R-182** (Minimal Diffs), **R-202** (Direct Proof Over Synthetic Simulation), **R-211** (Blast-Radius Grounding & Single-Fact Proof)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `agents/blast-radius-verification.md` |
| **Capability Archetypes** | Impact Analysis, Cross-Boundary Safety Audits, Runtime Dependency Verification |
| **Trigger Phrases** | `"blast radius of X"`, `"what could this break"`, `"verify change safety"`, `"audit side effects"` |
| **Prerequisites** | Git 2.40+, Pytest/Jest/Go test runners, static AST analyzer or grep, access to local runtime environment |

Small-looking changes frequently trigger catastrophic production regressions in downstream consumers, wire formats, serialization boundaries, or asynchronous event loops. The **Blast-Radius Verification Protocol** provides a systematic, evidence-driven methodology to find what a change breaks beyond the immediate diff, isolate the single foundational fact that guarantees its safety, and prove that fact with executing code.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Blast-Radius Verification (Rule R-211)**:
> *A blast-radius writeup that sounds convincing is worthless without runtime proof.*
> Listing callers from a symbol grep is not the job. The true blast radius lies where static search stops: serialized JSON schemas, database column types, microtask timings, teardown hooks, feature flags, and multi-hop consumers. Most changes that look dangerous hinge on **one single safety fact**; agents MUST identify that fact and prove it with executing code.

```
                       5-LEVEL CERTAINTY HIERARCHY
                       
  Level 1: "You said so"               ──► [REJECTED: Worthless without proof]
  Level 2: "You pointed at line"       ──► [Cites file:line in library or source]
  Level 3: "You proved unreachable"    ──► [Step-by-step logic proving bad case fails]
  Level 4: "You ran a test/script"     ──► [PASS: Real execution fails loud if wrong]
  Level 5: "You reproduced in live app"──► [GOLD STANDARD: Observed in running system]
```

---

## 3. Architecture & Design Patterns

### 3.1 The 5-Step Blast Radius Methodology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Ingest Diff & Semantic Boundaries                                        │
│    Inspect modified, added, and deleted symbols. Trace indirect mutations. │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Isolate the "One Safety Fact"                                            │
│    Identify the single invariant that renders the risky change safe         │
│    (e.g., "This cache eviction only drops dead keys and never mutations").  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Look Where Grep Stops (The Dark Blast Radius)                            │
│    - JSON / Wire Schemas: Serialized objects read by other services.        │
│    - Database Columns: Foreign keys, enum columns, non-null constraints.    │
│    - Execution Lifecycle: Microtasks, React teardowns, process exits.       │
│    - Feature Flags & Dynamic Routes: Hidden callers behind string keys.     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Build the Single-Fact Executable Probe                                    │
│    Write a standalone script or test exercising the exact edge case.        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Classify & Report (Proven vs Unproven)                                   │
│    Document real risks, cleared concerns, and the reproducible test.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 The Dark Blast Radius: Where Symbol Search Fails

Standard static tools and grep cannot detect:
1. **Serialization Wire Contracts**: Changing a struct field name from `userId` to `id` breaks external mobile clients or microservice RPCs that deserialize untyped payloads.
2. **Implicit Database Invariants**: Altering an enum value in code without checking database rows that already contain the legacy string.
3. **Execution Lifecycle Timing**: Code running during `window.onbeforeunload`, React `useEffect` cleanups, or Node.js `process.on('exit')` cannot perform asynchronous I/O or resolve promises.
4. **Shared Multi-Tenant Storage**: Key collisions in Redis or memcached when key namespace prefixes are altered.

---

## 4. Concrete Code Examples

### 4.1 Standalone Single-Fact Safety Probe (`blast_probe.py`)

```python
#!/usr/bin/env python3
"""Blast-Radius Single-Fact Executable Probe.
Verifies that modifying CacheEngine.evict() does not evict active user sessions.
"""

from __future__ import annotations
import sys
import time
from typing import Dict, Any

class MockSessionCache:
    """Production cache engine simulation for single-fact proof."""
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, value: Any, ttl_seconds: float):
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds
        }

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def evict_expired_batches(self) -> int:
        """The modified method under audit: must ONLY drop expired entries."""
        now = time.time()
        to_delete = [k for k, v in self._store.items() if now >= v["expires_at"]]
        for k in to_delete:
            del self._store[k]
        return len(to_delete)

def verify_single_fact_safety():
    """Prove Level 4 Certainty: Active sessions survive batch eviction."""
    cache = MockSessionCache()
    
    # 1. Populate active sessions (TTL = 3600s)
    cache.set("session_user_1", {"user_id": 101, "role": "admin"}, ttl_seconds=3600)
    cache.set("session_user_2", {"user_id": 102, "role": "editor"}, ttl_seconds=3600)
    
    # 2. Populate expired session (TTL = -10s)
    cache.set("session_user_expired", {"user_id": 999, "role": "guest"}, ttl_seconds=-10)

    # 3. Execute the eviction pass
    evicted_count = cache.evict_expired_batches()

    # 4. Assert foundational invariants
    assert evicted_count == 1, f"Expected 1 evicted key, got {evicted_count}"
    assert cache.get("session_user_expired") is None, "Expired session was not purged"
    assert cache.get("session_user_1") is not None, "FATAL: Active session_user_1 was dropped!"
    assert cache.get("session_user_2") is not None, "FATAL: Active session_user_2 was dropped!"

    print("✅ PROOF LEVEL 4 PASSED: Active sessions strictly survive eviction pass.")

if __name__ == "__main__":
    try:
        verify_single_fact_safety()
    except AssertionError as e:
        print(f"❌ BLAST RADIUS SAFETY VIOLATION: {e}", file=sys.stderr)
        sys.exit(1)
```

### 4.2 Blast Radius Audit Report Generator

```python
#!/usr/bin/env python3
"""Generates structured Markdown Blast-Radius reports."""

from dataclasses import dataclass
from typing import List

@dataclass
class RiskItem:
    area: str
    failure_mode: str
    file_and_line: str
    severity: str
    proof_status: str

def generate_blast_report(change_summary: str, single_safety_fact: str, proof_level: int, risks: List[RiskItem]) -> str:
    lines = [
        "## Blast-Radius Analysis Report",
        f"**Change Summary**: {change_summary}",
        f"**The One Safety Fact**: {single_safety_fact} (Certainty Level {proof_level}/5)\n",
        "| Subsystem / Area | Potential Failure Mode | Code Location | Severity | Proof Status |",
        "|---|---|---|---|---|"
    ]
    for r in risks:
        lines.append(f"| {r.area} | {r.failure_mode} | `{r.file_and_line}` | {r.severity} | {r.proof_status} |")
    return "\n".join(lines)

if __name__ == "__main__":
    report = generate_blast_report(
        change_summary="Optimized session cache pruning in memory store.",
        single_safety_fact="Active session timestamps are never less than or equal to current epoch.",
        proof_level=4,
        risks=[
            RiskItem("Auth Sessions", "Active users logged out mid-request", "src/cache.py:42", "HIGH", "CLEARED (Level 4)"),
            RiskItem("Token Store", "Memory leak from uncollected tombstones", "src/cache.py:55", "MEDIUM", "CLEARED (Level 3)")
        ]
    )
    print(report)
```

---

## 5. Security & Performance Considerations

- **Cross-Service Blast Radius**: When modifying database models, verify whether asynchronous replication pipelines (Kafka, Debezium CDC) or read replicas consume that table schema.
- **Microtask Execution Starvation**: When inserting recursive microtasks (`queueMicrotask` or `process.nextTick`), ensure they do not starve the I/O event loop or cause memory consumption spikes.
- **Feature Flag Reentrancy**: Ensure feature flag evaluation calls do not themselves invoke the component being flagged, avoiding stack overflows.

---

## 6. Common Pitfalls & Anti-Patterns

### ❌ Anti-Pattern 1: The Raw Caller Grep Fallacy
```markdown
<!-- BAD: Listing all grep results and assuming that covers the blast radius -->
"I ran git grep 'getUser' and found 3 callers. I checked them and they look fine."
```
```markdown
<!-- GOOD: Tracing beyond symbol grep to wire contracts and serialized payloads -->
"Beyond the 3 direct TypeScript callers of `getUser`, the return object is serialized to JSON and sent over WebSocket to the desktop client. Checked the client's schema parser: field `user_tier` is required. Retained backward compatibility."
```

### ❌ Anti-Pattern 2: Synthesized Claims without Code Execution
```markdown
<!-- BAD: Claiming safety based on mental simulation -->
"The database transaction guarantees that if the second write fails, the first is rolled back."
```
```markdown
<!-- GOOD: Providing the concrete reproduction script proving rollback -->
"Executed integration test `test_tx_rollback_on_payment_failure`: Intentionally raised OperationalError on line 54; verified with `SELECT count(*) FROM orders` that 0 rows were committed."
```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Certainty Level** | Minimum Level 4 (Executed Test) | Verify test script ran with exit code 0 |
| **2. Single Safety Fact** | Explicitly stated in report | Assertion directly tests the stated safety fact |
| **3. Beyond-Grep Audit** | Checked serialization & wire formats | Documented JSON/DB schema verification |
| **4. Zero Speculative Guesses** | 100% of cited risks tied to `file:line` | All reported file paths exist on disk |
| **5. Clean Proof Script** | Self-contained executable probe | Probe script runs standalone without external mocks |

---

*See also*: [`agents/full-send-delivery.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/full-send-delivery.md) for delivery merge gates and [`agents/tdd-reproduction.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/tdd-reproduction.md) for bug reproduction protocols.
