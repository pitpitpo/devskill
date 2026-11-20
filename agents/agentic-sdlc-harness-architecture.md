# 🏗️ Production Agentic SDLC Architecture, Harness Engineering & Zero-Trust Runtime Governance (`agents/agentic-sdlc-harness-architecture.md`)

> **Standard Identifier**: `AGENT-HARNESS-ARCH-001`  
> **Status**: Mandatory / Non-Negotiable Production Systems Architecture  
> **Empirical Foundations**: POMDP & Factored Scope Control (`FactorSmith`, `Agent-BRACE`), Harness Source Audits (`Agent = Model + Harness`, 11 production harnesses), Retrieval Geometry Bounds (Weller et al., ICLR 2026), Deterministic Control Planes (`Rel(AI)Build`, `Claim Plane`), Multi-Agent Failure Taxonomy (`MAST`, NeurIPS 2025), Regression Debt (`SWE-Maintain`), Neuro-Symbolic Verification (`ACH`, `PBT-Bench`, `Debug2Fix`, `AutoVerus`/`KVerus`, `SWE-Gate`, `BaxBench`), Transactional SRE (`STRATUS`), Zero-Trust Isolation (`Firecracker`, `Kata v4.3+`, `srt`, `SPIFFE`/`WIMSE`, `OWASP ASI01–ASI10`), Token FinOps & Skill Preservation (Shen & Tamkin)  
> **Governing Rules**: **R-228**, **R-229**, **R-261**–**R-272**  
> **Last Updated**: 2026-11-20

---

## 1. Core Architectural Thesis

> **Axiom (`Rel(AI)Build`)**: *A non-deterministic LLM component CANNOT serve as a trustworthy control for another non-deterministic component.*

Empirical production telemetry exposes a severe divergence between raw coding-agent commit velocity (+240% commits) and actual shipped software releases (+30%, AI–human elasticity of substitution = 0.23), driven by bottlenecks in scoping, review, security, and unverified regression leakage. Converting abundant agent-authored patches into reliable production software requires **engineering the surrounding control plane, code intelligence, and verification oracles** (`Agent = Model + Harness`), not deploying unconstrained multi-agent autonomy.

---

## 2. The Five-Layer Production Architecture

Confine probabilistic LLM reasoning strictly to **Layer 3**, while enforcing every authorization, scope, budget, isolation, and verification invariant deterministically in **Layers 1, 2, 4, and 5**:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: LIVING SPECIFICATIONS & REQUIREMENT LEDGER (Git-Versioned)          │
│ Bidirectional Spec -> Plan -> Tasks -> Code -> Spec; protected               │
│ `<!-- BEGIN USER-SPECIFIED -->` blocks; explicit `DO NOT MODIFY` exclusions; │
│ frozen SHA-256 JSON ledger (`scripts/req-ledger.py`).                        │
├──────────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: DETERMINISTIC NON-LLM CONTROL PLANE (R-267)                         │
│ Phase-state machine, HMAC-stamped lockfiles, command/path blocklists,        │
│ static pre-write scope locks (`Claim Plane` / Git worktrees), turn & token   │
│ ceilings, CI retry caps (1-2 loops max), append-only hashed audit logs.      │
├──────────────────────────────────────────────────────────────────────────────┤
│ LAYER 3: BOUNDED AGENT HARNESS (`Agent = Model + Harness`)                   │
│ Hand-written native async execution loop (no heavy framework wrappers);      │
│ deferred tool-schema loading; structural compaction (`CliffCompaction`,      │
│ `SWE-Pruner`); model portfolio routing (workhorse vs. frontier).             │
├──────────────────────────────────────────────────────────────────────────────┤
│ LAYER 4: GROUNDED CODE INTELLIGENCE & ACI (R-268)                            │
│ Live lexical search (`ripgrep`/`glob`), Tree-sitter AST/PageRank maps,       │
│ compiler-grade LSP diagnostics/references, MCP Policy Gateway (OAuth 2.1 +   │
│ RFC 8707), exact `str_replace` / AST-aware edits (never bare unified diffs). │
├──────────────────────────────────────────────────────────────────────────────┤
│ LAYER 5: ZERO-TRUST ISOLATION & NEURO-SYMBOLIC ORACLES (R-269, R-270)        │
│ OS sandbox locally (`srt`/Seatbelt/bubblewrap+Landlock) & hardware microVMs  │
│ (`Firecracker`/`Kata v4.3+`) in cloud; host-proxy secret injection;          │
│ 100% pass-to-pass regression preservation + Mutation/PBT/SAST/Formal proofs. │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Formal POMDP Dynamics, Harness Subsystems & Retrieval Geometry

### 3.1 Goal-Conditioned Factored POMDP
Repository-scale engineering is a sequential decision problem under partial observability:
$$\mathcal{M} = \langle \mathcal{G}, \mathcal{S}, \mathcal{A}, \mathcal{O}, T, \Omega, R, \gamma \rangle$$
Two control-theory consequences dictate harness design:
1. **Belief-State Sufficiency**: Raw multi-turn terminal logs poison the implicit belief state (*Context Rot*). Maintain an explicit externalized state (frozen requirement ledger + structured compaction via goal-aware line pruning `SWE-Pruner` or aggressive `CliffCompaction` at 16K–45K budgets rather than relying solely on 200K–1M raw histories).
2. **Factored Dependency Scopes**: Exploit localized dependency scopes $Z_i$ (`FactorSmith`) to bound context reads, isolate modular tasks, and enforce disjoint file-scope write locks.

### 3.2 Seven Canonical Harness Subsystems & The "Twin Absence"
Production harness audits across 11 flagship coding harnesses confirm two universal patterns (**The Twin Absence**):
1. **Zero General Agent Frameworks**: All 11 production harnesses hand-write their async execution loop directly on native primitives (no LangChain/AutoGen overhead).
2. **Zero Static Vector-Store RAG Over Source Code**: Weller et al. (ICLR 2026) proved via high-dimensional sphere-packing bounds that retrieving arbitrary top-$k$ file subsets from an $n$-file repository requires embedding dimension:
   $$d = \Omega\left(\frac{k \log(en/k)}{\log(1 + 1/\gamma)}\right)$$
   Fixed-dimension dense embeddings fail recall as monorepos scale and go stale on every edit.

**Prescribed 4-Modality Code Intelligence Stack**:
1. **Live Lexical Search**: `ripgrep` / `glob` + targeted reads (offloaded to read-only exploration subagents).
2. **AST Symbol & Dependency Graphs**: Tree-sitter symbol maps + Personalized PageRank / heterogeneous caller graphs.
3. **Compiler-Grade LSP Grounding**: `go-to-definition`, `find-all-references`, and live compiler/type diagnostics via LSP/MCP.
4. **Adaptive Edit Primitives**: Prefer exact verbatim `str_replace`, Tree-sitter AST block/function edits (`BlockDiff`/`FuncDiff`), IDE refactoring APIs (`CoRenameAgent`), or hash-anchored lines—never rely on raw LLM-counted unified diff line headers (`@@ -a,b +c,d @@`).

---

## 4. Orchestration Topologies & Multi-Agent Failure Prevention (MAST)

Empirical trace audits (`MAST`, 1,600+ traces) show >75% of multi-agent failures stem from specification/design defects (41.8%–44.2%) and inter-agent misalignment (32.4%–36.9%), while uncoordinated swarms amplify errors **17.2×** (vs. **4.4×** centralized), sequential chains > 4 handoffs routinely fail, and tasks where a single agent already exceeds 45% accuracy suffer negative returns from adding peer agents.

### 4.1 Default Topology: Deterministic Blueprint + Single Agent
Model enterprise factories (Stripe Minions, Spotify Honk, Google Kythe+Gemini) by wrapping strictly bounded LLM nodes inside deterministic non-LLM state machines:
- Pre-populate deterministic context (static reference graphs, mapping tables, explicit `DO NOT MIGRATE` / `DO NOT MODIFY` exclusions).
- Restrict active tool surface to the minimum required slice (deferred schema loading cuts startup prompt ~40%).
- Run sub-second local linters/formatters deterministically before invoking remote CI; cap CI retry loops at **1–2 iterations** before escalating.

### 4.2 The Only 4 Multi-Agent Topologies Permitted in Production (`R-268`)
| Permitted Topology | Architectural Pattern | Write Concurrency Rule |
|---|---|---|
| **1. Read-Parallel, Single-Writer** | Central orchestrator spawns read-only subagents for search, log forensics, or test synthesis in isolated contexts. | **Single writer** in primary session; zero concurrent filesystem writers. |
| **2. Tool-Complexity Encapsulation** | Dedicated subagent wraps noisy stateful tooling (e.g., `Debug2Fix` `pdb`/DAP interactive debugging) behind concise Q&A. | Subagent executes read-only/ephemeral inspection; returns concise diagnosis. |
| **3. Artifact-Mediated Deliberation** | Specialized reviewers exchange formal artifacts (Kruchten 4+1 views, ATAM mismatch reports, frozen `requirements.json` audits) instead of unstructured chat. | Read-only evaluator contexts (`R-265`). |
| **4. Worktree / Static Claim-Plane Parallelism** | Independent tracks execute in isolated Git worktrees OR under a **Static Pre-Write Claim Plane** that fails closed on any undeclared file edit. | Disjoint static file scopes declared upfront (never dynamic mid-flight scope negotiation). |

---

## 5. The 5-Tier Neuro-Symbolic Verification Stack (`R-269`)

Controlled sequential-maintenance evidence (`SWE-Maintain`) proves that **downstream technical debt in agent-edited code is caused by unverified regression leakage**: whenever inherited agent edits pass 100% of prior regression tests, the downstream maintenance penalty disappears completely. Conversely, **20.3%–49.9%** of functionally correct generated backends retain exploitable security flaws (`BaxBench`), **34.3%** of test-passing patches violate implicit review constraints (`SWE-Gate`), and naive coverage-only LLM tests average ~40% mutation scores.

Layer verification deterministically:
1. **Strict Pass-to-Pass Regression Gate**: Require 100% of pre-existing tests + strict static types (`tsc --noEmit`, `mypy --strict`, `cargo check`) to pass with zero weakened assertions (`R-011`).
2. **Mutation-Guided Test Hardening (`ACH`)**: Generate domain/compliance mutants, filter equivalent mutants, and synthesize tests strictly required to kill surviving mutants—never accept coverage-only tests that merely assert buggy implementation behavior.
3. **Property-Based Testing (`Hypothesis` / `fast-check`)**: Encode roundtrip, invariant, boundary, and state-machine properties to catch semantic bugs missed by example-based tests (+6.7 to +24.5 pp recall).
4. **Hybrid Deterministic SAST + LLM Self-Proving Security Review**: Pair `CodeQL` / `Semgrep` taint/data-flow rules with LLM business-logic inspection that must prove exploitability (PoC) to suppress false positives; target AI-prevalent CWEs (`CWE-918` SSRF, `CWE-215` debug leaks, `CWE-502` deserialization, `CWE-79` XSS, `CWE-89` SQLi, `CWE-798` secrets, `CWE-78` CMDi, `CWE-22` path traversal).
5. **Formal Verification ("Vericoding") for Critical Kernels & Ledgers**: Use Verus, Dafny, TLA+, or Lean for memory-safety, concurrency, and accounting invariants, ALWAYS paired with deterministic proof-bypass checks forbidding `sorry`, `admit`, `axiom`, `assume()`, `unsafe`, `@[extern]`, and vacuous postconditions.

---

## 6. Autonomous SRE & Live Operations Safety Ceiling (`R-271`)

Because frontier operational benchmarks show peak RCA ceilings of **25.3%–56.2%** (`ORCA-bench` / `ITBench-AA`), **39.5%–62.0%** invalid recovery actions after correct diagnosis (`R2Act`), and **17.9%** safe DB repair vs. **93.4%** for human DBAs (`DBA-Bench`):
1. **Default Read-Only Mode**: Restrict AI SRE agents to read-only telemetry queries (`Obs-MCP` for PromQL/LogQL/traces) and human-approved runbooks.
2. **Transactional No-Regression (`TNR` / `STRATUS`)**: Any automated production write action MUST pair with an explicit deterministic undo operator (converting destructive deletions into recoverable backups/rollbacks) and pass **dual LLM-free Outcome + Safety health oracles** under live traffic before closing an incident.

---

## 7. Zero-Trust Compute Isolation, Supply-Chain & Identity Stack (`R-270`)

Model safety training alone leaves 22.9%–81% exploit rates under indirect prompt injection and MCP tool poisoning (`MCPTox`, `mcpvenom`). Move containment into deterministic infrastructure:

| Environment | Mandatory Isolation Tier | Mandatory Controls |
|---|---|---|
| **Local Workstation** | **OS Process Sandbox** (`srt`: macOS Seatbelt / Linux `bubblewrap` + network namespace + `seccomp`/`Landlock`) | Filesystem write jail to workspace; default-deny egress routed through host-side domain allowlist proxy; Git/API credentials stay outside sandbox. |
| **Unattended Cloud / Untrusted Code** | **Hardware-Virtualized MicroVM** (`Firecracker` or `Kata Containers v4.3+` Rust runtime) | Dedicated guest kernel; zero standing secrets in VM memory; host-side credential-injecting egress proxy blocking `169.254.0.0/16` metadata; memory snapshot-restore for branching. |
| **Protocol & MCP Boundary** | **MCP Policy Gateway** (OAuth 2.1 + PKCE + RFC 8707 `resource`/`aud`, zero token passthrough) | Cryptographically pinned tool manifests (anti-rug-pull); automated metadata poisoning scan; explicit Cedar/OPA policy-as-code per tool call. |
| **Workload Identity & Provenance** | **Non-Human Workload Identity** (`SPIFFE`/`SPIRE` SVIDs + IETF `WIMSE` + `SLSA v1.2` + `Sigstore`) | Short-lived attested credentials (no shared human PATs); OpenTelemetry parent–child span lineage for every tool invocation. |
| **Software Supply Chain & Rule Files** | **Private Registry Proxy + Governance Review** | Disable package install scripts by default + verify registry provenance (anti-slopsquatting & `HalluSquatting`); subject `.mcp.json`, `AGENTS.md`, `CLAUDE.md`, and `SKILL.md` diffs to mandatory peer security review equal to CI/CD pipeline code. |

---

## 8. Token Portfolio FinOps, Compliance & Human Skill Preservation (`R-272`)

### 8.1 Token Portfolio FinOps (Countering Jevons Paradox)
- **Tiered Model Portfolio Routing**: Route ~80% of scoped edits, lint fixes, and triage to fast or open-weight models; reserve frontier reasoning models for architecture, security audits, and cross-file planning (3×–5× OpEx reduction).
- **Harness Token Hygiene**: Enable prompt-prefix caching, deferred tool-schema loading (−40% startup prompt), structural compaction (`CliffCompaction`/`SWE-Pruner`), and intermediate trajectory reuse (`SWE-Replay`) rather than restarting search from scratch.
- **Outcome Metric**: Measure **unit cost per verified, merged feature/PR** and **deployment rework rate**—never raw token volume or commit count.

### 8.2 Regulatory & IP Traceability via Living Specs
- **EU AI Act (Art. 11/12/14/50) & NIST CAISI / Cyber AI Profile**: Maintain an inventory of active agents classified by action risk; version Living Specs in Git (technical documentation), persist structured append-only agent event logs, and enforce deterministic human halt/override gates.
- **Software IP & Authorship Hygiene (USCO Guidance)**: Purely prompt-generated code lacks copyright protection; preserve demonstrable human architectural authorship, module selection/arrangement, substantive review/rewrites, and Git attribution under commercial zero-data-retention API agreements.

### 8.3 Human Debugging Mastery (Countering Skill Atrophy)
Controlled RCT evidence (Shen & Tamkin) documents a **17 percentage-point comprehension and debugging drop** under blind AI delegation. Countermeasures:
1. **Human Merge Explainability Gate**: Any engineer approving an agent-authored PR MUST be able to explain its failure modes and debug it without the agent present.
2. **Comprehension-Preserving Modes**: Use *Conceptual Inquiry*, *Hybrid Code-Explanation*, and *Generation-Then-Comprehension* during onboarding and unfamiliar subsystem work; rotate engineers through agent-heavy services during operational game days.

---

## 9. Production Readiness Verification Checklist

- [ ] Living spec and frozen requirement ledger committed (`scripts/req-ledger.py freeze`) with explicit `DO NOT MODIFY` boundaries and protected user-specified blocks.
- [ ] Deterministic control plane enforces phase gates, turn/token limits, static pre-write scope locks (`Claim Plane` / worktrees), and 1–2 CI retry cap.
- [ ] Single-agent loop grounded in live lexical/AST/LSP search and exact `str_replace`/AST edits; subagents limited to read-parallel or isolated scopes.
- [ ] 100% pass-to-pass regression preservation verified alongside mutation/PBT tests and hybrid SAST + security review.
- [ ] Execution isolated in OS sandbox (local) or Firecracker/Kata v4.3+ microVM (cloud) with host-proxy secret injection and peer-reviewed `.mcp.json` / `AGENTS.md` / `SKILL.md`.
- [ ] Live SRE agents restricted to read-only telemetry + Transactional No-Regression undo gates.
- [ ] Token portfolio routing active and human merge explainability verified.

---

*See also*: [`agents/zero-missed-requirements.md`](zero-missed-requirements.md), [`agents/mcp-a2a-protocols.md`](mcp-a2a-protocols.md), [`agents/unified-agent-stacks.md`](unified-agent-stacks.md), [`security.md`](../security.md), and [`scripts/req-ledger.py`](../scripts/req-ledger.py).
