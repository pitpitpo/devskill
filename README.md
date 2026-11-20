# 🚀 DevSkill v2.0: Autonomous Industry-Grade Engineering Library

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Quality Gate: Enterprise](https://img.shields.io/badge/Quality%20Gate-Enterprise%20v2.0-blue.svg)](DEFINITION_OF_DONE.md)
[![Security: OWASP 2025 + ASI](https://img.shields.io/badge/Security-OWASP%202025%20%2B%20ASI-green.svg)](security.md)
[![Agent Skills: Open Standard](https://img.shields.io/badge/Standard-agentskills.io%20%2B%20AGENTS.md-purple.svg)](SKILL.md)

`devskill` is an open-standard (`agentskills.io` + Linux Foundation AAIF `AGENTS.md`) engineering library and operational governance system built for autonomous AI coding agents and senior software engineering teams. It eliminates hallucinated defaults, enforces deterministic verification loops, embeds **OWASP Top 10:2025**, **OWASP Agentic Applications (ASI01–ASI10)**, **NIST SP 800-63B-4**, **NIST Post-Quantum Cryptography (FIPS 203–205)**, and **MCP 2026 / A2A** protocols, and provides executable validation and PR-watching scripts.

---

## 📚 What DevSkill v2.0 Provides

- **Progressive-Disclosure Standards Entrypoints**: [`SKILL.md`](SKILL.md) (`agentskills.io` v2.0 frontmatter), [`AGENTS.md`](AGENTS.md) (universal cross-tool standard), and [`CLAUDE.md`](CLAUDE.md) (declarative `.claude/settings.json` Exit-Code-2 harness hooks).
- **23-Archetype Deterministic Router**: [`ROUTING.md`](ROUTING.md) maps every engineering task to an exact 3–5 file reading list, invariant rules, prohibited actions, and terminal verification commands.
- **235 Universal Engineering Laws**: [`RULES.md`](RULES.md) (`R-001` through `R-235`) spanning code hygiene, typing, testing, database migrations, security, ERP/accounting ledgers, Linux kernel/AOSP, multi-agent orchestration, MCP/A2A, and post-quantum readiness.
- **2026 Production Security Baseline**: [`security.md`](security.md) covering OWASP Top 10:2025, OWASP Agentic ASI01–ASI10 & AST10, NIST SP 800-63B-4 (July 2025), and NIST FIPS 203/204/205 PQC.
- **Executable Guardrails & Self-Validation**:
  - [`scripts/ci-gate.sh`](scripts/ci-gate.sh) — Pre-commit (`--staged`) and CI quality gate scanner.
  - [`scripts/validate-skill.py`](scripts/validate-skill.py) — Deterministic repository auditor (links, rule citations, frontmatter, config syntax, and `index.json` parity).
  - [`scripts/pr-wait.py`](scripts/pr-wait.py) — Event-driven GitHub PR & review-bot watcher with REST rate-limit fallback (R-206).
- **Comprehensive Modular Library**:
  - [`agents/`](agents/) — Orchestrator DAGs, MCP/A2A interoperability, dynamic model discovery, tri-provider councils, Sol loop, Ralph loop, TLA+ formal verification, blast-radius proof, hillclimbing, TDD reproduction, Poteto discipline, Arena evaluator, full-send delivery.
  - [`frameworks/`](frameworks/) — Next.js 16, React 19.2, Vue/Nuxt, SvelteKit, Tailwind v4, FastAPI, NestJS, Django, Express, Spring Boot, Go Gin/Rust Axum, .NET, Odoo, ERPNext, React Native Expo, Flutter, Android AOSP.
  - [`sections/`](sections/) — Backend, Frontend, Database (PostgreSQL 18), DevOps/SRE, Testing/QA, AI/ML & LLM Integration, Enterprise ERP/Ledger, Systems & Kernel Drivers.
  - [`languages/`](languages/) — TypeScript 6/7 (`tsgo`), Python 3.14, Go 1.25+, Rust 2024, Java 21+, C23/C++23, SQL.
  - [`workflows/`](workflows/), [`pipelines/`](pipelines/), and [`scaffolding/`](scaffolding/).

---

## ⚡ Quick Verification Commands

```bash
# 1. Audit skill repository integrity (links, rules, frontmatter, configs, index.json)
python3 scripts/validate-skill.py

# 2. Run automated unit tests for bundled scripts
python3 -m unittest discover -s scripts -p "test_*.py" -v

# 3. Run the DevSkill CI quality gate on your project (or staged changes)
./scripts/ci-gate.sh --staged
```

---

## 🛠️ Usage by AI Agents

1. Start at [`AGENTS.md`](AGENTS.md) or [`SKILL.md`](SKILL.md) (progressive disclosure).
2. Classify the task in [`ROUTING.md`](ROUTING.md) or look up tags/archetypes in [`index.json`](index.json).
3. Enforce [`RULES.md`](RULES.md) and [`security.md`](security.md) unconditionally.
4. Load only the 3–5 prescribed domain guides for your archetype.
5. Verify with real CLI execution (Exit Code `0`) and score against [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) (≥ 95/100 total, ≥ 9.0/10 per category).
