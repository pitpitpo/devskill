# 🧠 Compound Engineering & Solution Knowledge Base Architecture (`agents/compound-engineering-knowledge.md`)

> **Standard Identifier**: `AGT-COMPOUND-001`  
> **Status**: Active / Production Standard (Synthesizing `EveryInc/compound-engineering-plugin`, ADR standards, and Institutional Memory Compounding)  
> **Governing Rules**: **R-001**, **R-016**, **R-046**, **R-244**, **R-250**, **R-277**  
> **Last Updated**: 2026-11-20  

---

## 1. Frontmatter & Metadata

- **Purpose**: Systematizing the compounding engineering loop (`Brainstorm → Plan → Work → Review → Compound`) and managing durable, searchable repository solution documents (`docs/solutions/`, `MISTAKES.md`, ADRs) so future agent sessions never repeat solved mistakes.
- **Applicability**: Engineering repositories maintaining persistent institutional memory across multi-agent workflows and multi-session lifecycles.
- **Prerequisites**: Markdown-enabled repository, Git version control, CI quality gates.

---

## 2. Core Philosophy / Golden Rule

> **Golden Rule**: *Every resolved incident, non-obvious bug fix, subtle library trap, or architectural trade-off MUST compound into a durable repository artifact. If an engineer or agent spends 30 minutes debugging a defect and leaves without codifying the lesson into `docs/solutions/`, `MISTAKES.md`, or an automated lint/test assertion, that engineering investment is lost.*

---

## 3. Architecture & Design Patterns

Ephemeral chat transcripts vanish when sessions conclude. Compound Engineering creates an **institutional memory loop** where each completed task makes future tasks faster, safer, and cheaper.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE COMPOUND ENGINEERING LOOP                        │
├────────────────────────────────────────────────────────────────────────┤
│  1. BRAINSTORM & DISCOVERY                                             │
│  • Check `docs/solutions/` and `MISTAKES.md` for known patterns        │
│  • Clarify assumptions & invalidate faulty premises (/office-hours)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Pre-Validated Plan
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  2. IMPLEMENTATION & MINIMAL DIFF                                      │
│  • Worktree-isolated development + Red-Green TDD reproduction          │
│  • Surgical edits preserving unrelated codebase structure              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Working Code
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  3. TWO-STAGE REVIEW & DESLOPPING                                      │
│  • Stage 1: Acceptance Criteria Spec Compliance                        │
│  • Stage 2: Code Quality, OWASP Security & Anti-Slop Cleanup           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Verified Pull Request
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  4. COMPOUND TO REPOSITORY MEMORY (`/compound`)                        │
│  • Generate standardized markdown record in `docs/solutions/<topic>.md`│
│  • Append critical traps to `MISTAKES.md`                             │
│  • Codify automated mechanical checks in CI / ESLint / Ruff / Tests    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Canonical Solution Artifact Template (`docs/solutions/2026-11-pgbouncer-transaction-pooling.md`)

```markdown
# Solution: PgBouncer Transaction Pooling Prepared Statement Mismatch

> **Identifier**: `SOL-DB-0042`  
> **Severity**: High (Intermittent 500 crashes during high-traffic spikes)  
> **First Observed**: 2026-11-18  
> **Resolved By**: Engineering Team  
> **Keywords**: pgbouncer, postgresql, prepared-statements, connection-pooling, prisma  

---

## 1. Problem Signature & Symptoms
- Error Message: `ERROR: prepared statement "s0" already exists` or `prepared statement does not exist`.
- Context: Triggered when Prisma ORM connected through PgBouncer operating in `pool_mode = transaction`.
- Impact: Intermittent query failures across authentication and checkout endpoints under traffic > 2,000 req/sec.

---

## 2. Root Cause Analysis
PgBouncer in `transaction` mode reassigns server connections between transactions. When an ORM uses named prepared statements by default, it registers them on the specific underlying server backend. When the next transaction reuses a different connection, the statement does not exist; or when another client reuses the first connection, the statement name collides.

---

## 3. Verified Solution Diff

```diff
// prisma/schema.prisma
datasource db {
  provider  = "postgresql"
- url       = env("DATABASE_URL")
+ url       = env("DATABASE_URL") // Connection to PgBouncer port 6432
+ directUrl = env("DIRECT_DATABASE_URL") // Direct connection for migrations port 5432
}

// src/lib/db.ts
import { PrismaClient } from '@prisma/client';

export const db = new PrismaClient({
  datasources: {
    db: {
+     // Disable named prepared statements for transaction pooler compatibility
+     url: `${process.env.DATABASE_URL}?pgbouncer=true&connection_limit=1`,
    },
  },
});
```

---

## 4. Anti-Recurrence Gate (Automated Invariant)
Added automated assertion to database configuration test suite:
```typescript
// tests/integration/db-config.test.ts
import { expect, test } from 'vitest';

test('database connection string contains pgbouncer parameter in production config', () => {
  const url = process.env.DATABASE_URL || '';
  if (url.includes(':6432')) {
    expect(url).toContain('pgbouncer=true');
  }
});
```
```

### 4.2 Automated Compounding Script (`scripts/compound-solution.py`)

```python
#!/usr/bin/env python3
import argparse
import datetime
import sys
from pathlib import Path

SOLUTION_TEMPLATE = """# Solution: {title}

> **Identifier**: `SOL-{date}-{slug}`  
> **Date**: {date}  
> **Keywords**: {keywords}  

---

## 1. Problem Signature
{problem}

---

## 2. Root Cause
{root_cause}

---

## 3. Verified Solution
{solution}

---

## 4. Anti-Recurrence Invariant (Tests / CI)
{prevention}
"""

def create_solution(title: str, keywords: str, problem: str, root_cause: str, solution: str, prevention: str) -> Path:
    today = datetime.date.today().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-").replace("/", "-")[:40]
    filename = f"{today}-{slug}.md"
    
    solutions_dir = Path("docs/solutions")
    solutions_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = solutions_dir / filename
    content = SOLUTION_TEMPLATE.format(
        title=title,
        date=today,
        slug=slug,
        keywords=keywords,
        problem=problem,
        root_cause=root_cause,
        solution=solution,
        prevention=prevention,
    )
    
    filepath.write_text(content, encoding="utf-8")
    print(f"Compounded solution created at: {filepath}")
    return filepath

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a standardized solution record")
    parser.add_argument("--title", required=True, help="Descriptive title of the solution")
    parser.add_argument("--keywords", required=True, help="Comma-separated searchable keywords")
    args = parser.parse_args()
    
    create_solution(
        title=args.title,
        keywords=args.keywords,
        problem="[Describe symptoms and exact error message]",
        root_cause="[Explain the technical root cause]",
        solution="[Provide the code diff or configuration change]",
        prevention="[Document the automated test or CI check enforcing anti-recurrence]",
    )
```

---

## 5. Security & Performance Considerations

1. **Zero Secret Leakage in Solutions**:
   - Solution documents must NEVER contain real passwords, customer API keys, production IP addresses, or unmasked database connection strings.
   - All connection examples must use standard placeholder environments (`env("DATABASE_URL")`).
2. **Searchability & Token Indexing**:
   - Solutions are indexed with descriptive keywords in YAML or frontmatter headers so agent search tools (`ripgrep`, `grep`) can discover them in milliseconds using error strings.
3. **Pruning & Maintenance**:
   - Outdated solutions superseded by upstream framework changes should be marked `[DEPRECATED: Replaced by Framework X in version Y]` rather than silently deleted, preserving architectural history.

---

## 6. Common Pitfalls & Anti-Patterns

- ❌ **Failing to Document the Anti-Recurrence Gate**: Simply explaining what went wrong without adding an automated test or linter rule means future contributors can re-introduce the bug.
- ❌ **Storing Solutions in Ephemeral Chat Logs**: Explaining the bug to the user in chat without writing it down to disk ensures the next agent starting a new session starts from zero knowledge.
- ❌ **Vague Problem Signatures**: Documenting "fixed database error" without quoting the exact error message or stack trace prevents future agents from matching on the failure string.
- ❌ **Over-Engineering Solution Documents**: Writing 20 pages of narrative prose when a 1-page structured markdown file with problem, root cause, diff, and test provides 100% of the value.

---

## 7. Verification Checklist

- [ ] Structured markdown record created in `docs/solutions/<YYYY-MM-DD-slug>.md` or appended to `MISTAKES.md`.
- [ ] Exact error message, symptoms, and environment conditions recorded in Problem Signature.
- [ ] Technical root cause clearly articulated without hand-waving.
- [ ] Minimal code/config diff provided showing the verified fix.
- [ ] Automated regression test, linter rule, or CI gate check implemented to prevent recurrence.
- [ ] Zero production secrets, private keys, or PII contained in the solution document.
