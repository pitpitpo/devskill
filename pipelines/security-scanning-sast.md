# 🛡️ Shift-Left Security: SAST, DAST, SCA & Container Scanning Automation

> **Standard Identifier**: `PL-SECURITY-SCANNING-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: DevSecOps Engineers, Security Architects, CI/CD Engineers  
> **Classification**: Level 4 Pipeline Engineering Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Shift security left into every pull request. Catching a vulnerability in code review costs $10; fixing it after a production breach costs millions. Block vulnerable dependencies, plain-text secrets, container CVEs, and insecure code patterns deterministically in CI.*

Modern application security requires an automated defense-in-depth scanning pipeline across 5 distinct domains:
1. **Secret Detection**: Block API keys, private certs, and credentials before they enter git history.
2. **SAST (Static Application Security Testing)**: AST-level semantic analysis of application source code.
3. **SCA (Software Composition Analysis)**: Open-source dependency vulnerability and license auditing.
4. **Container Image Scanning**: Base image OS vulnerabilities and misconfigurations.
5. **DAST (Dynamic Application Security Testing)**: Black-box runtime attack simulation against running preview environments.

---

## 2. Shift-Left Security Pipeline Architecture

```
   ┌─────────────────────────────────────────────────────────┐
   │                    DEVELOPER COMMIT                     │
   └────────────────────────────┬────────────────────────────┘
                                │ Pre-commit hook: Gitleaks (Blocks commit if secret detected)
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │                 PULL REQUEST CI WORKFLOW                │
   ├────────────────────────────┬────────────────────────────┤
   │ 1. Secret Scan             │ Gitleaks / TruffleHog      │
   │ 2. SAST Analysis           │ Semgrep / SonarQube        │
   │ 3. SCA Dependency Audit    │ Trivy / Snyk / Dependabot  │
   │ 4. Container CVE Scan      │ Trivy / Grype              │
   │ 5. IaC Security Audit      │ Checkov / tfsec            │
   └────────────────────────────┴────────────────────────────┘
                                │ All Gates Pass (0 High/Critical CVEs)
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │                  MERGE & PREVIEW DEPLOY                 │
   └────────────────────────────┬────────────────────────────┘
                                │ 6. DAST Scan: OWASP ZAP Against Ephemeral URL
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │                  PRODUCTION RELEASE GATE                │
   └─────────────────────────────────────────────────────────┘
```

---

## 3. Production GitHub Actions Security Pipeline

```yaml
name: Security & Vulnerability Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  secret-scan:
    name: Secret Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  sast-semgrep:
    name: SAST Semantic Code Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten
            p/r2c-security-checklist
          generateSarif: "1"
      - name: Upload SARIF to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: semgrep.sarif

  dependency-sca:
    name: SCA Dependency Vulnerabilities
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy Vulnerability Scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1' # Fails CI if High or Critical found
          ignore-unfixed: true

  container-scan:
    name: Container Image Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Local Container Image
        run: docker build -t test-image:${{ github.sha }} .
      - name: Scan Image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: test-image:${{ github.sha }}
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
```

---

## 4. Triage SLAs & Security Policy Standards

| Finding Severity | CVSS Score | Remediation SLA | CI Blocking Behavior |
| :--- | :--- | :--- | :--- |
| **Critical** | 9.0 - 10.0 | $\le 24\text{ hours}$ | Hard Block (PR cannot merge; production deployment blocked) |
| **High** | 7.0 - 8.9 | $\le 7\text{ days}$ | Hard Block (PR cannot merge unless signed exemption granted) |
| **Medium** | 4.0 - 6.9 | $\le 30\text{ days}$ | Warning (PR permitted, tickets generated automatically) |
| **Low** | 0.1 - 3.9 | $\le 90\text{ days}$ | Informational (Tracked in monthly security review) |

---

## 5. Verification Checklist & Production Audit

- [ ] Secret detection (Gitleaks) runs on all branches and pre-commit hooks.
- [ ] SAST scanning (Semgrep) enforces OWASP Top 10 rulesets with SARIF output.
- [ ] SCA tools (Trivy / Snyk) block merges on unfixed High and Critical CVEs.
- [ ] Container images are scanned before pushing to production registries.
- [ ] Dependencies are kept up to date via automated Renovate or Dependabot PRs.
