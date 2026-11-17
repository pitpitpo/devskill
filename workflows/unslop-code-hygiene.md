# 🧹 Anti-Slop Code Hygiene, Comment Elimination & Structural Encoding (`workflows/unslop-code-hygiene.md`)

> **Classification**: Production Code Quality Protocol  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Code Reviewers, Software Engineers  
> **Governing Rules**: **R-001** (Zero TODOs), **R-015** (Surgical Diffs), **R-016** (Zero Unsolicited Refactoring), **R-034** (Zero Any/Bypasses), **R-213** (Structural Encoding Over Comment Sermons), **R-214** (Zero AI Slop & Unsolicited Banners)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `workflows/unslop-code-hygiene.md` |
| **Capability Archetypes** | Code De-Slopping, Comment Purging, Structural Invariant Encoding, Anti-AI Boilerplate |
| **Trigger Phrases** | `"unslop"`, `"no comments"`, `"clean up slop"`, `"encode constraints"` |
| **Prerequisites** | TypeScript/Python/Rust compiler, linter (Ruff, ESLint, Clippy), Git 2.40+ |

AI code generation often leaves behind excessive conversational slop, verbose paragraph-long explanations for trivial operations, commented-out dead code, and defensive warning comments (`// IMPORTANT: do not remove!`). The **Anti-Slop Code Hygiene Protocol** enforces aggressive comment elimination and dictates that invariants MUST be encoded into compiler types, runtime validation schemas, or CI linters rather than inline prose.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Anti-Slop Hygiene (Rules R-213 & R-214)**:
> *Comments in business code are confessions of structural debt. Encode constraints in structure, not sermons.*
> If a developer feels compelled to write `// do not delete this, auth breaks!`, the system architecture is broken. Replace that comment with a compile-time branded type, an automated regression test, or a static CI assertion. Furthermore, all AI conversational fluff, sycophancy, status narrations, and unsolicited ASCII banners MUST be eliminated completely.

```
                  COMMENT TRIAGE & STRUCTURAL ENCODING
                  
                       [Target Code / Inline Comment]
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
    [The 5 Allowed Exceptions]                      [Unapproved Comments ("Meat")]
    1. Legal / License headers                      - Workaround apologies
    2. Foreign platform/protocol gotchas            - Narration ("loop through items")
    3. Public API contract docs                     - Commented-out dead code
    4. Issue / RFC links for external limits       - Warnings ("do not change this")
    5. Specific justified linter ignores            - Sycophantic AI status notes
               │                                             │
               ▼                                             ▼
          KEEP IN PLACE                             PURGE IMMEDIATELY
                                                             │
                                                             ▼
                                                    [Structural Encoding]
                                                    Can code express invariant?
                                                    ├── YES: Add type or CI check
                                                    └── NO:  File tracking issue
```

---

## 3. Architecture & Design Patterns

### 3.1 The 5 Allowed Comment Exceptions

Only five categories of comments are permitted to remain in production codebases:
1. **Legal & License Headers**: Copyright, SPDX license identifiers, and formal disclaimers required by law.
2. **Foreign Platform / Protocol Gotchas**: Non-obvious workarounds forced by an external OS, third-party vendor library, or wire protocol that cannot be reshaped.
3. **Public API Contract Documentation**: Docstrings (JSDoc, Python docstrings, Rustdoc) defining the public function signature, parameters, return types, and exceptions for external consumers.
4. **Formal Specification & Issue Links**: Direct URLs citing RFC standards, W3C specifications, or upstream vendor issue trackers explaining a constraint code cannot represent.
5. **Legitimate Linter Suppressions**: Suppressions targeting third-party typings or proven false-positive bugs in tooling (never suppressing type errors in business code).

### 3.2 Structural Encoding: Replacing Prose with Architecture

When encountering defensive comments, transform them into structural invariants:

| Anti-Pattern Comment | Structural Replacement |
|---|---|
| `// user_id must be a positive integer` | Branded type: `type UserId = Brand<number, "UserId">` + Zod schema validation |
| `// IMPORTANT: must call authenticate() before query()` | Session token parameter injection: `query(auth: AuthSession, ...)` |
| `// do not call this with null, crashes backend` | Non-nullable type: `name: string` (strict null checks enabled) |
| `// retry max 3 times if gateway timeouts` | Resilient middleware: `withRetryPolicy(call, { maxRetries: 3 })` |
| `// DO NOT MODIFY: format required by legacy billing` | Golden schema snapshot test or dedicated serialization adapter |

### 3.3 Anti-AI Slop Standards (Rule R-214)

Automated agents MUST adhere to these communication anti-slop rules:
- **No Sycophantic Greetings**: Never output *"Certainly! I'd be more than happy to help you with that!"* or *"Great choice!"*.
- **No Apology Loops**: Never output *"I apologize for the confusion earlier."* State what failed, why, and the exact remediation.
- **No ASCII Banner Flourishes**: Never prepend decorative ASCII art borders or emojis across multiple lines.
- **No Obvious Narration**: Never explain standard language syntax (e.g. *"Here we use a for loop to iterate over the array"*). State the engineering problem and the structural solution.

---

## 4. Concrete Code Examples

### 4.1 Automated Comment & Slop Purger (`unslop_auditor.py`)

```python
#!/usr/bin/env python3
"""AST-based comment auditor that flags unapproved comments and AI slop."""

from __future__ import annotations
import re
import sys
from typing import List, Tuple

ALLOWED_PATTERNS = [
    re.compile(r"^\s*(#|//|\*)\s*(SPDX-License-Identifier|Copyright|\(c\))", re.IGNORECASE),
    re.compile(r"https?://(github\.com|ietf\.org|rfc-editor\.org|w3\.org)/", re.IGNORECASE),
    re.compile(r"^\s*(#|//)\s*(prettier-ignore|eslint-disable-next-line|@ts-expect-error)", re.IGNORECASE)
]

SLOP_PATTERNS = [
    re.compile(r"^\s*(#|//)\s*(TODO|FIXME|XXX|HACK):", re.IGNORECASE),
    re.compile(r"^\s*(#|//)\s*(do not (change|remove|delete)|important|be careful)", re.IGNORECASE),
    re.compile(r"^\s*(#|//)\s*(loop through|helper function to|initialize variable)", re.IGNORECASE)
]

def audit_file_comments(file_path: str) -> List[Tuple[int, str, str]]:
    """Scan file and flag comments violating Anti-Slop Rule R-213."""
    violations = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith(("//", "#", "/*")):
                # Check if matches allowed exception
                if any(p.search(stripped) for p in ALLOWED_PATTERNS):
                    continue
                # Check if matches known slop pattern
                for sp in SLOP_PATTERNS:
                    if sp.search(stripped):
                        violations.append((idx, stripped, "Unsolicited warning or narration comment"))
                        break
    return violations

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: unslop_auditor.py <file_path>")
        sys.exit(2)
    target = sys.argv[1]
    issues = audit_file_comments(target)
    if issues:
        print(f"❌ Found {len(issues)} unslop violations in {target}:")
        for line_no, text, reason in issues:
            print(f"  Line {line_no}: {text} ({reason})")
        sys.exit(1)
    print(f"✅ {target} is 100% clean of slop comments.")
```

---

## 5. Security & Performance Considerations

- **Secrets in Commented Code**: Attackers frequently inspect git histories or comments for disabled credentials (`// api_key = "sk_live_..."`). All commented code must be purged.
- **Accidental Deletion of Pragmas**: Never strip compiler pragmas required for safety (e.g. `// @ts-check` in JavaScript or `#pragma once` in C++).
- **Public API Documentation Preserved**: Docstrings on exported library symbols MUST NOT be deleted; they constitute user-facing documentation.

---

## 6. Common Pitfalls & Anti-Patterns

### ❌ Anti-Pattern 1: The Apologetic Workaround Comment
```python
# BAD: Leaving a long workaround comment apologizing for bad architecture
# This is a temporary hack because the user service returns 404 instead of 401
# when the token is missing. Please do not touch this until service v2 is deployed.
if response.status_code == 404:
    return handle_unauthorized()
```
```python
# GOOD: Structural adapter isolating external service quirk cleanly
def parse_auth_response(response: ServiceResponse) -> AuthResult:
    """Isolate legacy vendor status code mapping at external network boundary."""
    if response.status_code in (401, 404):
        return AuthResult.UNAUTHORIZED
    return AuthResult.SUCCESS
```

### ❌ Anti-Pattern 2: Conversational Filler in PR Reviews
```markdown
<!-- BAD: Conversational sycophancy and filler -->
"Hi team! I hope you are having a wonderful Monday. Thank you so much for this amazing PR!
I noticed a tiny little thing on line 45, if you don't mind taking a quick look when you have a moment!"
```
```markdown
<!-- GOOD: Factual, direct, and concise feedback -->
Line 45: Potential null dereference when `user.profile` is undefined. Add non-null assertion or optional chaining `user.profile?.avatarUrl`.
```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Zero Slop Comments** | 0 forbidden comment warnings | Run `python unslop_auditor.py <file>` |
| **2. Zero Deferred Markers** | 0 TODO / FIXME / HACK occurrences | `git grep -EIn "(TODO|FIXME|HACK):"` returns 0 |
| **3. Structural Invariants** | Invariants enforced by types/linters | Typecheck passes without `@ts-ignore` |
| **4. Communication Cleanliness** | 0 AI filler / sycophancy phrases | PR description leads directly with problem |
| **5. License Integrity** | Legal / copyright headers preserved | License headers remain intact at top of file |

---

*See also*: [`agents/poteto-discipline.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/poteto-discipline.md) for surgical diff standards and [`workflows/code-review-standards.md`](file:///home/agy/.t3/userdata/attachments/devskill/workflows/code-review-standards.md) for PR review checklists.
