# 🏗️ Production Scaffolding & Configs (`scaffolding/`)

This directory provides plug-and-play production configurations and architectural starter blueprints for new repositories.

## Subdirectories

- [`configs/`](configs/):
  - [`.editorconfig`](configs/.editorconfig): Universal cross-editor formatting baseline.
  - [`.claude-settings.json`](configs/.claude-settings.json): Declarative Claude Code deterministic hooks (`PreToolUse`, `PostToolUse`, `Stop` using Exit Code `2` blocking).
  - [`tsconfig.base.json`](configs/tsconfig.base.json): Enterprise TypeScript 6/7 (`tsgo`) strict configuration.
  - [`ruff.toml`](configs/ruff.toml): Ultra-fast Python 3.13/3.14 linter and formatter config.
  - [`docker-compose.yml`](configs/docker-compose.yml): Production-parity local dev environment (PostgreSQL 18, Redis 8, Mailpit, MinIO, Adminer).
  - [`.github-ci-template.yml`](configs/.github-ci-template.yml): Universal starter GitHub Actions workflow (Node 24, Python 3.13, Go 1.25, DevSkill CI Gate, Trivy, Gitleaks).
- [`templates/`](templates/):
  - [`api-microservice.md`](templates/api-microservice.md): Production API microservice blueprint.
  - [`enterprise-modular-monolith.md`](templates/enterprise-modular-monolith.md): Enterprise Modular Monolith pattern.
  - [`fullstack-nextjs-fastapi.md`](templates/fullstack-nextjs-fastapi.md): Fullstack Next.js + FastAPI blueprint.
  - [`saas-multi-tenant.md`](templates/saas-multi-tenant.md): Multi-tenant SaaS architecture blueprint with RLS isolation.
