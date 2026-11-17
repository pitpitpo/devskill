# 🚀 DevSkill: Autonomous Industry-Grade Engineering Library

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Quality Gate: Enterprise](https://img.shields.io/badge/Quality%20Gate-Enterprise-blue.svg)](#)
[![Security: OWASP Top 10](https://img.shields.io/badge/Security-OWASP%20Compliant-green.svg)](file:///home/agy/.t3/userdata/attachments/devskill/security.md)
[![Agents: Guardrails Active](https://img.shields.io/badge/Agents-Deterministic-purple.svg)](file:///home/agy/.t3/userdata/attachments/devskill/agents.md)

`devskill` is an open standard and operational knowledge repository engineered for autonomous AI agents and senior development teams shipping production-grade software. It bridges the gap between raw code completion and resilient, high-performance, enterprise-ready systems.

---

## 📚 What DevSkill Provides

- **Deterministic Rules & Quality Gates**: [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) enforces non-negotiable coding, architecture, typing, and testing laws.
- **Production Security Standard**: [`security.md`](file:///home/agy/.t3/userdata/attachments/devskill/security.md) delivers complete OWASP Top 10 mitigation, token handling, secrets management, and defense-in-depth guidelines.
- **Autonomous Agent Safety**: [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md) defines agent personas, sandboxing rules, self-correction loops, and context hygiene.
- **Architectural Decision Matrix**: [`decisions.md`](file:///home/agy/.t3/userdata/attachments/devskill/decisions.md) guides choices across databases, frameworks, APIs, and state managers.
- **Comprehensive Technical Guides**: Deep production manuals organized into modular folders:
  - [`frameworks/`](file:///home/agy/.t3/userdata/attachments/devskill/frameworks/) (Next.js, React, FastAPI, NestJS, Django, Spring Boot, Go Gin, Odoo, ERPNext, Android AOSP, etc.)
  - [`sections/`](file:///home/agy/.t3/userdata/attachments/devskill/sections/) (Backend, Frontend, Database, DevOps, Testing & QA, Enterprise ERP/Ledger, Systems & Kernel Drivers)
  - [`languages/`](file:///home/agy/.t3/userdata/attachments/devskill/languages/) (TypeScript, Python, Go, Rust, Java, C/C++, SQL)
  - [`workflows/`](file:///home/agy/.t3/userdata/attachments/devskill/workflows/) (Git branching, PR reviews, SemVer, Incident response)
  - [`pipelines/`](file:///home/agy/.t3/userdata/attachments/devskill/pipelines/) (CI/CD GitHub Actions, GitLab CI, SAST/DAST)
  - [`scaffolding/`](file:///home/agy/.t3/userdata/attachments/devskill/scaffolding/) (Production starter configs and architecture templates)

---

## ⚡ Quick Navigation

```
devskill/
├── SKILL.md                          # Top-level AI Agent Skill Specification
├── specs.md                          # System Specification & Architecture Schema
├── RULES.md                          # Non-Negotiable Universal Engineering Rules
├── ROUTING.md                        # Deterministic Task-Archetype Decision Matrix
├── security.md                       # Production Security Standards & OWASP Checklist
├── agents.md                         # Autonomous Agent Protocols & Guardrails
├── decisions.md                      # Technology Selection Decision Trees
├── index.json                        # Machine-Readable Fast Topic Index
│
├── agents/                           # Autonomous Agent Sub-Skills & Execution Protocols
│   ├── orchestrator.md               # Multi-Agent DAGs, Fencing Leases & Reconcilers
│   ├── poteto-discipline.md          # Minimal Diff, Surgical Engineering & Evidence
│   ├── tdd-reproduction.md           # Reproduction-First TDD & Defect Isolation
│   └── arena-evaluator.md            # Multi-Solution Arena Scoring & Trade-offs
│
├── frameworks/
│   ├── frontend/                     # Next.js, React, Vue/Nuxt, SvelteKit, Tailwind
│   ├── backend/                      # FastAPI, NestJS, Django, Express, Spring, Go/Rust, .NET
│   ├── erp/                          # Odoo 17/18, Frappe & ERPNext v15/v16
│   └── mobile/                       # React Native Expo, Flutter, Android AOSP
│
├── sections/
│   ├── backend/                      # API Design, Microservices vs Monolith, Caching, Queues
│   ├── frontend/                     # State Management, Accessibility (A11y), Performance
│   ├── database/                     # PostgreSQL Mastery, Migrations, NoSQL, Pooling
│   ├── erp-enterprise/               # Core Accounting Ledger, Inventory & Supply Chain
│   ├── systems-kernel/               # Linux Kernel Drivers, Device Tree & eBPF
│   ├── devops-infrastructure/        # Docker Containers, Kubernetes, Terraform, Observability
│   └── testing-qa/                   # Test Pyramid, Contract Testing, E2E Playwright
│
├── languages/                        # TypeScript, Python, Go, Rust, Java, C/C++, SQL
├── workflows/                        # Git Branching, Code Reviews, Release Versioning, Incidents
├── pipelines/                        # GitHub Actions, GitLab CI, Security Scanning, Deployments
└── scaffolding/                      # Starter Configs (.editorconfig, tsconfig, Docker, etc.)
```

---

## 🛠️ Usage by AI Agents

AI agents loading `devskill` as a skill should:
1. First read [`SKILL.md`](file:///home/agy/.t3/userdata/attachments/devskill/SKILL.md) and [`index.json`](file:///home/agy/.t3/userdata/attachments/devskill/index.json).
2. Adhere unconditionally to [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) and [`security.md`](file:///home/agy/.t3/userdata/attachments/devskill/security.md).
3. Select appropriate technical stacks via [`decisions.md`](file:///home/agy/.t3/userdata/attachments/devskill/decisions.md).
4. Fetch specific domain guides on-demand without loading unnecessary context.
