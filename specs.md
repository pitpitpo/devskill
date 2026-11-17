# 📐 DevSkill Technical Specification (`specs.md`)

> **Document Version**: 1.2.0 (Updated: 2026-11-17)  
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
├── SKILL.md                          # Top-level AI Agent Skill Specification
├── README.md                         # Main Documentation, Architecture Overview & Quick Start
├── specs.md                          # Complete System Specification (This Document)
├── RULES.md                          # Non-Negotiable Universal Engineering Rules
├── ROUTING.md                        # Task Archetype Router & Context Retrieval Directives
├── security.md                       # Comprehensive Production Security Standards & Checklist
├── agents.md                         # Autonomous Agent Protocols, Boundaries & Execution Guardrails
├── decisions.md                      # Tech Stack & Architecture Decision Matrices (The Selector)
├── index.json                        # Machine-Readable Catalog & Fast Token Index for AI Retrieval
│
├── agents/                           # Autonomous Agent Sub-Skills & Execution Protocols
│   ├── orchestrator.md               # Multi-Agent DAGs, Fencing Leases, Sagas & Reconciler Loops
│   ├── poteto-discipline.md          # Minimal Diff, Surgical Engineering & Evidence Standards
│   ├── tdd-reproduction.md           # Reproduction-First TDD, Defect Localization & Isolation
│   └── arena-evaluator.md            # Multi-Solution Arena Scoring & Architectural Trade-offs
│
├── frameworks/                       # Framework-Specific Deep Mastery Guides
│   ├── README.md                     # Directory index and framework selection guidance
│   ├── frontend/
│   │   ├── nextjs.md                 # Next.js 14/15 App Router, RSC, Server Actions, Caching, Edge
│   │   ├── react.md                  # React 18/19 Core, Concurrency, Hooks, Profiling, Render Trees
│   │   ├── vue-nuxt.md               # Vue 3 Composition API, Nuxt 3 Hybrid SSR, Pinia, Nitro
│   │   ├── sveltekit.md              # Svelte 5 Runes, SvelteKit Form Actions, Loaders, Adapters
│   │   └── tailwindcss.md            # Tailwind CSS v3/v4, Design Tokens, JIT, Dark Mode, Architecture
│   ├── backend/
│   │   ├── fastapi.md                # Python FastAPI, Pydantic v2, AsyncIO, Dependency Injection, Uvicorn
│   │   ├── nestjs.md                 # Enterprise NestJS, Modular Hexagonal Architecture, Guards, CQRS
│   │   ├── django.md                 # Django 5 & DRF, ORM Optimization, Celery, Security Hardening
│   │   ├── express.md                # TypeScript Express, Middleware Chains, Error Boundaries, Rate Limits
│   │   ├── spring-boot.md            # Java Spring Boot 3, Spring Security, JPA, Virtual Threads (Project Loom)
│   │   ├── go-gin-axum.md            # Go (Gin/Echo/Chi) & Rust (Axum/Actix-web) High-Throughput Services
│   │   └── dotnet-aspnet.md          # C# .NET 8/9 Minimal APIs, EF Core, Middleware Pipeline, Caching
│   ├── erp/
│   │   ├── README.md                 # ERP Ecosystem Taxonomy, Selection Matrix & Common Ledger Invariants
│   │   ├── odoo.md                   # Odoo 17/18 Architecture, Models/ORM, Computed Fields, XML Views & Security
│   │   └── erpnext.md                # Frappe Framework v15/v16 & ERPNext, DocType Lifecycle & Submittables
│   └── mobile/
│       ├── react-native-expo.md      # Expo Router, Native Modules, Hermès Engine, Performance Tuning
│       ├── flutter.md                # Dart/Flutter 3+, Riverpod/Bloc, Platform Channels, Shaders
│       └── android-aosp.md           # Android 14/15/16 AOSP, Project Treble, Stable AIDL HAL, Soong & SELinux
│
├── sections/                         # Domain-Specific Cross-Cutting Architectural Layers
│   ├── README.md                     # Directory index and domain taxonomy
│   ├── backend/
│   │   ├── api-design.md             # RESTful Standards, GraphQL, gRPC, tRPC, Idempotency, Versioning
│   │   ├── microservices-vs-monolith.md # Modular Monolith vs Distributed Microservices, Domain-Driven Design
│   │   ├── caching-strategies.md     # Redis, Cache-Aside, Write-Through, Invalidation, Stampede Protection
│   │   └── background-jobs-queues.md # Celery, BullMQ, Kafka, RabbitMQ, SQS, Dead Letter Queues, Backoffs
│   ├── frontend/
│   │   ├── state-management.md       # Client vs Server State, TanStack Query, Zustand, Jotai, Redux Toolkit
│   │   ├── accessibility-a11y.md     # WCAG 2.2 AA Compliance, ARIA Roles, Focus Trap, Screen Readers
│   │   └── web-performance.md        # Core Web Vitals (LCP, INP, CLS), Bundle Splitting, Image Optimization
│   ├── database/
│   │   ├── postgresql-mastery.md     # Query Plans (EXPLAIN ANALYZE), B-Tree/GIN/GiST Indexes, Vacuuming, MVCC
│   │   ├── schema-migrations.md      # Zero-Downtime Migrations, Expand/Contract Pattern, Alembic, Prisma
│   │   ├── nosql-redis-vector.md     # MongoDB, Redis Data Structures, Pgvector, DynamoDB Single-Table Design
│   │   └── connection-pooling.md     # PgBouncer, Connection Sizing, Timeout Configuration, Deadlock Handling
│   ├── erp-enterprise/
│   │   ├── README.md                 # Enterprise Financial, Supply Chain & Accounting Invariants
│   │   ├── core-accounting-ledger.md # Double-Entry Bookkeeping Invariants, Immutability & Multi-Currency Ledger
│   │   └── inventory-supply-chain.md # FIFO Inventory Queues, Landed Cost Distribution & Perpetual Valuation
│   ├── systems-kernel/
│   │   ├── README.md                 # Systems & Kernel Overview, Ring 0 Memory Safety & Atomic Context Rules
│   │   └── linux-kernel-driver.md    # Linux 6.6+ Character & Platform Drivers, Device Tree, Mutexes & eBPF
│   ├── devops-infrastructure/
│   │   ├── docker-containers.md      # Multi-Stage Builds, Rootless Execution, Distroless Images, Layer Caching
│   │   ├── kubernetes-cloud.md       # Deployments, StatefulSets, HPA, Services, Ingress, Probes, Resource Limits
│   │   ├── terraform-iac.md          # Infrastructure as Code, State Locking, Module Structure, Drift Control
│   │   └── observability-telemetry.md# OpenTelemetry (Traces, Metrics, Logs), Prometheus, Grafana, Jaeger
│   └── testing-qa/
│       ├── test-pyramid.md           # Testing Strategy: Unit (70%), Integration (20%), E2E (10%), Mocks vs Real
│       ├── integration-contract.md   # Testcontainers, Database Fixtures, Consumer-Driven Pact Testing
│       └── e2e-playwright.md         # Playwright Framework, Page Object Model, CI Parallelization, Traces
│
├── languages/                        # Deep Idiomatic Language Standards
│   ├── README.md                     # Directory overview and language benchmarks
│   ├── typescript.md                 # Strict Mode, Type Narrowing, Generics, Utility Types, Zod Integration
│   ├── python.md                     # Modern Python 3.12+, PEP 8, Type Hints, Ruff/Mypy, Poetry/UV, AsyncIO
│   ├── golang.md                     # Idiomatic Go, Goroutines, Channels, Mutexes, Error Wrapping, Interfaces
│   ├── rust.md                       # Ownership, Borrowing, Lifetimes, Traits, Tokio Async, Result/Error Handling
│   ├── java.md                       # Modern Java 21 LTS, Records, Pattern Matching, Sealed Classes, Loom
│   ├── c-cpp.md                      # Modern ISO C23 & C++23/26, RAII Lifetimes, Memory Safety & Concurrency
│   └── sql.md                        # ANSI SQL, CTEs, Window Functions, Index-Friendly Filtering, Transactions
│
├── workflows/                        # Development & Operational Workflows
│   ├── README.md                     # Directory overview
│   ├── git-branching-pr.md           # Trunk-Based Development, Conventional Commits, PR Hygiene
│   ├── release-versioning.md         # Semantic Versioning (SemVer 2.0.0), Changelogs, Tagging Automations
│   ├── code-review-standards.md      # Senior PR Review Checklist, Blocking vs Non-Blocking Comments
│   ├── incident-response.md          # Severity Tiers (P0-P4), On-Call Runbooks, Blameless Post-Mortems
│   └── feature-flags.md              # Trunk Development, Dark Launches, Flag Lifecycles, Kill Switches
│
├── pipelines/                        # CI/CD Automation Specifications & Templates
│   ├── README.md                     # Pipeline architectures and security scanning
│   ├── github-actions.md             # Production Workflow: Lint -> Typecheck -> Test -> Build -> Scan -> Deploy
│   ├── gitlab-ci.md                  # Multi-Stage YAML, Artifacts, Cache Keys, Environment Deployments
│   ├── security-scanning-sast.md     # SAST/DAST Tooling: Snyk, Trivy, Gitleaks, Semgrep, SonarQube
│   └── deployment-strategies.md      # Blue/Green, Canary Deployments, Rolling Updates, GitOps ArgoCD
│
└── scaffolding/                      # Battle-Tested Configurations & Templates
    ├── README.md                     # Scaffolding instructions
    ├── configs/
    │   ├── .editorconfig             # Universal code styling
    │   ├── tsconfig.base.json        # Enterprise TypeScript base compiler options
    │   ├── ruff.toml                 # Ultra-fast Python linter and formatter config
    │   ├── docker-compose.yml        # Production-like local dev environment (Postgres, Redis, Mailpit)
    │   └── .github-ci-template.yml   # Universal GitHub Actions workflow
    └── templates/
        ├── fullstack-nextjs-fastapi.md   # Next.js 15 + FastAPI architecture blueprint
        └── enterprise-modular-monolith.md # Modular Monolith domain scaffolding
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
