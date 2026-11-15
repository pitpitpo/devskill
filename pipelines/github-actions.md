# ⚡ Production GitHub Actions CI/CD Pipeline Architecture

> **Standard Identifier**: `PL-GITHUB-ACTIONS-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: DevOps Architects, Platform Engineers, Full-Stack Developers  
> **Classification**: Level 4 Pipeline Engineering Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Pipelines must be fast (< 5 minutes), deterministic, secure, and reproducible. Use OIDC for cloud authentication instead of static secrets, pin third-party actions to immutable commit SHAs, enforce strict concurrency controls, and cache dependency layers aggressively.*

CI/CD pipelines are the ultimate gatekeeper of production stability. Insecure or slow pipelines stall team momentum and expose infrastructure to credential compromise.

---

## 2. Complete Enterprise CI/CD Pipeline Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                    GIT PUSH / PULL REQUEST             │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼ Concurrency: Cancel In-Progress           ▼
            ┌──────────────────────┐                    ┌──────────────────────┐
            │   LINT & TYPECHECK   │                    │   SECURITY & SAST    │
            │ • Ruff / Biome / ESLint │                 │ • Gitleaks (Secrets) │
            │ • Mypy / tsc strict  │                    │ • Semgrep / Trivy    │
            └──────────┬───────────┘                    └──────────┬───────────┘
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │ All checks pass
                                             ▼
                                ┌───────────────────────────┐
                                │     PARALLEL UNIT TESTS   │
                                │ • Node (Vitest) / Pytest  │
                                │ • Coverage Threshold > 80%│
                                └────────────┬──────────────┘
                                             │
                                             ▼
                                ┌───────────────────────────┐
                                │     INTEGRATION TESTS     │
                                │ • Docker Testcontainers   │
                                │ • Real Postgres & Redis   │
                                └────────────┬──────────────┘
                                             │
                         ┌───────────────────┴───────────────────┐
                         ▼ Branch: main ONLY                     ▼
              ┌────────────────────────┐              ┌────────────────────────┐
              │ DOCKER BUILDX & PUSH   │              │ CLOUD DEPLOY (OIDC)    │
              │ • BuildKit GHA Cache   │              │ • Zero static secrets  │
              │ • Distroless runtime   │              │ • Automated Rollout    │
              └────────────────────────┘              └────────────────────────┘
```

---

## 3. Production GitHub Actions Workflow (`.github/workflows/ci.yml`)

```yaml
name: Enterprise Production Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

# Cancel redundant in-progress runs for the same branch
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

permissions:
  contents: read
  id-token: write # Mandatory for cloud OIDC auth
  security-events: write

jobs:
  lint-and-typecheck:
    name: Code Hygiene & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test-unit-integration:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: [lint-and-typecheck]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - name: Run Tests with Coverage
        run: npm run test:ci -- --coverage

  build-and-push-docker:
    name: Multi-Stage Docker Buildx
    runs-on: ubuntu-latest
    needs: [test-unit-integration]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # Authenticate to AWS ECR via OIDC (Zero static IAM keys)
      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy-role
          aws-region: us-east-1

      - name: Build and Push with Cache
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: 123456789012.dkr.ecr.us-east-1.amazonaws.com/api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## 4. Security Hardening & Principle of Least Privilege

1. **Top-Level Permissions**: Always declare `permissions: read-all` or explicit minimal scopes at the workflow root.
2. **Action SHA Pinning**: Never use `@v1` or `@main` for third-party actions; pin to immutable 40-character commit hashes (e.g., `uses: actions/checkout@b4ffde... # v4.1.1`).
3. **OIDC Federation**: Ban long-lived static AWS/GCP/Azure access keys in GitHub Secrets. Use OpenID Connect (OIDC) tokens with short 15-minute expirations.

---

## 5. Verification Checklist & Production Audit

- [ ] `concurrency` block with `cancel-in-progress` prevents redundant CI runs on PR update.
- [ ] OIDC is configured for cloud deployments with zero static credentials stored in secrets.
- [ ] Docker BuildKit caching (`type=gha`) speeds up image compilation.
- [ ] Pipeline completes from commit to test verification in $< 5\text{ minutes}$.
- [ ] All third-party actions are pinned to immutable commit SHA hashes.
