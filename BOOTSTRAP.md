# ⚡ Agent Intro Point: URL-Only Bootstrap Protocol (`BOOTSTRAP.md`)

> **STOP & READ FIRST — FOR ANY AI AGENT GIVEN ONLY THIS SKILL'S URL**  
> If a user provided you **only a URL** to this repository (e.g., `https://github.com/<owner>/<repo>` or a direct link to `README.md`, `SKILL.md`, `AGENTS.md`, or `BOOTSTRAP.md`) and asked you to follow it, execute this exact bootstrap protocol **before** planning or writing code.

---

## 1. Choose Your Access Mode

### Mode A — You Have Shell / Git Access *(Claude Code, Codex CLI, Gemini CLI, Cursor, Devin)*
Clone a shallow, read-only local copy **outside** the user's project tree so you can read guides and execute bundled guardrails without polluting the user's repository:

```bash
# 1. Fetch read-only skill reference into /tmp (NEVER commit into user's repo)
rm -rf /tmp/devskill-ref && git clone --depth 1 <SKILL_REPO_URL> /tmp/devskill-ref

# 2. Classify the user's task against the 30 archetypes (pick 1–2 max)
#    Read: /tmp/devskill-ref/index.json and /tmp/devskill-ref/ROUTING.md

# 3. Load ONLY the 3–5 prescribed guides for that archetype + active rules in RULES.md

# 4. If the task has >= 4 requirements or strict "MUST NOT" constraints (R-261–R-266):
#    Use /tmp/devskill-ref/scripts/req-ledger.py against a temporary ledger (/tmp/requirements.json)
#    init -> add -> freeze -> recite -> audit-prompt -> verify -> gate --require-frozen

# 5. Before finishing, run the bundled CI quality gate in the user's project repo:
/tmp/devskill-ref/scripts/ci-gate.sh
```

### Mode B — You Have Web-Fetch / HTTP Access Only *(No Shell or Git)*
Derive `<RAW_BASE>` from the URL the user gave you:
- **GitHub repo URL** `https://github.com/<owner>/<repo>` (or `.../tree/<branch>`)  
  → `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/` *(try `main`, fallback `master`)*
- **Direct raw file URL** (e.g. `.../<branch>/SKILL.md` or `.../<branch>/README.md`)  
  → strip the filename to get `<RAW_BASE>/`

Then fetch strictly in **4 progressive-disclosure hops** (never scrape the entire repository):

1. **`<RAW_BASE>/index.json`** — Machine-readable catalog of all documents, tags, rule range (`R-001..R-272`), and 30 archetypes.
2. **`<RAW_BASE>/ROUTING.md`** — Match the user's task to its archetype to obtain the exact **3–5 file Mandatory Reading List**, invariant rules, prohibited actions, and verification commands.
3. **`<RAW_BASE>/RULES.md`** *(relevant sections + universal invariants)* and **`<RAW_BASE>/security.md`** *(whenever touching APIs, auth, data, or agentic tooling)*.
4. **ONLY the 3–5 prescribed domain/framework guides** from `ROUTING.md` (e.g., `<RAW_BASE>/frameworks/erp/odoo.md`, `<RAW_BASE>/FRONTEND.md`, `<RAW_BASE>/agents/zero-missed-requirements.md`).

---

## 2. Non-Negotiable Remote Activation Rules

1. **Never Stop at the Landing Page**: Reading only `README.md`, `SKILL.md`, or `BOOTSTRAP.md` is **not** sufficient. You MUST follow `index.json` → `ROUTING.md` → the 3–5 domain guides for the active task.
2. **Never Bulk-Fetch All Documents (`R-263`)**: Loading > 5 unrelated guides induces Context Rot and degrades instruction recall. Fetch strictly on demand via `ROUTING.md`.
3. **Never Pollute the Target Workspace**: Keep cloned skill files and temporary ledgers in `/tmp/` (or gitignored scratch paths)—never commit DevSkill files into the user's project unless explicitly asked.
4. **Enforce Zero-Missed-Requirements (`R-261`–`R-266`)**: Whenever the user's prompt has ≥ 4 requirements or negative ("MUST NOT") constraints, freeze every requirement into a JSON ledger (`passes: false` by default), recite open negative constraints at milestones, run SatisFix deviation elicitation (`audit-prompt`), and refuse to finish until 100% of required items have verified execution proof.
5. **Prove Execution, Never Guess (`R-004`, `R-181`, `R-202`)**: Run real build, lint, typecheck, and test commands (observing Exit Code `0`) and score the result against [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) (≥ 95/100 total, ≥ 9.0/10 per category).

---

## 3. First Response Handshake (Optional Short Check)

Once bootstrapped from the URL, immediately proceed with the user's task and include a compact 3-line activation header (or internal plan note):
- **Archetype**: `<# and name from ROUTING.md>`
- **Loaded Guides**: `<3–5 exact relative paths fetched>`
- **Active Gates**: `<Rules enforced + verification commands to run>`

*Next*: Continue to [`SKILL.md`](SKILL.md) | [`AGENTS.md`](AGENTS.md) | [`ROUTING.md`](ROUTING.md) | [`index.json`](index.json).
