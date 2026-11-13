# 🌿 Git Branching & Pull Request Standards (`git-branching-pr.md`)

> **Classification**: Source Control & Collaboration Workflow  
> **Core Strategy**: Trunk-Based Development with Short-Lived Feature Branches

---

## 1. Trunk-Based Development (TBD)

```
main (Production / Continuous Deploy) ───────────────────────────────────►
        \                                             / (Squash & Merge)
         \─── feat/auth-login (Lifespan < 24-48h) ───/
```

- **Short-Lived Branches**: Branches should live less than 48 hours. Long-lived feature branches cause massive merge conflicts and integration pain.
- **Feature Flags for Incomplete Features**: Never hold a branch open for 3 weeks waiting for a feature to be finished. Merge behind a feature flag into `main`.

---

## 2. Conventional Commits Standard

Commit messages must follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types:
- `feat`: A new feature for the user or system
- `fix`: A bug fix
- `perf`: A code change that improves performance
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `docs`: Documentation changes only
- `chore`: Updating dependencies, build tools, or linters
- `ci`: Changes to CI/CD configuration files and scripts

### Example:
```
feat(auth): implement argon2id password hashing

Replaced legacy bcrypt implementation with Argon2id to meet OWASP 2026 guidelines.
Configured memory cost to 64MB and parallelism to 4.

Closes #142
```

---

## 3. Pull Request Template

Every PR description must contain:
1. **Summary**: What does this PR do and why?
2. **Changes Made**: Bulleted list of key code changes.
3. **Testing Performed**: How was this verified? (Unit test output, manual steps).
4. **Security Checklist**:
   - [ ] No secrets or API keys committed
   - [ ] Inputs validated at boundaries
   - [ ] Unit & integration tests pass in CI
