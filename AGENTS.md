# AGENTS.md — Universal Repository Instructions for AI Coding Agents

> **Standard**: Open `AGENTS.md` Specification (Linux Foundation Agentic AI Foundation / AAIF)  
> **Applies To**: Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, and all autonomous coding agents operating in this repository or consuming `devskill`.  
> **Skill Entrypoint**: [SKILL.md](SKILL.md) | **Detailed Agent Protocols**: [agents.md](agents.md)

---

## 1. Progressive Disclosure Read Order

Load ONLY the files needed for your task archetype — do not dump the entire repository into context:

1. **Classify the task** using [ROUTING.md](ROUTING.md) (28 task archetypes → exact 3–5 file reading list + required verification commands).
2. **Enforce non-negotiable invariants** from [RULES.md](RULES.md) (R-001 through R-260) and [security.md](security.md) (OWASP Top 10:2025, OWASP Agentic ASI01–ASI10, NIST SP 800-63B-4, NIST PQC).
3. **Locate domain guides fast** via [index.json](index.json) (machine-readable catalog with tags, archetypes, and exact paths).
4. **Apply unified agent stack discipline** from [agents/unified-agent-stacks.md](agents/unified-agent-stacks.md) (`pstack`, `tstack`, `gstack`, `kstack`, `superpowers`, `compound-engineering`), [agents/code-forensics-interrogation.md](agents/code-forensics-interrogation.md), and [agents.md](agents.md) (Always/Ask/Never boundaries, 3-strike escalation).

---

## 2. Non-Negotiable Engineering Invariants

- **Zero Placeholders & Zero Mock Data in Production**: Never ship `TODO`/`FIXME`/`TBD` stubs (R-001) or hardcoded mock records in production paths (R-002).
- **Direct Execution Proof**: Never claim tests, builds, or linters passed without executing them and verifying Exit Code `0` (R-004, R-181, R-202).
- **Red-Green TDD on Bug Fixes**: Reproduce defects with a failing test before modifying production code (R-005, R-183).
- **Strict Static Typing & Boundary Validation**: Ban `any` / `@ts-ignore` / `# type: ignore` (R-034). Validate every external boundary with Zod, Pydantic, or strict schemas (R-060).
- **Security by Default**: Parameterized queries only (R-061), tenant-scoped AuthZ / zero IDOR (R-063), zero secrets in git (R-064), fail-closed error handling (OWASP A10:2025 / R-232), and least-agency tool permissions (OWASP ASI02/ASI03 / R-228).
- **Surgical Diffs**: Modify only lines required for the task (R-015, R-182). Never weaken or delete tests to force green (R-011, R-096).

---

## 3. Repository Commands & Quality Gates

| Task | Command |
|---|---|
| **Validate DevSkill Integrity & Index Parity** | `python3 scripts/validate-skill.py` |
| **Regenerate `index.json` Deterministically** | `python3 scripts/validate-skill.py --write-index` |
| **Run DevSkill Script Unit Tests** | `python3 -m unittest discover -s scripts -p "test_*.py" -v` |
| **Run CI Quality Gate Scan (Repo)** | `./scripts/ci-gate.sh` |
| **Run CI Quality Gate Scan (Staged)** | `./scripts/ci-gate.sh --staged` |
| **Watch a GitHub PR (Event-Driven)** | `python3 scripts/pr-wait.py <pr-num> --until ready` |

---

## 4. Ship Gate Threshold

Every completed task MUST satisfy the Dual-Threshold Ship Gate in [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md):
- **Total Score ≥ 95 / 100** AND **Every individual category ≥ 9.0 / 10 relative**.
- All verification commands executed cleanly with **Exit Code 0**.
