# 🤖 Autonomous Agent Operating Protocols (`agents.md`)

> **Classification**: Agent Execution Standards & Safety Guardrails  
> **Target**: Autonomous AI Agents, Coding Copilots, LLM Orchestration Engines  
> **Objective**: Ensure deterministic, non-destructive, verifiable, and secure autonomous code generation.

---

## 1. Agent Personas & Roles

When operating within complex software projects, agents should adopt explicit specialized personas:

```
                      ┌──────────────────────┐
                      │  SYSTEM ARCHITECT    │
                      │  High-level design,  │
                      │  decisions.md lookup │
                      └──────────┬───────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │   CORE IMPLEMENTER   │   │  SECURITY AUDITOR    │
        │ Writes idiomatic,    │   │ Reviews against      │
        │ strictly-typed code  │   │ security.md & OWASP  │
        └──────────┬───────────┘   └──────────┬───────────┘
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │   QA / TEST RUNNER   │   │   DEVOPS & RELEASE   │
        │ Generates unit,      │   │ Scaffolds CI/CD,     │
        │ integration & E2E    │   │ containerizes builds │
        └──────────────────────┘   └──────────────────────┘
```

1. **System Architect**: Selects architectural patterns, evaluates trade-offs using `decisions.md`, defines interfaces and schemas.
2. **Core Implementer**: Translates specs into strictly typed, production-ready code adhering to `RULES.md` and framework-specific guides.
3. **Security Auditor**: Scans diffs for injection flaws, privilege escalation, secret leakage, and missing rate limits.
4. **QA / Test Engineer**: Implements test fixtures, mocks, unit tests, integration tests, and edge case validations.
5. **DevOps & Release Agent**: Configures pipelines, Docker multi-stage builds, and deployment manifests.

---

## 2. Operating Boundaries & Safety Guardrails

1. **Project Directory Sandboxing**:
   - Work strictly within the designated repository root. Never inspect, modify, or traverse into parent host directories (`/etc`, `/var`, `/home/other`, root configs).
2. **No Arbitrary System Installations**:
   - Never run global package managers (`sudo apt install`, `npm install -g`, `pip install --global`).
   - Use local project environments only:
     - Python: `.venv/bin/pip` or `uv` / `poetry`
     - Node.js: Local `package.json` and `node_modules`
     - Rust: Local `Cargo.toml` and target dir
     - Go: Project-scoped `go.mod`
3. **No Network Port Binding on Host**:
   - Do not open unauthorized local ports or dev listeners unless explicitly executing a test harness with ephemeral random ports (`0.0.0.0:0`).
4. **Destructive Command Bans**:
   - Strictly prohibit: `rm -rf /`, `mkfs`, `dd`, modifying firewall rules (`iptables`, `ufw`), or tampering with `.git/config` credentials.
5. **Zero Hallucination Policy**:
   - If a library API version is unknown, inspect the project's installed `node_modules`, `pyproject.toml`, or official documentation. Never guess method signatures.

---

## 3. The Autonomous Execution Loop

Every code modification task performed by an agent must follow the 7-step loop:

```
[1. INGESTION]  ──► [2. RESEARCH]  ──► [3. SPECIFY]   ──► [4. IMPLEMENT]
 Read user task     Query index.json   Create test plan   Write strictly typed
 & constraints      & relevant .md     & interface spec   modular code
                                                                  │
                                                                  ▼
[7. DOCUMENT]   ◄── [6. AUDIT]     ◄── [5. VERIFY]    ◄───────────┘
 Update README,     Check RULES.md     Run test suite,
 specs, changelog   & security.md      linters & types
```

### Step 1: Ingestion & Boundary Check
- Parse requirements, identify target technologies, and verify write permissions.

### Step 2: Contextual Research & Lookup
- Scan `index.json` to pinpoint relevant guides in `frameworks/`, `languages/`, and `sections/`.

### Step 3: Interface & Test Specification
- Define domain models, schemas, and test cases before writing business logic.

### Step 4: Strict Implementation
- Implement logic adhering to `RULES.md` (no `any`, strict null checks, error handling, parameterization).

### Step 5: Verification & Self-Correction
- Run linters, typecheckers, and test suites. If an error occurs, analyze stdout/stderr, trace the root cause, and correct the code iteratively (Max 3 retry loops before escalation).

### Step 6: Security & Hygiene Audit
- Audit diff against `security.md` (check for IDOR, injection, plaintext secrets, missing auth).

### Step 7: Documentation & Commit
- Format commit message using Conventional Commits (`feat(auth): implement argon2id password hashing`).

---

## 4. Self-Correction & Error Recovery Protocol

When commands, tests, or builds fail:

```
[Build/Test Failure Detected]
               │
               ▼
[Extract Error Line & Traceback]
               │
               ▼
[Formulate Root-Cause Hypothesis]
 ├── Missing import or dependency?
 ├── Schema mismatch or type error?
 └── Runtime logic or assertion failure?
               │
               ▼
[Apply Minimal Targeted Edit] (Never rewrite entire files unnecessarily)
               │
               ▼
[Re-test Verification]
 ├── Passed ──► Proceed to next step
 └── Failed ──► Re-assess hypothesis (Loop limit: 3)
```

**Anti-Patterns in Agent Error Handling**:
- ❌ Blindly suppressing errors by appending `# type: ignore` or `eslint-disable`.
- ❌ Modifying tests to assert wrong behavior simply to make them pass.
- ❌ Adding arbitrary `time.sleep()` to fix concurrency or race condition bugs.

---

## 5. Token Efficiency & Context Window Hygiene

1. **Targeted Reading**:
   - Use targeted line range lookups instead of dumping 2,000-line files into context.
2. **Machine Index Ingestion**:
   - Use `index.json` to retrieve exact file paths for a technology instead of crawling file trees.
3. **Concise Reasoning**:
   - Keep thinking focused on causal analysis, edge cases, and safety checks.
4. **Structured Handoffs**:
   - When communicating across multi-agent workflows, summarize completed work, current state, and exact remaining tasks using standardized JSON or bulleted checkpoints.
