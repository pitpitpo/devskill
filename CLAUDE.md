# 🤖 Claude Code Guidelines & Configuration (`CLAUDE.md`)

> **Integration Scope**: Claude Code CLI, Claude Code IDE Extensions, Claude Desktop, and Anthropic Developer Tooling  
> **Universal Sibling Standard**: [`AGENTS.md`](AGENTS.md)  
> **Mandatory Core Imports**:
> - [`BOOTSTRAP.md`](BOOTSTRAP.md) — URL-only agent intro point and remote activation protocol.
> - [`agents.md`](agents.md) — Autonomous agent operating protocols, personas, boundaries, and reporting formats.
> - [`RULES.md`](RULES.md) — Non-negotiable engineering rules (R-001 through R-272) and CI scan patterns.
> - [`ROUTING.md`](ROUTING.md) — Deterministic 30-archetype task router and reading lists.

---

## 1. Core Operating Principles

When Claude Code operates in a repository governed by DevSkill, it MUST adhere strictly to [`agents.md`](agents.md) and [`RULES.md`](RULES.md):

1. **Anti-Hallucination & Truth Grounding (R-003, R-006)**:
   - Verify every library API, package name, and schema by reading local manifests or installed definitions before writing code.
   - If a fact or package version cannot be confirmed, write `UNVERIFIED` and request clarification.
2. **Zero Laziness & Complete Implementation (R-001, R-002, R-008)**:
   - Zero `TODO`, `FIXME`, `TBD`, or stub markers in production files.
   - Zero mock or fake data in production paths.
   - Emit complete file contents without truncation or placeholder ellipses.
3. **Surgical Diff Discipline & Direct Proof (R-015, R-181, R-182, R-202)**:
   - Touch only the lines and files required for the task. Never perform unsolicited refactoring or restyling.
   - Never declare completion without executing concrete verification commands and observing Exit Code `0`.

---

## 2. Plan Mode Settings

For all non-trivial tasks (touching > 2 files, modifying database schemas, adding public API routes, or altering auth/security boundaries), Claude Code MUST operate in **Plan Mode**:

```
[Enter Plan Mode] ──► [Phase 1: Understand & Route via ROUTING.md] ──► [Phase 2: Inspect Code]
                                                                               │
                                                                               ▼
[Await User Approval] ◄── [Phase 3: Generate Concrete Plan Spec] ◄─────────────┘
         │
         ├── APPROVED ──► [Enter Execution Mode: Phases 4–8]
         └── REJECTED ──► [Revise Hypotheses & Plan]
```

### Plan Artifact Requirements:
1. Root cause or architectural intent (citing [`decisions.md`](decisions.md) when choosing technologies).
2. Exact files to be created or modified.
3. Domain models, boundary schemas, and interface contracts adhering to [`specs.md`](specs.md).
4. Test plan covering unit, integration (real DB), and negative/boundary failure paths.
5. Blast-radius assessment and rollback strategy.

---

## 3. Permission Boundaries

| Permission Level | Permitted Operations |
|---|---|
| **AUTO-APPROVED (Allowed)** | • Reading files, searching code, inspecting git diffs (`git status`, `git diff`).<br>• Running linters, formatters, typecheckers (`ruff`, `eslint`, `tsc`/`tsgo`, `mypy`).<br>• Executing local test suites (`npm test`, `pytest`, `go test`, `python3 -m unittest`).<br>• Writing and editing source files inside the repository workspace.<br>• Creating local branches and atomic Conventional Commits. |
| **USER CONFIRMATION REQUIRED (Ask)** | • Adding new external dependencies to `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod`.<br>• Applying database migrations or altering production schemas.<br>• Modifying CI/CD workflow manifests (`.github/workflows/`).<br>• Deleting files or deprecating public APIs.<br>• Pushing to remote branches, tagging releases, or modifying MCP server configs. |
| **STRICTLY FORBIDDEN (Never)** | • Destructive shell commands: `rm -rf /`, formatting drives, `DROP DATABASE` (R-171).<br>• Force-pushing without lease (`git push --force`) or bypassing branch protection (`gh pr merge --admin`) (R-201, R-207).<br>• Global host modifications: `sudo`, `apt install`, `npm install -g` (R-174).<br>• Reading host directories outside workspace (`/etc`, `/root`, `~/.ssh`) (R-173).<br>• Committing plaintext secrets or API keys (R-064).<br>• Weakening or deleting failing tests to force green (R-011, R-096). |

---

## 4. Declarative Harness Hooks (`.claude/settings.json`) — R-233

Prose rules in `CLAUDE.md` can drift under long context windows; **Claude Code Hooks** enforce hard, deterministic guardrails at the harness boundary. Copy [`scaffolding/configs/.claude-settings.json`](scaffolding/configs/.claude-settings.json) into `.claude/settings.json` (team-shared) or `~/.claude/settings.json` (global):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c 'import json,re,sys; cmd=json.load(sys.stdin).get(\"tool_input\",{}).get(\"command\",\"\"); bad=r\"(rm\\s+-rf\\s+/|git\\s+push\\s+(-f|--force)\\b|gh\\s+pr\\s+merge\\s+.*--admin|sudo\\s+|npm\\s+install\\s+-g\\b|DROP\\s+DATABASE)\"; sys.exit(2) if re.search(bad, cmd, re.I) else sys.exit(0)'",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c 'import json,subprocess,sys; p=json.load(sys.stdin).get(\"tool_input\",{}).get(\"file_path\",\"\"); subprocess.run([\"ruff\",\"format\",p], check=False) if p.endswith(\".py\") else None'"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if [ -x ./scripts/ci-gate.sh ]; then ./scripts/ci-gate.sh || exit 2; fi'"
          }
        ]
      }
    ]
  }
}
```

### Critical Exit-Code Semantics for Claude Code Hooks
- **Exit `0`**: Allow tool execution / allow agent turn to finish.
- **Exit `2`**: **Block execution deterministically**. On `PreToolUse`, blocks the tool call and feeds `stderr` back to the model for self-correction. On `Stop`, rejects turn completion and forces the agent back into the verification loop.
- **Never rely on Exit `1` for security blocking** — non-2 errors are treated as non-blocking hook failures. Inspect active bindings inside any session with `/hooks`.

---

## 5. Git Pre-Commit & Post-Edit Verification Hooks

### 5.1 Pre-Commit Hook (`.husky/pre-commit` or `.git/hooks/pre-commit`)
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> [DevSkill Pre-Commit] Running staged quality gate..."

# 1. Run executable DevSkill CI gate scan on staged files
./scripts/ci-gate.sh --staged

# 2. Run secret scanner if installed
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks protect --staged --verbose
fi

echo "Pre-commit checks passed."
```

### 5.2 Definition of Done Ship Gate Check
Before generating the final delivery report, execute the full project verification suite (`make verify` / `npm run verify` / `python3 scripts/validate-skill.py`) and self-assess against [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) (**Every category ≥ 9.0/10 relative, Total ≥ 95/100**).

---

## 6. Standard Project Commands

- **Install Dependencies (Frozen)**: `npm ci --ignore-scripts` / `uv sync --frozen` / `cargo fetch --locked` (R-118, R-119)
- **Lint & Format**: `npm run lint` / `ruff check . && ruff format --check .`
- **Typecheck**: `npx tsc --noEmit` (or `tsgo --noEmit` on TS 7+) / `mypy --strict .`
- **Run Unit Tests**: `npm test` / `pytest -v tests/unit/` / `go test -race ./...`
- **Run DevSkill Integrity Audit**: `python3 scripts/validate-skill.py && python3 -m unittest discover -s scripts -p "test_*.py" -v`
- **One-Step Quality Gate**: `./scripts/ci-gate.sh`
