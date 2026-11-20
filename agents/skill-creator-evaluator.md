# 🛠️ Agent Skill Creator, Progressive Disclosure & Evaluation Benchmarking (`agents/skill-creator-evaluator.md`)

> **Standard Identifier**: `AGT-SKILL-CREATOR-001`  
> **Status**: Active / Production Standard (Synthesizing `agentskills.io`, Anthropic `skill-creator`, and Linux Foundation AAIF `AGENTS.md`)  
> **Governing Rules**: **R-001**, **R-034**, **R-181**, **R-190**, **R-276**  
> **Last Updated**: 2026-11-20  

---

## 1. Frontmatter & Metadata

- **Purpose**: Authoring, testing, benchmarking, and maintaining production-grade Agent Skills conforming to the open `agentskills.io` standard with zero context bloat and measurable eval pass rates.
- **Applicability**: AI agent skills, plugins, slash commands, and domain playbooks across Claude Code, Cursor, Codex, OpenCode, Antigravity, and Gemini CLI harnesses.
- **Prerequisites**: Python 3.11+, PyYAML, `validate-skill.py`, or equivalent repository schema validators.

---

## 2. Core Philosophy / Golden Rule

> **Golden Rule**: *An agent skill is software: it must have strict specifications, progressive disclosure architecture (< 500 lines at the root), deterministic syntax validation, and empirical evaluation test suites. Never ship an unbenchmarked prompt or conversational essay as an agent skill.*

---

## 3. Architecture & Design Patterns

Skills are modular, reusable directories designed to instruct AI agents on domain-specific engineering workflows. An effective skill balances **immediate concise routing** with **deep progressive reference documentation**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SKILL DIRECTORY TOPOLOGY                        │
├────────────────────────────────────────────────────────────────────────┤
│  SKILL ROOT: `skills/<skill-name>/`                                    │
│  ├── SKILL.md                 # Mandatory canonical entrypoint (<500 lines)
│  │   ├── YAML Frontmatter     # name, description, trigger keywords   │
│  │   └── Execution Playbook   # Step-by-step operational instructions  │
│  ├── scripts/                 # Optional deterministic Python/Bash utilities
│  ├── references/              # Detailed API tables, domain deep-dives │
│  └── evals/                   # Test cases, input prompts & pass criteria
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Evaluated By
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  THE THREE-TIER EVALUATION HARNESS                                     │
│  • Tier 1: Schema & Link Linting (`validate-skill.py`)                │
│  • Tier 2: Static Token & Line Ceiling Gate (< 500 lines per file)    │
│  • Tier 3: Behavioral Execution Eval (Model invocation against rubric) │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Progressive Disclosure Principle
An AI agent has a finite context window. Loading a monolithic 5,000-line skill crashes performance and causes Context Rot:
1. **Tier 1 (Root `SKILL.md`)**: Contains ONLY the high-frequency decision tree, invariant rules, and immediate CLI workflow. Must be under **500 lines**.
2. **Tier 2 (`references/*.md`)**: Detailed API specifications, edge-case tables, and deep-dive checklists loaded *only when triggered* by specific tasks.
3. **Tier 3 (`scripts/*`)**: Deterministic verification tasks delegated to executable code rather than probabilistic model reasoning.

---

## 4. Concrete Code Examples

### 4.1 Canonical `SKILL.md` Template with `agentskills.io` Frontmatter

```markdown
---
name: database-migration-safeguard
description: Zero-downtime database migrations, lock timeout safety, and expand/contract table schema alterations for PostgreSQL 16+.
version: "1.0.0"
author: "DevSkill Platform Team"
license: "MIT"
tags: [database, postgresql, migrations, ddl, locks]
---

# 🐘 PostgreSQL Zero-Downtime Migration Safeguard

> **Golden Rule**: *Never acquire table-exclusive locks without setting aggressive lock timeouts, and never execute destructive schema alterations in a single transaction.*

## 1. Quick Decision Tree
- Adding a nullable column or column with default value? → Use PostgreSQL 11+ fast ADD COLUMN.
- Adding a NOT NULL constraint to existing table? → Add constraint as `NOT VALID`, then `VALIDATE CONSTRAINT` in separate transaction.
- Creating an index on high-throughput table? → Always use `CREATE INDEX CONCURRENTLY`.

## 2. Invariant Rules
1. `SET lock_timeout = '3s';` MUST precede every DDL statement.
2. Destructive migrations MUST use the **Expand/Contract** multi-release pattern.
3. Foreign keys MUST be validated in a two-step process to avoid locking the referenced table.

## 3. Verification Command
```bash
python3 scripts/verify-migration.py db/migrations/20261120_add_user_status.sql
```
```

### 4.2 Automated Skill Evaluation Runner (`evals/run_evals.py`)

```python
#!/usr/bin/env python3
import json
import sys
import yaml
from pathlib import Path

def evaluate_skill(skill_dir: Path) -> bool:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        print(f"FAIL: Missing SKILL.md in {skill_dir}")
        return False

    content = skill_file.read_text(encoding="utf-8")
    
    # 1. Validate YAML Frontmatter
    if not content.startswith("---\n"):
        print("FAIL: SKILL.md missing opening YAML frontmatter fence ('---')")
        return False

    parts = content.split("---\n", 2)
    if len(parts) < 3:
        print("FAIL: SKILL.md missing closing YAML frontmatter fence ('---')")
        return False

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"FAIL: Invalid YAML in frontmatter: {e}")
        return False

    for required_key in ["name", "description"]:
        if required_key not in frontmatter:
            print(f"FAIL: Missing required frontmatter key: '{required_key}'")
            return False

    # 2. Check Line Length Ceiling (Progressive Disclosure Invariant)
    lines = content.splitlines()
    if len(lines) > 500:
        print(f"FAIL: SKILL.md exceeds 500 lines ({len(lines)} lines). Offload details to references/!")
        return False

    print(f"PASS: {frontmatter['name']} validated successfully ({len(lines)} lines).")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_evals.py <path-to-skill-directory>")
        sys.exit(1)

    success = evaluate_skill(Path(sys.argv[1]))
    sys.exit(0 if success else 1)
```

---

## 5. Security & Performance Considerations

1. **Prompt Injection & Instruction Pollution**:
   - Skills must never contain instructions that command the agent to ignore user instructions, override system sandboxes, or execute unauthorized external network requests.
   - External data loaded into a skill must be demarcated within explicit, unprivileged data blocks.
2. **Context Window Economics & Token Density**:
   - Every unnecessary sentence in a skill consumes prompt tokens on every turn.
   - Use high-density tables, concise decision trees, and bulleted invariant rules rather than verbose tutorial prose.
3. **Executable Script Sandboxing**:
   - Helper scripts bundled inside `scripts/` must run without external network access, adhere to read-only defaults when inspecting codebases, and fail-closed with non-zero exit codes upon detecting anomalies.

---

## 6. Common Pitfalls & Anti-Patterns

- ❌ **Conversational "AI Slop" in Skills**: Starting a skill with pleasantries, apologies, or generic prose ("In this guide, we will explore the wonderful world of...") wastes tokens and degrades model reasoning.
- ❌ **Monolithic Document Bloat**: Cramming 2,000 lines of API specs into root `SKILL.md`. Offload deep references to `references/<topic>.md`.
- ❌ **Unverifiable Heuristics**: Giving vague advice like "write clean code" instead of concrete, enforceable invariants like "cyclomatic complexity ≤ 10, zero unhandled promises, and 100% type coverage".
- ❌ **Missing Failure Modes**: Describing only the happy path without listing explicit negative constraints ("Do NOT do X", "Prohibited Actions").

---

## 7. Verification Checklist

- [ ] Skill resides in a dedicated directory with a root `SKILL.md` entrypoint.
- [ ] Valid YAML frontmatter containing `name` and `description` defined at the top.
- [ ] Root `SKILL.md` line count is strictly under 500 lines (progressive disclosure).
- [ ] Deep technical specifications and reference tables partitioned into `references/`.
- [ ] Deterministic verification commands and test scripts bundled in `scripts/`.
- [ ] Invariant rules, prohibited actions, and golden rules explicitly stated.
- [ ] Schema, links, and syntax pass `validate-skill.py` with 0 errors.
