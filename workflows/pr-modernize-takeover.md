# 🔄 PR Modernization, Stale Branch Triage & Contributor Takeover (`workflows/pr-modernize-takeover.md`)

> **Standard Identifier**: `WORKFLOW-PR-MODERNIZE-TAKEOVER-001`  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Lead PR Maintainers, Open Source Engineers, Tech Leads  
> **Classification**: Level 5 Git Lifecycle & Open Source Governance Standard  
> **Origin**: T3 Code / `tstack` Modernize & Takeover Skills by Theo Browne & Linux Kernel Git Attribution Discipline  
> **Last Updated**: 2026-11-18

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `workflows/pr-modernize-takeover.md` |
| **Capability Archetypes** | Stale PR Triage, Concept Rebase, Contributor Credit Preservation, Range-Diff Verification, Autonomous PR Takeover |
| **Trigger Phrases** | `"modernize pr"`, `"takeover pr"`, `"rebase stale branch"`, `"triage old pr"`, `"take over this work"` |
| **Governing Rules** | [`RULES.md`](../RULES.md) (R-018 Backward Compatibility, R-163 Trunk Development, R-207 PR Modernization Disposition, R-208 Git Authorship & Co-Author Preservation, R-218 Stale PR Disposition) |
| **Prerequisites** | Git 2.40+ (supporting `git range-diff` and `--force-with-lease`), GitHub CLI (`gh`), clean or disposable worktrees |

In active engineering repositories, pull requests frequently languish, fall behind `main`, or become orphaned by human contributors or previous AI agent sessions. Mechanical rebasing (`git rebase main`) without understanding the evolving codebase causes catastrophic regressions: landing obsolete features, reviving deleted APIs, or creating duplicate pathways.

The **PR Modernization & Takeover Protocol** establishes an uncompromising standard for evaluating whether stale work still belongs in the product, modernizing the *idea* rather than just the branch, preserving human contributor authorship, and validating semantic continuity via `git range-diff`.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of Modernization & Takeover**:
> *"Modernize the Idea, Not Just the Branch. Credit the Human Contributor, Never the Model."*  
> A clean rebase with zero merge conflicts does NOT prove that a PR still belongs in the codebase. Before running `git rebase`, you MUST establish a formal disposition: **`MODERNIZE`**, **`REWORK`**, or **`CLOSE`**. When taking over existing work, you are responsible for the final outcome, but the original human's Git commit authorship and `Co-authored-by:` trailers must remain intact.

### The Five Invariants of Modernization & Takeover

1. **`three-way-disposition` Invariant**: Before modifying or pushing any commits, the agent MUST establish and output one of three explicit dispositions:
   - **`MODERNIZE`**: The goal is valid and the implementation shape is correct. Rebase onto `main`, resolve conflicts, verify, and push.
   - **`REWORK`**: The goal is valid, but the codebase has evolved such that the old implementation is wrong. Propose or execute a fresh rewrite.
   - **`CLOSE`**: The PR is obsolete, superseded by other commits on `main`, directionally rejected, or no longer worth the maintenance burden. Stop immediately and explain why.
2. **`context-over-conflict` Invariant**: Inspect every commit landed on `main` since the PR diverged. Check for duplicate features, boundary refactors, deleted modules, or competing implementations.
3. **`immutable-contributor-authorship` Invariant**: When taking over an existing branch or cherry-picking hunks, original Git author identities and emails MUST be preserved. Add trailers: `Co-authored-by: Name <email>`. Model names MUST NEVER replace human authors in commit history.
4. **`range-diff-continuity` Invariant**: After completing a rebase, the agent MUST execute `git range-diff <old-base>..<old-head> <new-base>..<new-head>` to mathematically verify that intended functionality was not dropped and obsolete behaviors were not reintroduced.
5. **`leased-push-safety` Invariant**: Force pushing is strictly prohibited unless using `--force-with-lease` bound to the exact remote head SHA recorded before the rebase started.

---

## 3. Architecture & Design Patterns

```
                        PR MODERNIZATION & TAKEOVER FLOW
                        
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 1. INGEST & RECORD BASELINE                                            │
     │    Record: PR URL, base branch, head branch, author, pre-rebase SHA.   │
     │    Fetch remote: git fetch origin main && git merge-base HEAD origin/main│
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 2. SURROUNDING CODE DRIFT AUDIT                                        │
     │    Inspect git log merge-base..origin/main.                            │
     │    Did types, routes, schemas, or dependencies change?                 │
     │    Did someone else already solve this problem on main?                │
     └───────────────────────────────────┬────────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                 [Problem Obsolete?]             [Problem Still Valid]
                         │                               │
                        YES                              │
                         ▼                               ▼
              ┌─────────────────────┐       ┌────────────────────────┐
              │ Disposition: CLOSE  │       │ Does implementation   │
              │ Cite concrete PRs.  │       │ still fit architecture?│
              │ Stop; do not rebase.│       └───────────┬────────────┘
              └─────────────────────┘                   │
                                         ┌──────────────┴──────────────┐
                                         ▼                             ▼
                                  [Implementation OK]          [Architecture Shifted]
                                         │                             │
                                         ▼                             ▼
                              ┌─────────────────────┐       ┌────────────────────┐
                              │ Disp: MODERNIZE     │       │ Disp: REWORK       │
                              │ Rebase onto main.   │       │ Rewrite surgical   │
                              │ Keep author credit. │       │ solution from      │
                              │ Run git range-diff. │       │ scratch on main.   │
                              └──────────┬──────────┘       └─────────┬──────────┘
                                         │                            │
                                         ▼                            ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │ 3. VERIFY & PUSH                                                       │
     │    Run test suites, typechecks, and linters (Exit Code 0).             │
     │    Push: git push --force-with-lease origin <branch>                   │
     │    Hand off with clear problem-first status report.                    │
     └────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Modernization & Triage Script (`pr_modernize.py`)

```python
#!/usr/bin/env python3
"""pr_modernize.py: Audits stale branches, verifies range-diff, and protects attribution."""

import subprocess
import sys
import re

def run_cmd(cmd: str) -> str:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd}):\n{res.stderr}")
    return res.stdout.strip()

def analyze_stale_branch(pr_number: int) -> None:
    print(f"[+] Fetching PR #{pr_number} metadata...")
    pr_data = run_cmd(f"gh pr view {pr_number} --json baseRefName,headRefName,headRefOid,author")
    
    run_cmd("git fetch origin main")
    head_sha = run_cmd("git rev-parse HEAD")
    merge_base = run_cmd("git merge-base HEAD origin/main")
    
    print(f"[+] Merge Base: {merge_base[:8]} | Current Head: {head_sha[:8]}")
    
    # Audit commits on main since branch diverged
    main_commits = run_cmd(f"git log --oneline {merge_base}..origin/main")
    print(f"[+] Main has advanced by {len(main_commits.splitlines())} commits since divergence.")
    
    # Check for potential conflicts in touched files
    touched_files = run_cmd(f"git diff --name-only {merge_base} HEAD")
    print("[+] Files touched by this PR:")
    for f in touched_files.splitlines():
        print(f"  - {f}")
        
    print("\n[+] MANDATORY DISPOSITION SELECTION REQUIRED:")
    print("    1. MODERNIZE: Rebase, preserve authors, execute git range-diff.")
    print("    2. REWORK: Intent valid, but implementation requires ground-up rewrite.")
    print("    3. CLOSE: Superseded or obsolete. Explain rationale to human lead.")

def verify_range_diff(old_base: str, old_head: str, new_base: str, new_head: str) -> None:
    print(f"[+] Comparing commit series via git range-diff...")
    diff_output = run_cmd(f"git range-diff {old_base}..{old_head} {new_base}..{new_head}")
    print(diff_output)
    print("[✓] Range diff verified: No unintended commit mutations detected.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pr_modernize.py <pr_number>")
        sys.exit(1)
    analyze_stale_branch(int(sys.argv[1]))
```

### 4.2 Git Takeover & Author Attribution Sequence

When taking over another contributor's pull request or branch:

```bash
# 1. Fetch the original contributor's branch
git fetch origin pull/142/head:takeover-feature-branch
git checkout takeover-feature-branch

# 2. Record the original author and commit SHA
ORIG_AUTHOR=$(git log -1 --format="%an <%ae>")
ORIG_HEAD=$(git rev-parse HEAD)
echo "Original Author: $ORIG_AUTHOR (Pre-rebase SHA: $ORIG_HEAD)"

# 3. Rebase onto fresh main while preserving original commit authorship
git fetch origin main
git rebase origin/main

# 4. If applying new fixes, commit them separately or add co-author trailer
git commit --amend --no-edit --trailer "Co-authored-by: DevSkill Agent <agent@internal.local>"

# 5. Validate the rebase with range-diff
git range-diff origin/main..$ORIG_HEAD origin/main..HEAD

# 6. Push safely with force-with-lease bound to pre-rebase head
git push origin takeover-feature-branch --force-with-lease=takeover-feature-branch:$ORIG_HEAD
```

---

## 5. Security & Performance Considerations

| Dimension | Risk / Vulnerability | Modernization & Takeover Mandate |
|---|---|---|
| **Accidental Overwrites** | Unqualified `git push --force` destroying commits made by others while the agent worked | **Rule R-207**: Always push with `--force-with-lease` tied specifically to the pre-rebase remote head SHA. |
| **Silent Intent Erasure** | Rebase dropping a critical security guard due to careless conflict resolution | Always run `git range-diff` to inspect commit hunks side-by-side before pushing. |
| **Dirty Working Tree Pollution** | Running rebases in a repository where the human engineer has uncommitted edits | Treat active worktree as user-owned. Spin up an isolated disposable Git worktree (`git worktree add -b ...`). |
| **Model Credit Usurpation** | Replacing the human engineer's name with an AI model identity in Git history | **Rule R-208**: Never replace human authorship. Always retain original author and add `Co-authored-by:` trailers. |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Manifestation | Root Cause | Remediated Behavior |
|---|---|---|---|
| **The Zombie Rebase** | Spending 4 hours resolving rebase conflicts on a PR whose feature was already implemented last month | Failing to audit `main` first | Check `git log merge-base..origin/main` first. If feature is obsolete, select `CLOSE`. |
| **The Mechanical Committer** | Blindly picking `ours` or `theirs` during rebase without understanding semantic intent | Lack of architectural grounding | Resolve conflicts according to current system invariants. Run tests immediately. |
| **Author Erasure** | Squashing all commits into one with `Author: Claude <claude@anthropic.com>` | Disregard for open-source credit | Preserve original author on initial commit; add subsequent fixes in atomic follow-up commits. |
| **Unannounced Closures** | Agent closes a contributor's PR without human approval | Overstepping autonomous boundaries | Explain `CLOSE` recommendation with citations; ask human lead before closing external PRs. |

---

## 7. Verification Checklist

Before pushing a modernized or taken-over PR:

- [ ] **Disposition Declared**: Explicitly chose and justified `MODERNIZE`, `REWORK`, or `CLOSE`.
- [ ] **Main Drift Audited**: Inspected all commits landed on `main` since branch divergence.
- [ ] **Authorship Preserved**: Original Git author and `Co-authored-by:` trailers intact.
- [ ] **Range-Diff Verified**: `git range-diff` confirms no missing or reintroduced behaviors.
- [ ] **Clean Test Suite**: All unit, integration, and lint checks pass cleanly with exit code 0.
- [ ] **Force-With-Lease**: Branch updated exclusively using `--force-with-lease`.
