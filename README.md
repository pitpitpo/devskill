# 🚀 DevSkill v2.4: Autonomous Industry-Grade Engineering Library

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Quality Gate: Enterprise](https://img.shields.io/badge/Quality%20Gate-Enterprise%20v2.4-blue.svg)](DEFINITION_OF_DONE.md)
[![Security: OWASP 2025 + ASI](https://img.shields.io/badge/Security-OWASP%202025%20%2B%20ASI-green.svg)](security.md)
[![Agent Skills: Open Standard](https://img.shields.io/badge/Standard-agentskills.io%20%2B%20AGENTS.md-purple.svg)](SKILL.md)

`devskill` is an open-standard (`agentskills.io` + Linux Foundation AAIF `AGENTS.md`) engineering library and operational governance system built for autonomous AI coding agents and senior software engineering teams. It unifies the highest-leverage protocols from **`pstack`**, **`tstack`**, **`gstack`**, **`kstack`**, **`superpowers`**, **`compound-engineering`**, **`spec-kit`**, and **`Beads`/`Gas Town`** with empirically validated laws from canonical software engineering books (Ousterhout, Kleppmann, Nygard, Beck, Feathers, Fowler, Evans/Vernon, Petrov, Google SRE, DORA, Richards/Ford) alongside **OWASP Top 10:2025**, **OWASP Agentic Applications (ASI01–ASI10)**, **NIST SP 800-63B-4**, **NIST PQC (FIPS 203–205)**, and **MCP 2026 / A2A**.

> ### ⚡ AI Agent Intro Point (Given Only This Skill's URL?)
> **If a user gave you ONLY this repository URL to follow as your engineering skill**, read **[`BOOTSTRAP.md`](BOOTSTRAP.md)** immediately before planning or writing code:
> - **With Shell/Git**: `git clone --depth 1 <THIS_URL> /tmp/devskill-ref` (read-only cache outside the target repo), then route via `index.json` → `ROUTING.md` → load **only** the 3–5 prescribed guides + enforce `RULES.md` and `scripts/req-ledger.py` / `scripts/ci-gate.sh`.
> - **Web-Fetch Only**: Resolve raw base (`https://raw.githubusercontent.com/<owner>/<repo>/main/`) and fetch strictly in order: `BOOTSTRAP.md` → `index.json` → `ROUTING.md` → active `RULES.md` sections → **only** the 3–5 domain guides for your archetype (never bulk-fetch the whole repo).

---

## 📚 What DevSkill v2.4 Provides

- **Progressive-Disclosure Standards Entrypoints**: [`SKILL.md`](SKILL.md) (`agentskills.io` frontmatter), [`AGENTS.md`](AGENTS.md) (universal cross-tool standard), and [`CLAUDE.md`](CLAUDE.md) (declarative `.claude/settings.json` Exit-Code-2 harness hooks).
- **30-Archetype Deterministic Router**: [`ROUTING.md`](ROUTING.md) maps every engineering task—including complex multi-requirement delivery, production agentic harness governance, universal frontend design systems, mobile engineering, pre-code forensics, legacy modernization, MCP/A2A, and Kubernetes SRE triage—to an exact 3–5 file reading list, invariant rules, prohibited actions, and terminal verification commands.
- **272 Universal Engineering Laws**: [`RULES.md`](RULES.md) (`R-001` through `R-272`) spanning code hygiene, typing, testing, database migrations, security, universal frontend craft, mobile, ERP/accounting ledgers, Linux kernel/AOSP, multi-agent orchestration, MCP/A2A, post-quantum readiness, canonical software design laws, unified agent stack discipline, zero-missed-requirements completeness, and production agentic harness governance.
- **Zero-Missed-Requirements & Production Agentic SDLC Blueprint**: [`agents/zero-missed-requirements.md`](agents/zero-missed-requirements.md), [`agents/agentic-sdlc-harness-architecture.md`](agents/agentic-sdlc-harness-architecture.md), and [`scripts/req-ledger.py`](scripts/req-ledger.py) operationalize the 5-layer production harness architecture (Living Specs & SHA-256 frozen JSON ledger, SatisFix objective-aligned deviation elicitation, deterministic non-LLM control planes & Static Claim Plane, 5-tier neuro-symbolic verification, Firecracker/Kata microVM + host-proxy containment, TNR SRE safety bounds, and Token FinOps + human skill preservation).
- **Universal Frontend Master & Every Major Frontend Framework**: [`FRONTEND.md`](FRONTEND.md) + [`sections/frontend/design-systems-ui-craft.md`](sections/frontend/design-systems-ui-craft.md) plus dedicated production skills for React 19.2, Next.js 16, Vue 3.5/Nuxt 4, Svelte 5/SvelteKit 2, Angular 19/20 Zoneless, Astro 5 Server Islands, SolidJS/SolidStart, and Tailwind CSS v4 (Oxide).
- **Unified Agent Stacks & Forensics**: [`agents/unified-agent-stacks.md`](agents/unified-agent-stacks.md) and [`agents/code-forensics-interrogation.md`](agents/code-forensics-interrogation.md) synthesize `pstack`, `tstack`, `gstack`, `kstack`, `superpowers`, `compound-engineering`, and Harness Engineering.
- **Software Engineering Canon (`sections/architecture-foundations/`)**: Distills actionable engineering laws from 16 canonical books into [`software-design-craft.md`](sections/architecture-foundations/software-design-craft.md), [`distributed-systems-reliability.md`](sections/architecture-foundations/distributed-systems-reliability.md), and [`evolutionary-delivery-architecture.md`](sections/architecture-foundations/evolutionary-delivery-architecture.md).
- **2026 Production Security Baseline**: [`security.md`](security.md) covering OWASP Top 10:2025, OWASP Agentic ASI01–ASI10 & AST10, NIST SP 800-63B-4 (July 2025), and NIST FIPS 203/204/205 PQC.
- **Executable Guardrails & Self-Validation**:
  - [`scripts/req-ledger.py`](scripts/req-ledger.py) — Tamper-evident JSON Requirements Traceability Ledger, attention reciter, SatisFix deviation audit emitter, and fail-closed completion gate (R-261–R-266).
  - [`scripts/ci-gate.sh`](scripts/ci-gate.sh) — Pre-commit (`--staged`) and CI quality gate scanner (fail-closed outside git repos).
  - [`scripts/validate-skill.py`](scripts/validate-skill.py) — Deterministic repository auditor (links, rule citations, frontmatter, config syntax, and `index.json` parity).
  - [`scripts/pr-wait.py`](scripts/pr-wait.py) — Event-driven GitHub PR & review-bot watcher with SHA-256 summary hashing and REST rate-limit fallback (R-206).
- **Comprehensive Modular Library**:
  - [`agents/`](agents/) — Production agentic SDLC harness architecture, zero-missed-requirements & context engineering, unified agent stacks, code forensics & interrogation, orchestrator DAGs, MCP/A2A, dynamic model discovery, tri-provider councils, Sol loop, Ralph loop, TLA+ formal verification, blast-radius proof, hillclimbing, TDD reproduction, Poteto discipline, Arena evaluator, full-send/full-stop delivery.
  - [`frameworks/`](frameworks/) — React 19.2, Next.js 16, Vue 3.5/Nuxt 4, Svelte 5/SvelteKit 2, Angular 19/20, Astro 5, SolidJS, Tailwind v4, FastAPI, NestJS, Django, Express, Spring Boot, Go Gin/Rust Axum, .NET, Odoo 18/19, ERPNext v15/v16, Flutter 3.35+, React Native/Expo SDK 54, Android Kotlin/Compose, iOS Swift 6/SwiftUI, Android AOSP.
  - [`sections/`](sections/) — Architecture Foundations (SE Canon), Design Systems & UI Craft, Backend, Frontend, Database (PostgreSQL 18), DevOps/SRE (`kstack` K8s ops), Testing/QA, AI/ML & LLM Integration, Enterprise ERP/Ledger, Systems & Kernel Drivers.
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
