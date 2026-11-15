# 🔍 Senior Engineering Code Review Standards & PR Hygiene

> **Standard Identifier**: `WF-CODE-REVIEW-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Software Engineers, Tech Leads, Engineering Managers  
> **Classification**: Level 4 Workflow Standard  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Code review is a critical engineering quality gate, collective code ownership mechanism, and architecture alignment checkpoint. It is not a forum for subjective style debates or nitpicking formatting. Automate syntax in CI; focus human reviews on system architecture, security invariants, data modeling, and failure modes.*

High-velocity engineering teams maintain high code quality by enforcing clear review SLAs, structured comment conventions, and small batch sizes (< 400 lines of diff per PR).

---

## 2. The Conventional Comments Standard

Reviewers must prefix comments with conventional labels to indicate severity and actionability:

| Label | Meaning | Blocking? | Example |
| :--- | :--- | :--- | :--- |
| **`issue`** | A critical bug, security vulnerability, data race, or logic error | **Yes (Blocking)** | `issue: This query is vulnerable to SQL injection because raw user input is concatenated.` |
| **`suggestion`** | A cleaner or more idiomatic alternative implementation | **Optional** | `suggestion: We could use a Set lookup here to reduce time complexity from O(N^2) to O(N).` |
| **`question`** | Seeking clarification on intent or requirement | **Requires Reply** | `question: How does this endpoint handle concurrent updates from multiple browser tabs?` |
| **`nitpick`** | Minor polish (naming, comment wording) | **No** | `nitpick: Consider renaming 'data' to 'activeCustomers' for clarity.` |
| **`praise`** | Commending clean abstractions, thorough tests, or performance wins | **No** | `praise: Great job covering the edge case where the webhook arrives before the order row exists!` |

---

## 3. Senior Reviewer Comprehensive Checklist

### 3.1 Architecture & Design
- [ ] Does the change adhere to the single-responsibility principle?
- [ ] Are domain boundaries respected without cyclic dependencies between modules?
- [ ] Is there an existing utility or library that already solves this problem?

### 3.2 Security & Data Integrity
- [ ] Are all database queries parameterized? Zero raw string interpolations.
- [ ] Are authorization checks performed at the object level (BOLA / IDOR protection)?
- [ ] Are sensitive fields (passwords, tokens, PII) excluded from logs and error traces?

### 3.3 Concurrency & Distributed Systems
- [ ] Are race conditions possible in concurrent write paths?
- [ ] Are distributed locks, atomic database operations, or idempotency keys utilized where needed?
- [ ] What happens if an external network dependency (Stripe, Twilio) experiences 10-second latency? Are timeouts bounded?

### 3.4 Performance & Database
- [ ] Are database foreign keys indexed?
- [ ] Are there hidden N+1 queries in serializers or entity mappers?
- [ ] Is data fetching paginated with reasonable max bounds?

### 3.5 Testing & Verification
- [ ] Does the PR include automated tests proving the bug is fixed or feature functions?
- [ ] Are edge cases tested (empty arrays, boundary numbers, null values)?
- [ ] Are integration tests running against realistic test containers rather than excessive mocks?

---

## 4. Reviewer & Author Responsibilities and SLAs

```
   ┌─────────────────────────────────────────────────────────┐
   │                    REVIEW TIMELINE                      │
   └────────────────────────────┬────────────────────────────┘
                                │
     Author: Creates PR < 400 lines with description & test evidence
                                ▼
     CI: Automated lint, typecheck, tests, and security scans (< 5m)
                                ▼
     Reviewer SLA: First substantive review within 4 business hours
                                ▼
     Resolution: Author resolves blocking issues; Reviewer re-reviews
```

- **PR Batch Size**: Under 400 lines of diff (excluding lockfiles and generated fixtures). Large features must be broken into stacked PRs.
- **Review SLA**: First response within 4 hours during business days.
- **Approval Policy**: Minimum of 1 approved review from a code owner; zero unresolved blocking `issue` comments.

---


---


---

## 4. Concrete Code Examples: High-Impact Review Patterns

### 4.1 Flagging SQL Vulnerabilities (Blocking Issue)
```markdown
<!-- ✅ Conventional Comment Example -->
**issue (security, blocking)**: Parameter interpolation flaw detected.
Raw string concatenation in SQL queries permits injection bypass.
Use parameterized binds:
```typescript
// ❌ BAD: SQL Injection risk
const user = await db.query(`SELECT * FROM users WHERE email = '${input.email}'`);

// ✅ GOOD: Parameterized prepared statement
const user = await db.query('SELECT * FROM users WHERE email = $1', [input.email]);
```

### 4.2 Recommending O(1) Data Structures (Suggestion)
```markdown
<!-- ✅ Conventional Comment Example -->
**suggestion (performance, non-blocking)**: 
Array `.includes()` inside `.filter()` results in $O(N 	imes M)$ runtime complexity.
Constructing a `Set` before iteration reduces lookup to $O(1)$ amortized:
```typescript
// ✅ GOOD: Optimized Set lookup
const allowedIdSet = new Set(allowedIds);
return items.filter(item => allowedIdSet.has(item.id));
```

## 5. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Monolithic Mega-PRs** | Submitting > 1,000 lines of diff in a single PR | Review fatigue; bugs approved without proper inspection | Break into Stacked PRs (< 400 lines each) |
| **Subjective Style Debates** | Debating formatting or import orders in review comments | Wastes senior engineering hours; delays delivery | Automate formatting and linting via CI tools (Prettier, Ruff) |
| **Silent LGTM Approvals** | Rubber-stamping PRs without inspecting logic or tests | Production outages from uninspected edge cases | Enforce mandatory review checklists on critical paths |

## 5. Verification Checklist & Production Audit

- [ ] Automated linters and formatters pass in CI before review begins.
- [ ] All comments use Conventional Comments syntax.
- [ ] PR description includes motivation, architectural summary, and reproduction/verification steps.
- [ ] Author never merges their own PR without required peer approval.
