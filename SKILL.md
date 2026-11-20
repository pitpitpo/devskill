---
name: devskill
description: >-
  Industry-grade software engineering skill and operational governance library
  for autonomous AI coding agents and senior engineers. Trigger whenever
  designing architectures, implementing or refactoring backend/frontend/mobile/ERP/kernel
  code, fixing bugs with Red-Green TDD, conducting security or blast-radius
  audits, writing database migrations, building MCP/A2A agentic systems,
  optimizing performance, configuring CI/CD pipelines, or shipping pull requests.
license: MIT
compatibility: >-
  Portable across Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI,
  and agentskills.io-compliant harnesses. Optional helper scripts require Python 3.10+,
  Git 2.40+, Bash, and GitHub CLI (gh) for PR watching.
metadata:
  version: "2.0.0"
  category: "software-engineering"
  author: "DevSkill Core Architecture Team"
  updated: "2026-11-19"
  standards: "OWASP-2025,OWASP-ASI-2026,NIST-800-63B-4,NIST-PQC-FIPS-203-205,WCAG-2.2-AA,RFC-9457,MCP-2026,A2A"
---

# DevSkill: Autonomous Industry-Grade Engineering Library

`devskill` is the foundational knowledge and operational protocol repository for AI agents and engineering teams shipping enterprise-grade software. It uses **progressive disclosure** (`AGENTS.md` → `ROUTING.md` → `index.json` → targeted domain guides) so agents ingest only the exact rules, threat models, and blueprints needed for the active task without bloating context windows.

---

## 🎯 Progressive Disclosure Execution Flow

When tasked with designing, architecting, implementing, auditing, or refactoring code:

```
[Agent Activated]
       │
       ▼
1. Classify Task Archetype via ROUTING.md (23 archetypes) or query index.json
       │
       ▼
2. Load & Enforce Core Constraints:
   ├── RULES.md       (Non-negotiable engineering law: R-001 through R-235)
   ├── security.md    (OWASP Top 10:2025, OWASP Agentic ASI01–ASI10, NIST 800-63B-4, PQC)
   └── AGENTS.md / agents.md (Execution safety, Always/Ask/Never boundaries, 3-strike triage)
       │
       ▼
3. Consult Decision Matrix (decisions.md) & Arena Evaluator (agents/arena-evaluator.md)
   ├── Evaluate trade-offs before choosing frameworks, databases, or agent protocols
   └── Justify choices on latency, consistency, complexity, and operational cost
       │
       ▼
4. Load ONLY Target Domain Guides (3–5 files max):
   ├── languages/<language>.md
   ├── frameworks/<category>/<framework>.md
   ├── sections/<domain>/<topic>.md
   ├── agents/<protocol>.md
   └── pipelines/<ci-provider>.md
       │
       ▼
5. Scaffold & Implement (scaffolding/)
   ├── Apply strict static typing, boundary schemas, container & hook hygiene
   └── Write complete, deterministic, test-covered code with surgical diffs
       │
       ▼
6. Verify & Audit (Exit Code 0 Required):
   ├── ./scripts/ci-gate.sh & project test/typecheck/lint suite
   ├── python3 scripts/validate-skill.py (when modifying skill artifacts)
   └── Score against DEFINITION_OF_DONE.md (>= 95/100 total, >= 9.0/10 per category)
```

---

## 📂 Core Navigation Map

| Section | Location | Description |
|---|---|---|
| **Universal Agent Entrypoint** | [`AGENTS.md`](AGENTS.md) | Concise cross-tool `AGENTS.md` open standard (AAIF) |
| **Claude Code Harness Config** | [`CLAUDE.md`](CLAUDE.md) | Claude Code Plan Mode, permissions, and `settings.json` Exit-Code-2 hooks |
| **Deterministic Routing** | [`ROUTING.md`](ROUTING.md) | 23-archetype routing matrix prescribing exact reading lists and test commands |
| **Engineering Rules** | [`RULES.md`](RULES.md) | Universal laws of architecture, security, ERP, kernel, and agents (R-001–R-235) |
| **Security Standards** | [`security.md`](security.md) | OWASP Top 10:2025, Agentic ASI01–ASI10, NIST SP 800-63B-4, NIST PQC |
| **Agent Protocols** | [`agents.md`](agents.md) & [`agents/`](agents/) | Multi-agent DAGs, MCP/A2A, dynamic model discovery, Ralph loop, Sol loop, TLA+, PR delivery |
| **Decision Trees** | [`decisions.md`](decisions.md) | Trade-off matrices for databases, architecture, APIs, state, queues, and MCP/A2A |
| **Fast Semantic Index** | [`index.json`](index.json) | Machine-readable catalog with tags, archetypes, line counts, and rule summaries |
| **Repository Specification** | [`specs.md`](specs.md) | System taxonomy, document anatomy, and governance rules |
| **Definition of Done** | [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) | 100-point Dual-Threshold Ship Gate rubric |
| **Frameworks** | [`frameworks/`](frameworks/) | Next.js 16, React 19.2, FastAPI, NestJS, Django, Spring Boot, Go/Rust, .NET, Odoo, ERPNext, AOSP, Flutter |
| **Sections** | [`sections/`](sections/) | Backend, Frontend, Database (PG 18), DevOps, QA, AI/ML, ERP/Ledger, Systems/Kernel |
| **Languages** | [`languages/`](languages/) | TypeScript 6/7 (`tsgo`), Python 3.14, Go 1.25+, Rust 2024, Java 21+, C23/C++23, SQL |
| **Workflows** | [`workflows/`](workflows/) | 8-phase lifecycle, PR babysitting, modernization/takeover, Git, SemVer, Incidents, Anti-Slop |
| **Pipelines** | [`pipelines/`](pipelines/) | GitHub Actions, GitLab CI, SAST/DAST/SCA, and progressive deployments |
| **Scaffolding** | [`scaffolding/`](scaffolding/) | Production configs (`.claude-settings.json`, `tsconfig`, `ruff`, Docker Compose, CI) & templates |
| **Executable Scripts** | [`scripts/`](scripts/) | `ci-gate.sh`, `validate-skill.py`, `pr-wait.py`, and automated unit tests |

---

## ⚡ Prime Directives for Agents

1. **Validate every boundary**: Parse all external inputs through strict runtime schemas (Zod, Valibot, Pydantic v2) and reject unknown fields (R-060).
2. **Never commit secrets**: Zero credentials, API keys, or private tokens in code, commits, or logs (R-064).
3. **Prove every claim with execution**: Run real commands and observe Exit Code `0`; write a failing test first on bug fixes (R-004, R-005, R-181, R-202).
4. **Enforce strict typing & zero placeholders**: Zero `any`/`@ts-ignore`/`# type: ignore`, zero `TODO`/`FIXME` stubs, zero mock data in production paths (R-001, R-002, R-033, R-034).
5. **Fail closed & enforce least agency**: Never swallow errors, never return stack traces to clients, enforce OWASP Top 10:2025 + Agentic ASI01–ASI10 least-privilege boundaries, and log structured JSON with W3C `traceparent` correlation (R-046, R-057, R-142, R-228, R-232).
