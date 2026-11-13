# 🏷️ Release Management & Semantic Versioning (`release-versioning.md`)

> **Standard**: Semantic Versioning 2.0.0 (`MAJOR.MINOR.PATCH`)  
> **Automation**: Release Please / Semantic Release / Changesets

---

## 1. SemVer Rules

Given a version number `MAJOR.MINOR.PATCH`:
1. **MAJOR**: Incompatible API changes, breaking schema modifications, deprecated endpoint removal.
2. **MINOR**: Backward-compatible new functionality (new endpoints, new non-breaking options).
3. **PATCH**: Backward-compatible bug fixes and internal refactors.

---

## 2. Automated Release Workflow

```
[PR merged to main]
        │
        ▼
[Analyze Conventional Commits]
 ├── feat: -> Bump MINOR
 ├── fix:  -> Bump PATCH
 └── BREAKING CHANGE or !: -> Bump MAJOR
        │
        ▼
[Generate CHANGELOG.md]
        │
        ▼
[Create Git Tag (v1.4.0)]
        │
        ▼
[Trigger Production Deployment Pipeline]
```
