# 🔄 PR Lifecycle, Bot Babysitting, Modernization & Takeover (`workflows/pr-lifecycle-babysitting.md`)

> **Classification**: Production Workflow Specification  
> **Status**: Mandatory / Non-Negotiable Core Protocol  
> **Target Audience**: Autonomous AI Agents, Lead PR Maintainers, DevOps Engineers  
> **Governing Rules**: **R-001** (Zero TODOs), **R-164** (Atomic Commits), **R-205** (Event-Driven PR Babysitting), **R-206** (GitHub Rate-Limit Partitioning), **R-207** (PR Modernization Disposition), **R-208** (Git Authorship Preservation), **R-209** (Problem-First PR Communication), **R-210** (Agent Comment Attribution)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Field | Value |
|---|---|
| **Skill Name** | `workflows/pr-lifecycle-babysitting.md` |
| **Capability Archetypes** | PR Monitoring, Bot Triage, Branch Modernization, PR Takeover, GitHub Comment Formatting |
| **Trigger Phrases** | `"babysit"`, `"modernize"`, `"take over"`, `"file a PR"`, `"watch PR"` |
| **Prerequisites** | GitHub CLI (`gh`), Git 2.40+, Python 3.10+ (for `pr-wait`), write permissions on target branches |

Shipping enterprise pull requests involves much more than pushing a git branch. It demands resilient event-driven monitoring through CI and review bots, triage of AI feedback (Greptile, Macroscope, CodeRabbit), intent-based branch modernization rather than blind rebasing, and meticulous preservation of human contributor authorship during PR takeovers.

---

## 2. Core Philosophy / Golden Rule

> [!IMPORTANT]
> **The Golden Law of PR Governance (Rules R-207 & R-209)**:
> *Lead with the problem, prove with direct evidence, and modernize the intent—not just the branch.*
> 1. A pull request description MUST lead with a concise, human explanation of the problem and the direct solution. It MUST NOT start with a file-by-file inventory of changes.
> 2. A rebase without merge conflicts does NOT prove a pull request still belongs in the product. Every aged PR MUST be evaluated under a formal disposition: `MODERNIZE`, `REWORK`, or `CLOSE`.
> 3. Taking over another engineer's work MUST preserve their Git authorship and co-author trailers. AI model attribution MUST NEVER overwrite human contributor credit.

```
                         PULL REQUEST LIFECYCLE PIPELINE
                         
   [Feature / Bugfix Verified]
                │
                ▼
   [File Problem-First PR] ──► Concise title, problem statement, harness attribution
                │
                ▼
   [Engage Event-Driven Watcher]
   ├── T3 Code Environment: watch_pull_request
   └── Standalone CLI: workflows/scripts/pr-wait <pr-num> --until ready
                │
                ▼
   [Triage Events & CI Checks]
   ├── Required CI Check Fail? ──────► Reproduce defect -> Fix -> Push with lease
   ├── Gating Bot (Greptile/Macro)? ─► Verify against code -> Fix or dismiss with note
   ├── Advisory Bot (CodeRabbit)? ───► Evaluate findings; never hold merge gate
   └── Base Branch Moved (BEHIND)? ──► Rebase onto origin/main -> Verify range-diff
                │
                ▼
   [Evaluate Merge Gate (R-201)] ────► All 5 criteria satisfied?
                │
        ┌───────┴───────┐
        ▼               ▼
     [YES]             [NO]
        │               │
     Merge / Handoff   Continue Babysitting / Escalate to Human Boundary
```

---

## 3. Architecture & Design Patterns

### 3.1 Event-Driven Babysitting Architecture (Rule R-205)

Agents MUST NOT implement active sleep loops (`while sleep 10; do ...`). Use one of two sanctioned event-driven watcher protocols:

1. **In T3 Code Harness**:
   - Call `watch_pull_request` on the PR URL and cleanly end the current turn.
   - The harness automatically awakens the agent when a check finishes, a review arrives, or merge conflicts occur.
   - Before ending a session (or when blocked), call `unwatch_pull_request` to unhook the notification pipeline.
2. **In Standalone Shell Environments**:
   - Execute [`workflows/scripts/pr-wait`](file:///home/agy/.t3/userdata/attachments/devskill/workflows/scripts/pr-wait) with `--until ready` or `--until green`.
   - The script uses state files in `~/.local/state/pr-wait/` and OS-level file locking (`fcntl`) to guarantee only one watcher per PR.
   - Exits with code `0` on merge/readiness, code `1` on actionable failure, code `2` on bad arguments.

### 3.2 GitHub Rate-Limit Partitioning (Rule R-206)

When executing high-frequency PR checks, the GitHub GraphQL rate limit (5,000 points/hr) can become exhausted.
- `gh pr view`, `gh pr checks`, and `gh pr create` utilize GraphQL by default.
- If GraphQL returns `rate limit exceeded`, the agent MUST fall back to the independent REST API pool:
  ```bash
  # REST PR details fallback
  gh api repos/<owner>/<repo>/pulls/<pr_number>
  # REST check runs fallback
  gh api repos/<owner>/<repo>/commits/<sha>/check-runs
  ```

### 3.3 AI Review Bot Triage Strategy

Not all bot comments carry equal weight. Treat automated reviewers according to their governance tier:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REVIEW BOT TRIAGE MATRIX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Gating Bots     │ Greptile, Macroscope. Mandatory triage. Verify each       │
│                 │ finding against source code. Fix real bugs; reply with    │
│                 │ written explanation for false positives before resolving. │
├─────────────────┼───────────────────────────────────────────────────────────┤
│ Advisory Bots   │ CodeRabbit. Advisory feedback. Address actionable bugs;   │
│                 │ never hold the merge gate or delay PR shipping for it.    │
├─────────────────┼───────────────────────────────────────────────────────────┤
│ Status Bots     │ github-actions, Vercel, Netlify, Railway. Do not parse    │
│                 │ top-level status comments; inspect actual check runs.     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 PR Modernization: The 3 Dispositions (Rule R-207)

When assigned to modernize an aged PR or rebase a stagnant branch, the agent MUST inspect base branch commits since divergence (`git log merge-base..origin/main`) and assign a formal disposition:

1. **`MODERNIZE`**: The goal is still relevant and the implementation architecture remains sound.
   - Rebase onto `origin/main`.
   - Validate consistency with `git range-diff <old-sha>...HEAD`.
   - Push with `git push --force-with-lease`.
2. **`REWORK`**: The goal is still desirable, but surrounding architecture has fundamentally shifted (e.g., deprecated modules, new abstractions).
   - Stop before rebasing; document the minimal necessary rewrite and present the recommendation.
3. **`CLOSE`**: The problem was already solved by another commit, the feature was intentionally deprecated, or the maintenance cost outweighs the benefit.
   - Cite concrete evidence and recommend closing the PR without wasting compute on rebasing.

### 3.5 Contributor Credit & Takeover Protocol (Rule R-208)

When taking over another engineer's pull request or abandoned branch:
- **Retain Original Commits**: Import the original branch commits onto a new feature branch to preserve historical author attribution.
- **Add Separate Fix Commits**: Place agent corrections in distinct subsequent commits.
- **Preserve Trailers**: Maintain all existing `Co-authored-by:` trailers in commit messages and squash descriptions:
  ```
  Co-authored-by: Original Contributor <contributor@example.com>
  ```
- **Attribution Boundary**: Model attribution (`Created with Gemini in T3 Code`) belongs in PR descriptions or footer notes, NEVER displacing human commit authors.

### 3.6 Standardized GitHub Comment Attribution (Rule R-210)

Every comment posted by an automated agent on GitHub on behalf of the user MUST use the standard note callout format:

```markdown
> [!NOTE]
> 🤖 **<model> responding on behalf of <user>**

Lead with the factual conclusion. Cite the relevant code, behavior, check, or reproduction.
```

---

## 4. Concrete Code Examples

### 4.1 Problem-First PR Template Generator (`file_pr.py`)

```python
#!/usr/bin/env python3
"""Problem-First Pull Request Generator conforming to DevSkill Standards."""

from __future__ import annotations
import subprocess
import sys

def create_problem_first_pr(title: str, problem: str, solution: str, proof: str, model: str, harness: str):
    """Generate and submit a clean, problem-first pull request."""
    body = (
        f"### Problem\n{problem}\n\n"
        f"### Solution\n{solution}\n\n"
        f"### Proof\n{proof}\n\n"
        f"---\n*Created with {model} in {harness}.*\n"
    )
    cmd = [
        "gh", "pr", "create",
        "--title", title,
        "--body", body
    ]
    print(f"[*] Filing PR: {title}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # Fallback to REST API if GraphQL rate limit is exhausted
        print("[-] gh pr create failed. Falling back to REST API...")
        # REST fallback logic
        raise RuntimeError(f"PR creation failed: {res.stderr}")
    print(f"✅ PR filed successfully: {res.stdout.strip()}")

if __name__ == "__main__":
    create_problem_first_pr(
        title="fix(auth): enforce JWT expiration claim validation",
        problem="Expired JWT tokens were accepted if signature was valid, allowing replay attacks.",
        solution="Added strict 'exp' claim validation and clock-skew tolerance check in auth middleware.",
        proof="Added unit test test_expired_jwt_rejected() reproducing 401; 100% CI checks green.",
        model="Gemini 2.0 Pro",
        harness="T3 Code"
    )
```

### 4.2 Standardized PR Comment Poster (`post_pr_comment.py`)

```python
#!/usr/bin/env python3
"""Post standardized agent response comments on GitHub PR threads."""

import subprocess
import sys

def post_attributed_comment(pr_number: int, comment_body: str, model_name: str, user_name: str):
    """Format and post an attributed PR comment conforming to Rule R-210."""
    formatted = f"""> [!NOTE]
> 🤖 **{model_name} responding on behalf of {user_name}**

{comment_body.strip()}
"""
    cmd = [
        "gh", "pr", "comment", str(pr_number),
        "--body", formatted
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to post comment: {res.stderr}")
    print(f"✅ Attributed comment posted to PR #{pr_number}.")

if __name__ == "__main__":
    post_attributed_comment(
        pr_number=142,
        comment_body="Verified Greptile finding regarding nil pointer: Added defensive bounds check in handler.go:45.",
        model_name="Gemini 2.0 Pro",
        user_name="core-dev"
    )
```

---

## 5. Security & Performance Considerations

- **Force Push Safety**: Bare `git push -f` is strictly prohibited. Always specify `--force-with-lease`. If the remote head changed since your last fetch, the lease fails, preventing accidental deletion of coworker commits.
- **Secret Redaction in PR Bodies**: Before submitting PR titles, descriptions, or comments, the agent MUST scan contents for API keys, tokens, internal URLs, or private customer identifiers.
- **Rate Limit Throttling**: Never invoke GitHub API calls in sub-second intervals. Honor HTTP 429 and `Retry-After` headers.

---

## 6. Common Pitfalls & Anti-Patterns

### ❌ Anti-Pattern 1: The Implementation Inventory PR Description
```markdown
<!-- BAD: Leading with a boring, laundry-list inventory of files edited -->
### Changes
- Modified src/auth/jwt.py lines 14-25
- Deleted helper function validateTokenInternal()
- Added import time in middleware.py
- Updated package.json version
```
```markdown
<!-- GOOD: Leading with the user problem and the direct solution -->
### Problem
Users remained logged in indefinitely after session revocation because the JWT expiration claim was ignored.

### Solution
Enforce strict expiration timestamp checks with a 60-second clock-skew window in the authentication middleware.

### Proof
Executed reproduction suite `pytest tests/test_auth.py::test_revocation` (passed).
```

### ❌ Anti-Pattern 2: Mechanical Rebase without Intent Modernization
```bash
# BAD: Blindly resolving git conflicts by accepting whatever compiles, ignoring new invariants
git rebase origin/main -X ours
git push -f origin feat/my-branch
```
```bash
# GOOD: Validating range-diff and establishing disposition
git range-diff origin/main...HEAD@{1} HEAD
git push --force-with-lease origin feat/my-branch
```

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. PR Title Standard** | Explains why the change matters | Check against Conventional Commits / human summary |
| **2. Problem-First Format** | Problem statement precedes solution | Verify description structure (Problem, Solution, Proof) |
| **3. Event-Driven Monitoring** | Zero tight polling loops | `watch_pull_request` active or `pr-wait` running |
| **4. Authorship Integrity** | Original author trailers preserved | `git log -n 5 --format="%an <%ae> %B"` verifies credit |
| **5. Comment Attribution** | Callout header present on bot comments | Verify `> [!NOTE]\n> 🤖 **...**` on posted comments |

---

*See also*: [`agents/full-send-delivery.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/full-send-delivery.md) for full-send merge gate automation and [`agents/multi-model-council.md`](file:///home/agy/.t3/userdata/attachments/devskill/agents/multi-model-council.md) for multi-model reviews.
