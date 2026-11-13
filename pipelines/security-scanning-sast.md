# 🛡️ Automated Security Scanning & SAST/DAST (`security-scanning-sast.md`)

> **Classification**: Automated Security Quality Gates  
> **Target**: CI/CD Pipelines, Pre-Commit Hooks, DevSecOps

---

## 1. Multi-Tier Security Scanning Matrix

| Category | Tool | Scope | Trigger | Fail Threshold |
|---|---|---|---|---|
| **Secret Scanning** | **Gitleaks** / GitGuardian | Git history & staged diffs | Pre-commit & CI | Any leak |
| **Dependency SAST** | **Trivy** / Snyk | `package-lock.json`, `poetry.lock` | Every PR | CVSS >= 7.0 (High/Critical) |
| **Static Code SAST**| **Semgrep** | Source code rules & AST patterns | Every PR | High confidence vulnerabilities |
| **Container Images**| **Trivy Image** / Grype | Built Docker layers & OS packages | Post-build | High/Critical OS CVEs |
| **DAST (Dynamic)**  | **OWASP ZAP** | Running ephemeral staging endpoints | Post-deploy | High vulnerability findings |

---

## 2. Local Pre-Commit Hook Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```
