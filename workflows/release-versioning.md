# 🏷️ Semantic Versioning, Automated Releases & Changelog Governance

> **Standard Identifier**: `WF-RELEASE-SEMVER-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Release Engineers, DevOps Architects, Tech Leads  
> **Classification**: Level 4 Workflow Standard  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Never create releases or edit changelogs manually. Tie all version increments strictly to Semantic Versioning 2.0.0 and automate artifact tagging, changelog generation, and package publishing from Conventional Commits in CI.*

Manual release workflows produce untracked commits, broken dependency constraints, and inconsistent release notes. Industrial engineering relies on deterministic release automation via **Changesets** (monorepos) or **semantic-release** (single repos).

---

## 2. Semantic Versioning (SemVer 2.0.0) Specification

Given a version number `MAJOR.MINOR.PATCH`:

```
           MAJOR . MINOR . PATCH [-PRERELEASE] [+BUILD]
             │       │       │
             │       │       └── Backward-compatible bug fixes
             │       └────────── Backward-compatible new functionality
             └────────────────── Incompatible breaking API changes
```

1. **`MAJOR`**: Incompatible API changes (breaking endpoints, schema drops, removed configuration flags).
2. **`MINOR`**: Backward-compatible new functionality (new endpoint, optional request field).
3. **`PATCH`**: Backward-compatible bug fixes (performance tuning, security patches, internal bug remediation).

---

## 3. Automated Release Engineering Pipeline

```
   ┌────────────────────────────────────────────────────────┐
   │             RELEASE PROMOTION WORKFLOW                 │
   └──────────────────────────┬─────────────────────────────┘
                              │
     1. Developer submits PR with Conventional Commit or Changeset
                              ▼
     2. PR merged to `main` branch via Squash or Rebase
                              ▼
     3. CI Release Job runs:
        • Analyzes commits since last tag
        • Calculates next SemVer version
        • Generates CHANGELOG.md entry
        • Creates Git tag (e.g. `v2.4.1`)
        • Builds & pushes container images to registry
        • Publishes packages to npm / PyPI / Crates.io
        • Generates GitHub Release with signed artifacts
```

---

## 4. Multi-Channel Release Strategies

| Channel | Branch / Tag Pattern | Audience | Stability | Deployment Automation |
| :--- | :--- | :--- | :--- | :--- |
| **Nightly / Canary** | `canary` (`v2.5.0-canary.12`) | Internal dogfooding, automated smoke suites | Volatile | Continuous automated deploy on merge |
| **Beta** | `beta` (`v2.5.0-beta.1`) | Early-access opt-in customers | High | Automated deploy to staging environment |
| **Stable** | `main` (`v2.5.0`) | 100% production users | Production Gate | Triggered via automated release tags with canary rollouts |

---

## 5. Hotfix & Emergency Patch Protocol

When an urgent production regression occurs:

```
                  v1.2.0 (Tag)
                     │
                     ▼
          Branch `hotfix/v1.2.1`
                     │
         [Commit: fix(auth): ...]
                     │
                     ▼
                 PR to `main`
                     │
                     ▼
          Tag `v1.2.1` & Deploy
```

1. Branch from the exact production release tag: `git checkout -b hotfix/v1.2.1 tags/v1.2.0`.
2. Apply the atomic minimal fix with regression unit test.
3. Open PR directly to `main`; merge and trigger automated patch release (`v1.2.1`).

---


---


---

## 4. Concrete Release Automation Configuration

```json
// .changeset/config.json
{
  "$schema": "https://unpkg.com/@changesets/config/schema.json",
  "changelog": "@changesets/cli/changelog-github",
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "restricted",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
```

```yaml
# .github/workflows/release.yml
name: Release & Publish Packages

on:
  push:
    branches: [main]

permissions:
  contents: write
  packages: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - name: Create Release Pull Request or Publish
        uses: changesets/action@v1
        with:
          publish: npm run release:publish
          version: npm run release:version
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_PUBLISH_TOKEN }}
```

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Manual Version Bumping** | Editing `package.json` version manually | Version conflicts, missing git tags, unrecorded changelogs | Automate releases via Changesets or semantic-release in CI |
| **Breaking Changes in Minor Releases** | Introducing breaking API changes under SemVer MINOR | Breaks downstream consumers unexpectedly | Breaking changes mandate a SemVer MAJOR increment |
| **Untracked Release Commits** | Pushing directly to release branches | Inability to reproduce exact production binaries | Every release must correspond to an immutable signed git tag |

## 6. Verification Checklist & Production Audit

- [ ] All commits on main follow Conventional Commits standard.
- [ ] Releases and git tags are created strictly by automated CI bots, never developer laptops.
- [ ] CHANGELOG.md is generated deterministically from commit metadata.
- [ ] Container images and binary artifacts are tagged with both SemVer (`v1.2.1`) and git commit SHA.
- [ ] Release pipelines publish provenance attestations and SBOMs (Software Bill of Materials).
