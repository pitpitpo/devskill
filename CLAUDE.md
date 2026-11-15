# 🤖 Claude Code Guidelines & Configuration (`CLAUDE.md`)

> **Integration Scope**: Claude Code CLI, Claude Desktop, and Anthropics Developer Tooling  
> **Mandatory Core Imports**:
> - [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md) — Autonomous agent operating protocols, personas, boundaries, and reporting formats.
> - [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) — Non-negotiable engineering rules (R-001 through R-180+) and CI scan patterns.

---

## 1. Core Operating Principles

When Claude Code is active within this repository, it MUST adhere strictly to the protocols defined in [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md) and the rules in [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md):

1. **Anti-Hallucination & Truth Grounding**:
   - Verify every library API, package name, and schema by reading local files or package manifests before writing code.
   - If a fact or package version cannot be confirmed, write `UNVERIFIED` and request clarification.
2. **Zero Laziness & Complete Implementation**:
   - Zero `TODO`, `FIXME`, or stub markers in production files (R-001).
   - Zero mock or fake data in production paths (R-002).
   - Emit complete file contents without truncation or `// rest of code here` comments (R-008).
3. **Surgical Diff Discipline**:
   - Touch only the lines and files required for the task. Never perform unsolicited refactoring or restyling (R-015, R-016).

---

## 2. Plan Mode Settings

Claude Code supports iterative planning and execution. For all non-trivial tasks (defined as touching > 2 files or introducing new database schemas / API routes), Claude Code MUST operate in **Plan Mode**:

```
[Enter Plan Mode] ──► [Phase 1: Understand & Parse] ──► [Phase 2: Research & Inspect Code]
                                                                     │
                                                                     ▼
[Await User Approval] ◄── [Phase 3: Generate Plan Spec] ◄────────────┘
         │
         ├── APPROVED ──► [Enter Execution Mode: Phases 4-8]
         └── REJECTED ──► [Revise Hypotheses & Plan]
```

### Plan Mode Guidelines:
- **Trigger**: Tasks modifying architecture, adding endpoints, altering database schemas, or refactoring modules.
- **Artifact**: Generate a structured plan detailing:
  1. Root cause or architectural intent.
  2. Exact files to be created or modified.
  3. Domain models and interface definitions adhering to [`specs.md`](file:///home/agy/.t3/userdata/attachments/devskill/specs.md).
  4. Test plan covering Unit, Integration, and negative failure paths.
  5. Potential risks and rollback strategies.
- **Approval Gate**: Do not execute state-modifying tools (`write_to_file`, `replace_file_content`, database migrations) until the plan has been reviewed and approved.

---

## 3. Permission Boundaries

Claude Code must enforce strict command and tool authorization boundaries:

| Permission Level | Permitted Operations |
|---|---|
| **AUTO-APPROVED (Allowed)** | • Reading files, searching code, inspecting git diffs (`git status`, `git diff`).<br>• Running linters, formatters, and typecheckers (`npm run lint`, `mypy`, `ruff`).<br>• Executing test suites in local read-only containers (`npm test`, `pytest`).<br>• Writing and editing source files inside the repository directory.<br>• Creating git branches and running local non-destructive commits. |
| **USER CONFIRMATION REQUIRED (Ask)** | • Adding new external dependencies to `package.json` or `pyproject.toml`.<br>• Applying database migrations or altering database schemas.<br>• Modifying CI/CD workflow manifests (`.github/workflows/`).<br>• Deleting files or removing obsolete functions.<br>• Git operations pushing to remote branches or altering tags. |
| **STRICTLY FORBIDDEN (Never)** | • Destructive shell commands: `rm -rf /`, formatting drives, dropping databases (R-171).<br>• Force-pushing to protected git branches (`git push --force origin main`).<br>• Global system modifications: `sudo`, `apt install`, `npm install -g` (R-174).<br>• Reading or traversing parent host directories (`/etc`, `/root`, `~/.ssh`) (R-173).<br>• Committing plaintext secrets or API keys (R-064).<br>• Modifying tests to force a pass without changing application code (R-011, R-096). |

---

## 4. Hook Configurations

Integrate Claude Code with local git hooks and development scripts to ensure automated enforcement before code reaches review.

### 4.1 Pre-Commit Hook (`.husky/pre-commit` or `.git/hooks/pre-commit`)
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> [Claude Code Hook] Running pre-commit validation..."

# 1. Block forbidden patterns (TODO, mock data, any types, swallowed errors)
bash /home/agy/.t3/userdata/attachments/devskill/RULES.md

# 2. Run static linter and typecheck
npm run lint
npm run typecheck

# 3. Secret scan
if command -v gitleaks &> /dev/null; then
  gitleaks protect --staged --verbose
fi

echo "✅ Pre-commit hook completed cleanly."
```

### 4.2 Post-Edit Verification Hook
After Claude Code completes editing or writing code files, it must automatically execute the relevant localized test runner:
```bash
# For TypeScript / Node.js
npm test -- --findRelatedTests <modified-file>

# For Python
pytest -v <test-file-corresponding-to-edit>
```

### 4.3 Definition of Done Ship Gate Check
Before generating the final delivery report, Claude Code MUST execute the full project verification command:
```bash
make verify
# OR
npm run verify
```
Confirm exit code 0 and self-assess against [`DEFINITION_OF_DONE.md`](file:///home/agy/.t3/userdata/attachments/devskill/DEFINITION_OF_DONE.md) (Threshold: Every category ≥ 9/10 relative, Total ≥ 95/100).

---

## 5. Standard Project Commands

Claude Code should reference these standardized commands for build, test, and verification workflows:

- **Install Dependencies**: `npm ci` / `poetry install --no-root` (Frozen immutable installs; R-118)
- **Lint & Format**: `npm run lint` / `ruff check .`
- **Typecheck**: `npm run typecheck` / `mypy --strict .`
- **Run Unit Tests**: `npm test` / `pytest -v tests/unit/`
- **Run Integration Tests**: `npm run test:integration` / `pytest -v tests/integration/`
- **One-Step Full Gate**: `make verify` / `npm run verify`
