# 👁️ Code Review Standards & Rubric (`code-review-standards.md`)

> **Classification**: Engineering Quality & Peer Review Standard  
> **Target**: Senior Engineers, Staff Architects, Automated Code Review Agents

---

## 1. The Review Rubric

Reviewers must prioritize evaluation in the following order:

```
1. CORRECTNESS & LOGIC   ──► Does it solve the business problem? Edge cases handled?
2. SECURITY & PERM.     ──► Any OWASP flaws, IDOR, SQLi, secret leaks, missing auth?
3. ARCHITECTURAL FIT    ──► Does it violate RULES.md or layer boundaries?
4. PERFORMANCE & DATA   ──► Are queries indexed? N+1 queries prevented? Memory leaks?
5. MAINTAINABILITY      ──► Readable naming, test coverage, self-documenting?
6. STYLE & FORMATTING   ──► DELEGATED TO CI LINTERS (Humans never argue formatting)
```

---

## 2. Standardized Comment Prefixes

Reviewers must prefix comments to clarify whether an item is blocking or informational:

| Prefix | Meaning | Action Required by Author |
|---|---|---|
| `[BLOCKER]` | Critical bug, security risk, architectural violation | Must resolve before merge |
| `[SUGGESTION]`| Better alternative, cleaner pattern | Consider; author can explain or adopt |
| `[QUESTION]` | Inquiring about design rationale | Provide explanation |
| `[NIT]` | Trivial polish (naming, typo in comment) | Optional; does not block merge |

### Example:
> `[BLOCKER]` This SQL query uses string concatenation for `search_term`. Please replace with parameterized `$1` placeholder to prevent SQL injection.
