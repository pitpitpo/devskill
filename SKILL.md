---
name: devskill
description: Comprehensive industry-grade software engineering skill for autonomous AI agents and professional developers. Contains non-negotiable engineering rules, production security blueprints, multi-agent execution guardrails, framework and language mastery guides, architectural decision trees, CI/CD pipelines, and project scaffolding.
metadata:
  version: 1.2.0
  category: software-engineering
  author: DevSkill Core Architecture Team
  updated: 2026-11-17
---

# DevSkill: Autonomous Industry-Grade Engineering Library

`devskill` is the foundational knowledge and operational protocol repository for AI agents and engineering teams shipping enterprise-grade software. It eliminates hallucinations, standardizes architectural decisions, enforces zero-trust security, and provides battle-tested blueprints across every layer of the modern tech stack.

---

## 🎯 How an AI Agent Must Use DevSkill

When tasked with designing, architecting, implementing, auditing, or refactoring code:

```
[Agent Activated]
       │
       ▼
1. Query index.json or specs.md to identify domain & tech stack
       │
       ▼
2. Load & Enforce Core Constraints:
   ├── RULES.md       (Non-negotiable engineering rules)
   ├── security.md    (Production security & threat mitigation)
   └── agents.md      (Execution safety & agent boundaries)
       │
       ▼
3. Consult Decision Matrix (decisions.md)
   ├── Evaluate trade-offs before choosing frameworks/databases
   └── Justify choices based on latency, complexity, scalability
       │
       ▼
4. Load Target Domain Guides:
   ├── languages/<language>.md
   ├── frameworks/<category>/<framework>.md
   ├── sections/<domain>/<topic>.md
   └── pipelines/<ci-provider>.md
       │
       ▼
5. Scaffold & Implement (scaffolding/)
   ├── Apply strict type checks, lint configs, container hygiene
   └── Write deterministic, self-documenting, test-covered code
       │
       ▼
6. Verify & Audit against Workflows:
   ├── workflows/code-review-standards.md
   └── workflows/git-branching-pr.md
```

---

## 📂 Core Navigation Map

| Section | Location | Description |
|---|---|---|
| **Repository Specification** | [`specs.md`](file:///home/agy/.t3/userdata/attachments/devskill/specs.md) | Complete system architecture, taxonomy, schemas, and roadmap |
| **Engineering Rules** | [`RULES.md`](file:///home/agy/.t3/userdata/attachments/devskill/RULES.md) | Universal laws of architecture, code style, testing, and operations |
| **Security Standards** | [`security.md`](file:///home/agy/.t3/userdata/attachments/devskill/security.md) | OWASP mitigation, cryptographic specs, AuthN/AuthZ, supply chain |
| **Deterministic Routing** | [`ROUTING.md`](file:///home/agy/.t3/userdata/attachments/devskill/ROUTING.md) | Task-archetype decision matrix prescribing exact reading lists and test commands |
| **Agent Protocols** | [`agents.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents.md) & [`agents/`](file:///home/agy/.t3/userdata/attachments/devskill/agents/) | Multi-agent DAGs, dynamic model discovery, strength-based orchestration, Ralph loop, Sol review, TLA+ statecharts, PR delivery |
| **Decision Trees** | [`decisions.md`](file:///home/agy/.t3/userdata/attachments/devskill/decisions.md) | Trade-off matrices for databases, architecture, state, and APIs |
| **Fast Index** | [`index.json`](file:///home/agy/.t3/userdata/attachments/devskill/index.json) | Fast-lookup machine-readable index of all topics and tags |
| **Frameworks** | [`frameworks/`](file:///home/agy/.t3/userdata/attachments/devskill/frameworks/) | Deep-dive guides for React, Next.js, FastAPI, NestJS, Spring, Odoo, ERPNext, AOSP, etc. |
| **Sections** | [`sections/`](file:///home/agy/.t3/userdata/attachments/devskill/sections/) | Backend, Frontend, Database, DevOps, QA, Observability, ERP/Accounting, and Systems/Kernel |
| **Languages** | [`languages/`](file:///home/agy/.t3/userdata/attachments/devskill/languages/) | TypeScript, Python, Go, Rust, Java, C/C++, and SQL mastery |
| **Workflows** | [`workflows/`](file:///home/agy/.t3/userdata/attachments/devskill/workflows/) | PR babysitting, modernization, takeover, Git branching, SemVer, Incidents, Feature Flags, Anti-Slop Hygiene |
| **Pipelines** | [`pipelines/`](file:///home/agy/.t3/userdata/attachments/devskill/pipelines/) | CI/CD GitHub Actions, GitLab CI, SAST/DAST, and deployments |
| **Scaffolding** | [`scaffolding/`](file:///home/agy/.t3/userdata/attachments/devskill/scaffolding/) | Production configs, docker-compose, and starter templates |

---

## ⚡ Prime Directives for Agents

1. **Never generate unvalidated or unchecked code**: Every input must be validated via schema parsers (Zod, Pydantic, Marshmallow, etc.).
2. **Never commit secrets**: Zero credentials, API keys, or private tokens in code, commits, or logs.
3. **Always write tests alongside logic**: Minimum 80% branch coverage with unit, integration, and contract tests.
4. **Enforce strict typing**: No `any` in TypeScript, no untyped Python functions, full compiler strictness across all languages.
5. **Fail closed and log structured**: All errors must be logged with contextual correlation IDs, never exposing stack traces to clients.
