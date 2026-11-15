# 🌿 Trunk-Based Development, Git Branching & PR Hygiene

> **Standard Identifier**: `WF-GIT-BRANCHING-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: All Software Engineers, Tech Leads  
> **Classification**: Level 4 Workflow Standard  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Practice Trunk-Based Development. Keep branch lifespans under 24 hours, diff sizes under 400 lines, and merge continuously to `main` using feature flags to decouple deployment from release. Never maintain long-lived feature branches.*

Legacy branching models (GitFlow) with separate `develop`, `release`, and long-lived feature branches create massive merge conflicts, painful "merge hell" weeks, and delayed feedback loops. High-performing engineering teams standardize on Trunk-Based Development.

---

## 2. Branching Models Comparison

```
                    ┌────────────────────────────────────────────────────────┐
                    │               TRUNK-BASED DEVELOPMENT                  │
                    └──────────────────────────┬─────────────────────────────┘
                                               │
               main: ───●────────●────────●────●────────●─────> (Always Deployable)
                        │       ▲ │      ▲
                        └──●─●──┘ └──●───┘
                         feat-A    feat-B  (Branches live < 24-48 hours)
```

| Dimension | Trunk-Based Development | GitFlow (Legacy Anti-Pattern) |
| :--- | :--- | :--- |
| **Branch Lifespan** | $< 24\text{ hours}$ | Weeks or months |
| **Batch Size** | Micro-PRs ($< 400\text{ lines}$) | Giant multi-thousand line diffs |
| **Integration Frequency** | Multiple times per day per developer | Once per sprint or release cycle |
| **Merge Conflicts** | Rare and trivial | Frequent, painful, and error-prone |
| **Deployment Decoupling** | Handled via Feature Flags | Handled via branch staging |

---

## 3. Conventional Commits Specification

Every commit message on a branch or squashed PR must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types
- **`feat`**: A new user-facing feature (triggers `MINOR` SemVer bump).
- **`fix`**: A bug fix (triggers `PATCH` SemVer bump).
- **`refactor`**: Code change that neither fixes a bug nor adds a feature.
- **`perf`**: A code change that improves performance.
- **`test`**: Adding missing tests or correcting existing tests.
- **`chore`**: Changes to the build process or auxiliary tools and libraries.
- **`BREAKING CHANGE:`**: In body or `!` after type (e.g. `feat!: change auth schema`) triggers `MAJOR` SemVer bump.

---

## 4. Stacked Pull Requests Pattern

When building a large, complex feature that requires 1,500 lines of code:
- **Do NOT** open a 1,500-line monolithic PR.
- **DO** break it into a sequence of small, reviewable, stacked PRs:

```
PR 1: feat(db): add orders table migration & schema model (150 lines)
  ▲
  │
PR 2: feat(api): add repository & order creation service layer (200 lines)
  ▲
  │
PR 3: feat(api): add HTTP router endpoint & validation pipe (150 lines)
  ▲
  │
PR 4: feat(ui): add order checkout form component (200 lines)
```

Use tools like `gh-stack` or Graphite to manage git branch rebasing automatically.

---

## 5. Merge Strategies & CI Merge Queues

### Squash and Merge
- Standard for feature branches. Collapses all work-in-progress commits into a single, clean Conventional Commit on `main`.

### GitHub Merge Queue (Train)
- Solves the "merge race condition" where two independent PRs pass CI individually but break `main` when merged together. The merge queue tests PRs speculatively in series against the latest merged trunk before merging.

---

## 6. Verification Checklist & Production Audit

- [ ] Feature branches live $< 48$ hours before merging to `main`.
- [ ] PR diffs contain $< 400$ lines of functional code (excluding lockfiles and snapshots).
- [ ] Commit titles conform strictly to Conventional Commits format (`type(scope): description`).
- [ ] All PRs pass automated CI lint, typecheck, and unit test gates before review.
- [ ] Merge queue is enabled on the primary repository trunk branch.
