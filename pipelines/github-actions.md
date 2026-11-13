# ⚙️ Production GitHub Actions CI/CD Pipeline (`github-actions.md`)

> **Classification**: Production Continuous Integration & Continuous Delivery  
> **Target**: GitHub Actions Runners (Ubuntu 22.04 LTS / 24.04 LTS)

---

## 1. Enterprise Multi-Job Pipeline Anatomy

```
[Push to main / PR]
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
┌──────────────────────┐   ┌──────────────────────┐
│  Job: Lint & Types   │   │  Job: Security Audit │
│  tsc, eslint, ruff   │   │  gitleaks, trivy     │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           └─────────────┬────────────┘
                         ▼
             ┌──────────────────────┐
             │  Job: Test Suite     │
             │  Postgres & Redis svc│
             └──────────┬───────────┘
                        ▼
             ┌──────────────────────┐
             │  Job: Build & Push   │
             │  Docker multi-stage  │
             └──────────┬───────────┘
                        ▼
             ┌──────────────────────┐
             │  Job: Deploy Prod    │
             │  (Protected Env)     │
             └──────────────────────┘
```

---

## 2. Complete Workflow Manifest (`.github/workflows/ci-cd.yml`)

```yaml
name: Production CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-and-typecheck:
    name: Code Quality & Type Safety
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

  security-scan:
    name: Security & Secret Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Gitleaks Secret Scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Trivy Dependency CVE Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'

  test:
    name: Automated Test Suite
    needs: [lint-and-typecheck, security-scan]
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379

  build-and-push:
    name: Container Build & Push
    needs: [test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }},ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
