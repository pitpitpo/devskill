# 📐 DevSkill Technical Specification (`specs.md`)

> **Document Version**: 2.0.0 (Updated: 2026-11-19)  
> **Status**: Approved & Active  
> **Classification**: Core System Architecture Specification  
> **Target Audience**: AI Agents, System Architects, Principal Engineers, Platform Teams  

---

## 1. Executive Summary & Vision

Modern software engineering demands high-velocity delivery without sacrificing security, performance, or operational stability. AI agents possess immense coding capacity but frequently fail in production settings due to:
1. **Context fragmentation**: Inconsistent understanding of enterprise standards.
2. **Hallucinated or insecure defaults**: Permissive CORS, hardcoded credentials, plain-text secrets, missing rate limits.
3. **Suboptimal architectural choices**: Premature microservices, inappropriate database engines, unindexed relational queries, lack of idempotency.
4. **Flaky testing and unstandardized workflows**: Low test coverage, missing contract tests, untracked releases.

**DevSkill** is an industrial-grade engineering repository and cognitive skill library that bridges the gap between raw AI code generation and enterprise production requirements. It provides a deterministic, version-controlled knowledge base, decision engine, and operational playbook.

---

## 2. Core Pillars & Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               DEVSKILL CORE                  │
                    │   Cognitive & Operational Skill Framework    │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌───────────────────┬─────────────┴─────────────┬───────────────────┐
         ▼                   ▼                           ▼                   ▼
  ┌──────────────┐   ┌──────────────┐             ┌──────────────┐   ┌──────────────┐
  │   GOVERNANCE │   │  DECISION    │             │  STACK &     │   │  LIFECYCLE   │
  │   & SECURITY │   │  FRAMEWORK   │             │  FRAMEWORKS  │   │  & DEVOPS    │
  ├──────────────┤   ├──────────────┤             ├──────────────┤   ├──────────────┤
  │ RULES.md     │   │ decisions.md │             │ frameworks/  │   │ workflows/   │
  │ security.md  │   │              │             │ sections/    │   │ pipelines/   │
  │ agents.md    │   │ Trade-off    │             │ languages/   │   │ scaffolding/ │
  │              │   │ Matrices     │             │ Deep Guides  │   │ Automation   │
  └──────────────┘   └──────────────┘             └──────────────┘   └──────────────┘
```

The system is structured across four primary functional tiers:
1. **Tier 1: Governance & Security (The Guardrails)**:
   Absolute rules that cannot be violated under any circumstances. Covers secure coding, zero-trust design, agent behavior protocols, and non-negotiable code hygiene.
2. **Tier 2: Decision Engineering (The Polishing Engine)**:
   Deterministic decision trees and trade-off matrices preventing arbitrary technology selection. Guides choices across architecture, databases, state management, caching, and communication protocols.
3. **Tier 3: Domain & Language Mastery (The Technical Library)**:
   Exhaustive, framework-specific and language-specific production manuals. Each guide contains architectural blueprints, code conventions, anti-patterns, performance tuning, and idiomatic implementations.
4. **Tier 4: Lifecycle Automation (The Execution Engine)**:
   Real-world production CI/CD workflows, Git branching strategies, code review checklists, incident response runbooks, and reusable scaffolding configurations.

---

## 3. Directory Taxonomy & File Inventory

The repository adheres to a strict hierarchical directory structure:

```
devskill/
│
├── SKILL.md                          # Top-level agentskills.io Skill Specification (v2.0.0)
├── AGENTS.md                         # Universal Open-Standard AAIF Entrypoint for Coding Agents
├── CLAUDE.md                         # Claude Code Harness & Declarative Hook Configuration
├── README.md                         # Main Documentation, Quick Start & Verification Commands
├── specs.md                          # Complete System Specification (This Document)
├── RULES.md                          # Non-Negotiable Universal Engineering Rules (R-001–R-235)
├── ROUTING.md                        # 23-Archetype Deterministic Task Router
├── security.md                       # OWASP 2025, Agentic ASI01–ASI10, NIST 800-63B-4, NIST PQC
├── agents.md                         # Detailed Autonomous Agent Protocols & Boundaries
├── decisions.md                      # Tech Stack, Architecture & MCP/A2A Decision Matrices
├── DEFINITION_OF_DONE.md             # 100-Point Dual-Threshold Ship Gate Rubric
├── ARCHITECTURE.md                   # System Design & Architecture Principles
├── FRONTEND.md                       # Frontend Engineering Standards & Core Web Vitals
├── DEPLOYMENT.md                     # Production Deployment & Infrastructure Guide
├── OBSERVABILITY.md                  # Monitoring, Logging, Tracing & Alerting
├── MISTAKES.md                       # Living AI Failure Catalog & Automated Guards
├── index.json                        # Machine-Readable Catalog with Tags, Archetypes & Line Counts
│
├── agents/                           # Autonomous Agent Sub-Skills & Execution Protocols
│   ├── orchestrator.md               # Multi-Agent DAGs, Fencing Leases, Sagas & Reconciler Loops
│   ├── mcp-a2a-protocols.md          # MCP 2026 Stateless Streamable HTTP, OAuth 2.1 RFC 8707 & A2A
│   ├── full-send-delivery.md         # Autonomous End-to-End PR Delivery, Merge Gates & Full-Stop Handoff
│   ├── multi-model-council.md        # Tri-Provider Flagship Council, Review Loops & Scope-Creep Defense
│   ├── blast-radius-verification.md  # Systemic Impact Analysis, Single-Fact Proof & Dark Blast Radius
│   ├── hillclimbing-optimization.md  # Performance Hillclimbing, 7-Question Benchmark Audit & Ledgers
│   ├── poteto-discipline.md          # Minimal Diff, Surgical Engineering & Evidence Standards
│   ├── tdd-reproduction.md           # Reproduction-First TDD, Defect Localization & Isolation
│   ├── arena-evaluator.md            # Multi-Solution Arena Scoring & Architectural Trade-offs
│   ├── ralph-reconciler-loop.md      # The Ralph Loop, Fresh-Context Iteration & Non-Stop Reconciler
│   ├── sol-loop.md                   # Adversarial Single-Model Review Loop & Sol Protocol
│   ├── formal-verification-statecharts.md # Formal Verification, Statecharts & TLA+ Invariant Checking
│   ├── model-capability-orchestration.md  # Dynamic Model Discovery, Capability Profiling & Routing
│   ├── browser-qa-dogfooding.md      # Autonomous Browser Dogfooding, Visual QA & Playwright Synthesis
│   ├── skill-creator-evaluator.md    # Agent Skill Engineering, Progressive Disclosure & Eval Benchmarks
│   └── compound-engineering-knowledge.md # Institutional Memory Compounding, Solution Docs & ADRs
│
├── frameworks/                       # Framework-Specific Deep Mastery Guides
│   ├── README.md                     # Directory index and framework selection guidance
│   ├── frontend/
│   │   ├── nextjs.md                 # Next.js 15/16 App Router, RSC, Cache Components, Turbopack, proxy.ts
│   │   ├── react.md                  # React 19 / 19.2 Core, <Activity />, useEffectEvent, Compiler
│   │   ├── vue-nuxt.md               # Vue 3 Composition API, Nuxt Hybrid SSR, Pinia, Nitro
│   │   ├── sveltekit.md              # Svelte 5 Runes, SvelteKit Form Actions, Loaders, Adapters
│   │   ├── angular.md                # Angular 19/20 Signals-First, Zoneless, httpResource, @defer
│   │   ├── astro.md                  # Astro 5 Zero-JS Content Layer API, Server Islands, ClientRouter
│   │   ├── solidjs.md                # SolidJS / SolidStart Fine-Grained Signals without VDOM
│   │   └── tailwindcss.md            # Tailwind CSS v4, Oxide Engine, CSS-First @theme OKLCH Tokens
│   ├── desktop/
│   │   ├── tauri.md                  # Tauri v2 Desktop, Rust Core, Capabilities, Scoped IPC & System Tray
│   │   └── electron.md               # Electron 33+ Hardened Desktop, contextIsolation, sandbox, contextBridge
│   ├── tui/
│   │   └── terminal-ui.md            # Modern Terminal UIs: Ratatui (Rust), Bubble Tea (Go), Textual (Python)
│   ├── backend/
│   │   ├── fastapi.md                # Python FastAPI, Pydantic v2, AsyncIO, DI, Uvicorn
│   │   ├── nestjs.md                 # Enterprise NestJS, Modular Hexagonal Architecture, Guards, CQRS
│   │   ├── django.md                 # Django 5+ & DRF, ORM Optimization, Celery, Security Hardening
│   │   ├── express.md                # TypeScript Express, Middleware Chains, Error Boundaries, Rate Limits
│   │   ├── spring-boot.md            # Java Spring Boot 3+, Spring Security, JPA, Virtual Threads
│   │   ├── go-gin-axum.md            # Go (Gin/Echo/Chi) & Rust (Axum/Actix-web) High-Throughput Services
│   │   └── dotnet-aspnet.md          # C# .NET 8/9/10 Minimal APIs, EF Core, Middleware Pipeline
│   ├── erp/
│   │   ├── README.md                 # ERP Ecosystem Taxonomy, Selection Matrix & Common Ledger Invariants
│   │   ├── odoo.md                   # Odoo 17/18 Architecture, Models/ORM, Computed Fields, XML Views
│   │   └── erpnext.md                # Frappe Framework v15/v16 & ERPNext, DocType Lifecycle & Submittables
│   └── mobile/
│       ├── react-native-expo.md      # Expo Router, Native Modules, Hermes Engine, Performance Tuning
│       ├── flutter.md                # Dart/Flutter 3+, Riverpod/Bloc, Platform Channels, Impeller
│       ├── ios-swiftui.md            # Native iOS Swift 6 Concurrency, SwiftUI, @Observable, Keychain
│       ├── android-kotlin-compose.md # Native Android Kotlin 2, Jetpack Compose, StateFlow, Room
│       └── android-aosp.md           # Android 14/15/16 AOSP, Project Treble, Stable AIDL HAL & SELinux
│
├── sections/                         # Domain-Specific Cross-Cutting Architectural Layers
│   ├── README.md                     # Directory index and domain taxonomy
│   ├── ai-ml/
│   │   └── llm-integration.md        # Production LLM Gateways, Structured Outputs, Evals, MCP & OTel GenAI
│   ├── backend/
│   │   ├── api-design.md             # REST (RFC 9457), GraphQL, gRPC, tRPC, Idempotency, Webhooks
│   │   ├── microservices-vs-monolith.md # Modular Monolith vs Distributed Microservices, DDD
│   │   ├── caching-strategies.md     # Valkey/Redis, Cache-Aside, Write-Through, Stampede Protection
│   │   └── background-jobs-queues.md # Celery, BullMQ, Kafka, RabbitMQ, SQS, DLQs, Backoffs
│   ├── frontend/
│   │   ├── state-management.md       # Client vs Server State, TanStack Query, Zustand, Jotai, RTK
│   │   ├── accessibility.md          # WCAG 2.2 AA Compliance, ARIA Roles, Focus Trap, Screen Readers
│   │   └── web-performance.md        # Core Web Vitals (LCP, INP, CLS), Bundle Splitting, Asset Perf
│   ├── database/
│   │   ├── postgresql-mastery.md     # PostgreSQL 18 AIO, uuidv7(), EXPLAIN ANALYZE, Indexing, MVCC
│   │   ├── schema-migrations.md      # Zero-Downtime Migrations, Expand/Contract Pattern
│   │   ├── nosql-redis-vector.md     # MongoDB, Valkey/Redis Data Structures, pgvector, DynamoDB
│   │   └── connection-pooling.md     # PgBouncer, Connection Sizing, Timeouts, Deadlock Handling
│   ├── erp-enterprise/
│   │   ├── README.md                 # Enterprise Financial, Supply Chain & Accounting Invariants
│   │   ├── core-accounting-ledger.md # Double-Entry Bookkeeping Invariants, Immutability & Multi-Currency
│   │   └── inventory-supply-chain.md # FIFO Inventory Queues, Landed Cost Distribution & Perpetual Valuation
│   ├── systems-kernel/
│   │   ├── README.md                 # Systems & Kernel Overview, Ring 0 Memory Safety & Atomic Contexts
│   │   └── linux-kernel-driver.md    # Linux 6.6+ Character & Platform Drivers, Device Tree & eBPF
│   ├── devops-infrastructure/
│   │   ├── docker-containers.md      # Multi-Stage Builds, Rootless Execution, Distroless, Digest Pinning
│   │   ├── kubernetes-cloud.md       # Deployments, StatefulSets, HPA, Ingress, Probes, Limits
│   │   ├── terraform-iac.md          # IaC, State Locking, Module Structure, Drift Control
│   │   └── observability-telemetry.md # OpenTelemetry (Traces, Metrics, Logs, GenAI), Prometheus, SLOs
│   └── testing-qa/
│       ├── test-pyramid.md           # Unit (70%), Integration (20%), E2E (10%), Mocks vs Real
│       ├── integration-contract.md   # Testcontainers, Database Fixtures, Consumer-Driven Pact Testing
│       └── e2e-playwright.md         # Playwright Framework, Page Object Model, CI Parallelization
│
├── languages/                        # Deep Idiomatic Language Standards
│   ├── README.md                     # Directory overview and language benchmarks
│   ├── typescript.md                 # TypeScript 6/7 (tsgo), Strict Mode, Nominal Branding, Zod/Valibot
│   ├── python.md                     # Python 3.13/3.14 (PEP 750 t-strings, PEP 649), uv, Ruff, Mypy
│   ├── golang.md                     # Go 1.25+ (testing/synctest, container-aware GOMAXPROCS), Concurrency
│   ├── rust.md                       # Rust 2024 Edition (async closures, let chains), Ownership, Tokio
│   ├── java.md                       # Modern Java 21+ LTS, Records, Pattern Matching, Virtual Threads
│   ├── c-cpp.md                      # Modern ISO C23 & C++23/26, RAII Lifetimes, Memory Safety
│   └── sql.md                        # ANSI SQL, CTEs, Window Functions, Index-Friendly Queries
│
├── workflows/                        # Development & Operational Workflows
│   ├── README.md                     # Directory overview
│   ├── WORKFLOW.md                   # 8-Phase Engineering Lifecycle & Systematic Debugging Protocol
│   ├── pr-lifecycle-babysitting.md   # PR Monitoring, Bot Triage, Modernization & Comment Attribution
│   ├── pr-modernize-takeover.md      # PR Modernization, Stale Branch Triage & Contributor Takeover
│   ├── git-branching-pr.md           # Trunk-Based Development, Conventional Commits, PR Hygiene
│   ├── release-versioning.md         # Semantic Versioning (SemVer 2.0.0), Changelogs, Automation
│   ├── code-review-standards.md      # Senior PR Review Checklist, Blocking vs Non-Blocking Comments
│   ├── incident-response.md          # Severity Tiers (P0–P4), On-Call Runbooks, Blameless Post-Mortems
│   ├── feature-flags.md              # Trunk Development, Dark Launches, Flag Lifecycles, Kill Switches
│   ├── unslop-code-hygiene.md        # Comment Elimination, Anti-Slop Discipline & Structural Encoding
│   └── scripts/pr-wait               # Executable wrapper delegating to scripts/pr-wait.py
│
├── scripts/                          # Automated Verification, CI Gate & Watcher Utilities
│   ├── ci-gate.sh                    # Universal DevSkill CI & Pre-Commit Quality Gate Scanner
│   ├── validate-skill.py             # Deterministic Skill Integrity Auditor & index.json Generator
│   ├── pr-wait.py                    # Standalone Headless GitHub PR & Review Bot Watcher (with REST fallback)
│   └── test_devskill.py              # Automated Unit Test Suite for Bundled Scripts
│
├── pipelines/                        # CI/CD Automation Specifications & Templates
│   ├── README.md                     # Pipeline architectures and security scanning
│   ├── github-actions.md             # Production Workflow: Lint → Typecheck → Test → Build → Scan → Deploy
│   ├── gitlab-ci.md                  # Multi-Stage YAML, Artifacts, Cache Keys, Environment Deployments
│   ├── security-scanning-sast.md     # SAST/DAST/SCA Tooling: Trivy, Gitleaks, Semgrep, Cosign, Syft
│   └── deployment-strategies.md      # Blue/Green, Canary Deployments, Rolling Updates, GitOps ArgoCD
│
└── scaffolding/                      # Battle-Tested Configurations & Templates
    ├── README.md                     # Scaffolding instructions
    ├── configs/
    │   ├── .claude-settings.json     # Production Claude Code PreToolUse/PostToolUse/Stop Hooks
    │   ├── .editorconfig             # Universal code styling
    │   ├── tsconfig.base.json        # Enterprise TypeScript 6/7 base compiler options
    │   ├── ruff.toml                 # Ultra-fast Python 3.13/3.14 linter and formatter config
    │   ├── docker-compose.yml        # Production-like local dev stack (PG 18, Valkey/Redis, Mailpit, MinIO)
    │   └── .github-ci-template.yml   # Hardened Universal GitHub Actions workflow
    └── templates/
        ├── api-microservice.md           # Production API Microservice blueprint
        ├── enterprise-modular-monolith.md # Modular Monolith domain scaffolding
        ├── fullstack-nextjs-fastapi.md   # Next.js 16 + FastAPI architecture blueprint
        └── saas-multi-tenant.md          # Multi-Tenant SaaS RLS & isolation blueprint
```

---

## 4. Markdown Document Schema Standards

Every markdown document in `devskill` adheres to an unambiguous, standardized anatomy to ensure high human readability and deterministic AI parsing:

1. **Frontmatter / Title & Metadata**: Clear purpose, applicability scope, and prerequisites.
2. **Core Philosophy / Golden Rule**: Single-sentence foundational imperative.
3. **Architecture & Design Patterns**: ASCII or Mermaid structural diagrams illustrating data flow.
4. **Concrete Code Examples**: Complete, non-stubbed, idiomatic code snippets (Good vs Bad comparisons).
5. **Security & Performance Considerations**: Attack vectors, mitigation steps, latency/memory footprint.
6. **Common Pitfalls & Anti-Patterns**: Explicit list of practices to avoid.
7. **Verification Checklist**: Quantifiable verification criteria for automated or manual auditing.

---

## 5. Machine-Readable Semantic Index (`index.json`)

To prevent token waste when agents query `devskill`, an `index.json` catalog maps:
- **Topic IDs**: Unique identifiers (e.g., `sec-auth-jwt`, `fw-nextjs-rsc`, `db-pg-indexing`).
- **File Paths**: Absolute and relative paths to markdown files.
- **Keywords / Tags**: Semantic tags for vector/fuzzy search.
- **Rule Constraints**: Summarized one-line constraints for immediate in-context ingestion.

---

## 6. Maintenance, Quality Control & Extension Process

1. **Zero Hallucination Tolerance**: All commands, package names, configuration keys, and code snippets must be verifiable against current stable releases.
2. **Immutable Commit Standards**: All additions must follow Conventional Commits (`feat(frameworks): add nextjs-15 guide`).
3. **Continuous Review**: Quarterly audits to prune deprecated practices, update security baselines, and integrate emerging LTS software releases.
