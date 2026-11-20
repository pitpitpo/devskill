# 🛡️ Zero-Missed-Requirements, Context Engineering & Long-Horizon Completeness (`agents/zero-missed-requirements.md`)

> **Standard Identifier**: `AGENT-ZERO-OMISSION-001`  
> **Status**: Mandatory / Non-Negotiable Core Protocol for Multi-Requirement & Complex Tasks  
> **Research Foundations**: Chroma *Context Rot* (2025), Liu et al. *Lost in the Middle*, Anthropic *Effective Context Engineering* & *Effective Harnesses for Long-Running Agents* (`feature_list.json` + Generator/Evaluator split), Manus *Context Engineering* (Attention Recitation & KV-Cache Stability), *SatisFix* Specification Satisficing & Objective-Aligned Elicitation (Nov 2026), Living Specifications (`SpecKit`/`WiseSpec`), *SWE-Gate* Hidden Review Constraints, *CliffCompaction* & *SWE-Pruner*, Weller et al. Retrieval Geometry (ICLR 2026), Automated Requirements Traceability Matrix (RTM)  
> **Governing Rules**: **R-001**, **R-004**, **R-181**, **R-248**, **R-261**, **R-262**, **R-263**, **R-264**, **R-265**, **R-266**  
> **Executable Gate**: [`scripts/req-ledger.py`](../scripts/req-ledger.py)  
> **Last Updated**: 2026-11-20

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Never trust an LLM's working memory to hold more than 3–5 requirements across a multi-step engineering task. Externalize every explicit, implicit, edge-case, and negative requirement into a frozen, proof-bound JSON ledger BEFORE writing code; recite open constraints into the recency window at every milestone; audit the final diff from a fresh read-only context; and mechanically block completion until 100% of required items pass with observed execution evidence.*

---

## 2. Empirical Root Causes: Why AI Agents Drop Requirements

Research across frontier models (Chroma *Context Rot*, Multi-IF / IFEval constraint-decay studies, Anthropic & Manus production postmortems) proves that requirement omission is **structural, not accidental**:

| Failure Mode | Mechanism | How It Manifests in Coding Tasks |
|---|---|---|
| **1. Context Rot & Attention Dilution** | Accuracy degrades continuously as token count and semantically similar distractors grow—even at 10–20% of the context limit (*Two-Job Problem*: retrieve rule + reason over it simultaneously). | By tool turn 15, early user constraints and domain rules are buried under file reads and test logs, so the model silently violates them. |
| **2. Lost in the Middle (U-Shaped Attention)** | Models attend strongly to the prompt prefix and the immediate tail, but recall drops sharply in the middle. | **Negative constraints** ("never do X", "preserve backwards compatibility", "do not modify Y") are dropped first. |
| **3. Multi-Constraint Decay (> 5–7 Rules)** | Instruction-following accuracy drops sharply as simultaneous constraints scale past ~7 items in prose. | The model satisfies the 4 most salient functional requirements and silently skips 3 secondary details and 2 edge cases. |
| **4. Premature Happy-Path Victory** | Once the main file compiles and one happy-path test turns green, the model's completion heuristic triggers early. | Error handling, empty states, permissions, migrations, and secondary requirements are left unfinished. |
| **5. Markdown Checklist Tampering** | In freeform prose or Markdown TODO lists, models subconsciously rephrase, merge, or delete inconvenient criteria. | Requirements quietly shrink to match whatever partial code the agent happened to write. |
| **6. Self-Evaluation Bias & Context Poisoning** | Grading your own diff inside the same cluttered context window causes confirmation bias; failed debug traces pollute reasoning. | Agent reports "all requirements satisfied" while leaving stubbed branches or unverified edge cases; `SWE-Gate` found 34.3% of test-passing patches still violate implicit review constraints. |
| **7. Specification Satisficing (`SatisFix`)** | Even when an agent actively considers the compliant option $a^+$, it commits to and rationalizes a non-compliant shortcut $a^\circ$. Standard self-critique fails because the agent does not classify $a^\circ$ as an error. | Agent quietly approximates an invariant, skips a tricky edge constraint, or substitutes a weaker mechanism while convincingly justifying why it is "close enough." |

---

## 3. The 6-Layer Anti-Omission Architecture

```
[Complex User Brief / Spec]
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: ATOMIC DECOMPOSITION & FROZEN JSON LEDGER (R-261)               │
│ Extract EVERY explicit, implicit, edge-case & NEGATIVE ("MUST NOT")      │
│ requirement into `.devskill/requirements.json` (`passes: false`).        │
│ Run `req-ledger.py freeze` -> locks canonical SHA-256 `spec_hash`.       │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: SINGLE-SLICE INCREMENTAL EXECUTION (R-262)                      │
│ Implement ONE cohesive requirement (or small tightly-coupled slice) at   │
│ a time. Never attempt to one-shot 15 requirements in a single pass.      │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: ATTENTION RECITATION & CONTEXT HYGIENE (R-263)                  │
│ Every milestone (5–8 tool calls), run `req-ledger.py recite` to pull     │
│ open NEGATIVE constraints + next `REQ-*` into the recency window.        │
│ Offload giant logs to disk; delegate research to isolated subagents.     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: PROOF-BOUND DEFAULT-FAIL TRANSITIONS (R-264)                    │
│ Flip `passes: true` ONLY via `req-ledger.py verify` with concrete        │
│ files changed, exact command, `exit_code == 0`, and observed output.     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: FRESH-CONTEXT READ-ONLY EVALUATOR AUDIT (R-265)                 │
│ Independent critic (fresh context, zero write tools) compares every      │
│ `REQ-001..REQ-NNN` against `git diff` + test logs (Spec before Quality). │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: MECHANICAL FAIL-CLOSED COMPLETION GATE (`req-ledger.py gate`)   │
│ Exits 0 ONLY if `spec_hash` is intact AND 100% of required items have    │
│ `passes == true` + non-empty evidence. Wired into Stop / CI hooks.       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Operational Protocol: Using `scripts/req-ledger.py`

Whenever a task contains **≥ 4 distinct requirements**, spans **multiple files/subsystems**, or contains **strict negative constraints** ("do not touch X", "must preserve Y"), execute this workflow before editing code:

### Step 1 — Extract & Freeze the Atomic Requirement Contract
Classify every requirement into one of four explicit types so edge cases and negative rules can never hide inside vague paragraphs:
- `functional`: Core user-facing or API behavior required.
- `negative`: Explicit prohibitions ("MUST NOT break X", "never store Y in localStorage", "do not add web server"). **Always highlighted first during recitation.**
- `edge_case`: Boundary inputs, empty states, concurrency races, failure/retry paths, null/Unicode/overflow handling.
- `non_functional`: Performance budgets, security/AuthZ/tenant isolation, WCAG 2.2 AA accessibility, migrations, backward compatibility.

```bash
# 1. Initialize ledger
python3 scripts/req-ledger.py init .devskill/requirements.json --title "Billing Webhook Idempotency & Refunds"

# 2. Add atomic requirements (every item starts with passes: false)
python3 scripts/req-ledger.py add .devskill/requirements.json \
  --id REQ-001 --category api --type functional \
  --description "Verify Stripe HMAC-SHA256 webhook signature on raw request body" \
  --criteria "Invalid or missing Stripe-Signature header returns HTTP 400 and performs zero DB writes"

python3 scripts/req-ledger.py add .devskill/requirements.json \
  --id REQ-002 --category security --type negative --protected \
  --description "MUST NOT log raw webhook payloads containing customer PII or secret headers" \
  --criteria "Log scan on webhook test run shows zero email/card/signature substrings"

python3 scripts/req-ledger.py add .devskill/requirements.json \
  --id REQ-003 --category reliability --type edge_case \
  --description "Duplicate webhook delivery with identical event.id is idempotent" \
  --criteria "Second POST with same event.id returns 200 OK without creating duplicate ledger rows"

# 3. Freeze spec (computes tamper-evident SHA-256 spec_hash)
python3 scripts/req-ledger.py freeze .devskill/requirements.json
```

> **Living Spec & Protected Blocks**: In Git-versioned specification files (`spec.md` / `plan.md`), wrap non-negotiable security, compliance, and scope exclusions (`DO NOT MODIFY` paths) inside `<!-- BEGIN USER-SPECIFIED --> ... <!-- END USER-SPECIFIED -->` fences and mark corresponding ledger items with `--protected`. Never allow autonomous refinement loops to overwrite protected blocks.  
> **Anti-Tamper Rule**: Once frozen, editing or deleting a requirement invalidates `spec_hash` and causes `req-ledger.py gate` to fail closed. If the human explicitly changes scope mid-task, use `--amend --reason "<user directive>"` so every scope change is explicitly audited.

### Step 2 — Recite Before Every Milestone (Defeating Lost-in-the-Middle)
```bash
python3 scripts/req-ledger.py recite .devskill/requirements.json
```
This outputs a tiny (< 30 lines), ultra-high-signal block placed directly at the tail of the agent's context window:
1. Progress bar (`1/8 required verified`).
2. **ALL open `negative` constraints** (pinned at top so prohibitions are never forgotten).
3. The **next open requirement** with its exact acceptance criteria.

### Step 3 — Bind Concrete Execution Proof (Default-FAIL Contract)
```bash
python3 scripts/req-ledger.py verify .devskill/requirements.json \
  --id REQ-001 \
  --files "src/webhooks/stripe.ts,tests/webhooks/stripe.test.ts" \
  --command "npx vitest run tests/webhooks/stripe.test.ts" \
  --exit-code 0 \
  --evidence "4/4 tests passed: valid signature accepted (200), tampered/missing rejected (400), 0 DB inserts"
```
If `--exit-code` is non-zero or `--evidence` is empty, `req-ledger.py` rejects the transition fail-closed.

### Step 4 — Objective-Aligned Deviation Elicitation, Fresh-Context Audit & Mechanical Gate
Before claiming completion:
1. **Defeat Specification Satisficing (`R-266`, `SatisFix`)**: Generate the structured audit prompt (`python3 scripts/req-ledger.py audit-prompt .devskill/requirements.json`) and execute non-judgmental **Objective-Aligned Deviation Elicitation**: explicitly enumerate every place the implementation handled any requirement differently, simplified an edge case, or took a shortcut compared to the frozen spec—then remediate every unapproved deviation before proceeding.
2. **Fresh-Context Read-Only Evaluator Pass (`R-248`, `R-265`)**: Run an independent read-only Critic/Evaluator pass (clean context window, zero write tools) fed ONLY: (a) `.devskill/requirements.json`, (b) `git diff`, and (c) real test outputs. Verify **every single `REQ-*`** against actual code lines—not the generator's claims—and check implicit review constraints (`SWE-Gate`).
3. **Execute the Mechanical Completion Gate (`R-264`)**:
```bash
python3 scripts/req-ledger.py gate .devskill/requirements.json --require-frozen
```
- **Exit Code `0`**: Spec hash verified intact, 100% of required `REQ-*` items have `passes: true` + non-empty evidence + `exit_code == 0`, and full Requirement Traceability Matrix (RTM) summary printed.
- **Exit Code `1`**: Prints every missing, unverified, or tampered requirement — **agent MUST NOT stop or claim completion**.

---

## 5. Context Engineering Hygiene (Preventing Context Rot & Skill Overload)

Even DevSkill's own 270+ rules can induce Context Rot if loaded indiscriminately! Enforce strict context hygiene grounded in late-2026 empirical findings:

1. **Progressive Disclosure Budget (Max 3–5 Guides) & Retrieval-Based Spec Ingestion**: Consult [`ROUTING.md`](../ROUTING.md) and load ONLY the 3–5 files for your active archetype plus `.devskill/requirements.json`. For large specs, retrieve targeted sections on demand instead of monolithic prompt stuffing; avoid dense vector-store RAG over source code (Weller et al. sphere-packing recall limits)—prefer live `ripgrep`/AST/LSP queries.
2. **Static Prefix / Append-Only History & Deferred Schemas**: Keep system prompts and tool definitions static across turns for KV-cache stability, and use deferred on-demand tool-schema loading where supported (−40% startup context overhead).
3. **Structural Compaction & File System as Unbounded Memory**: Redirect verbose logs (> 150 lines of test output, build traces, or API dumps) to temporary files (e.g., `/tmp/test.log`) and inspect targeted excerpts (`tail`, `grep`). Apply goal-aware line pruning (`SWE-Pruner`) and structural compaction (`CliffCompaction`, keeping working context tight at 16K–45K tokens rather than letting stale observations rot a 200K–1M window).
4. **Subagent Isolation for Noisy Exploration**: Delegate broad codebase searches, log forensics, or interactive debugging (`Debug2Fix`) to read-only isolated subagents with fresh context windows that return compact structured digests (exact file paths, line numbers, verified facts).
5. **Keep Errors in Trace, Strip Failed Edits**: Leave tool error messages in conversation history so the model avoids repeating failed paths (Manus principle), but strip 100% of abandoned speculative code edits from `git diff` (`R-246`).
6. **Clean Session Handoff (Zero Amnesia Across Compaction)**: For multi-session tasks, update `.devskill/requirements.json` + commit verified slices atomically before pausing so the next session runs `git log -n 5` + `req-ledger.py recite` and resumes cleanly with zero lost context.

---

## 6. Anti-Patterns & Remediations

| Anti-Pattern | Failure Mechanism | Remediated Standard |
|---|---|---|
| **Holding 12 requirements in head / chat prose** | Multi-constraint decay silently drops items #5–#9 | Externalize every requirement into `.devskill/requirements.json` and `freeze` |
| **Editing or deleting tough requirements mid-task** | Checklist tampering masks incomplete delivery | Immutable `spec_hash` detected automatically by `req-ledger.py gate` |
| **Dumping 2,000-line test logs into context** | Context rot buries negative constraints | Save raw log to file; inspect only failing lines + summary |
| **Marking done after happy-path passes** | Premature completion / self-evaluation bias | Explicit `edge_case` + `negative` REQ entries + fresh-context read-only audit + `req-ledger.py gate` |
| **Loading 20 DevSkill docs "just in case"** | Instruction overload / distractor interference | Strict `ROUTING.md` progressive disclosure (3–5 files max) |

---

## 7. Verification Checklist

- [ ] Every explicit, implicit, edge-case, and negative ("MUST NOT") requirement is recorded in `.devskill/requirements.json` with a unique `REQ-NNN` ID.
- [ ] Specification frozen (`req-ledger.py freeze`) before implementation begins; any scope change recorded via audited `--amend`.
- [ ] `req-ledger.py recite` executed at milestone boundaries so open negative constraints stay in active attention.
- [ ] Every requirement verified with exact files, command, `exit_code == 0`, and observed output (`req-ledger.py verify`).
- [ ] Objective-aligned deviation elicitation (`req-ledger.py audit-prompt`) executed to catch rationalized shortcuts (`SatisFix`, `R-266`).
- [ ] Independent read-only diff-vs-ledger audit performed (Spec Compliance before Code Quality, `R-248`, `R-265`).
- [ ] `python3 scripts/req-ledger.py gate .devskill/requirements.json --require-frozen` exits with **Exit Code `0`**.

---

*See also*: [`agents/agentic-sdlc-harness-architecture.md`](agentic-sdlc-harness-architecture.md), [`agents/unified-agent-stacks.md`](unified-agent-stacks.md), [`agents/code-forensics-interrogation.md`](code-forensics-interrogation.md), [`scripts/req-ledger.py`](../scripts/req-ledger.py), and [`scaffolding/configs/.claude-settings.json`](../scaffolding/configs/.claude-settings.json) (`Stop` hook enforcement).
