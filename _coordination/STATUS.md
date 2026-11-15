# DevSkill Agent Coordination

## Shared Rules for All Agents
1. **NO HALLUCINATION**: Only write facts you can verify from files you've read or web searches you've done. If unsure, say "UNVERIFIED" and skip.
2. **CITE SOURCES**: Every rule or standard must reference its source (OWASP, 12-Factor, RFC, etc.)
3. **READ BEFORE WRITE**: Always read the existing file before overwriting. Merge, don't replace blindly.
4. **COORDINATE VIA THIS FILE**: Write your status here when done so other agents can pick up.
5. **NO PLACEHOLDERS**: Never write "TODO", "TBD", or "coming soon". If you can't complete it, leave it out.

## Agent Assignments
- Agent 1 (RESEARCHER): Read all existing files + ref_zip, produce gap analysis → write to _coordination/GAP_ANALYSIS.md
- Agent 2 (CORE-WRITER): Write RULES.md, AGENTS.md, WORKFLOW.md, DEFINITION_OF_DONE.md, MISTAKES.md, CLAUDE.md
- Agent 3 (STANDARDS-WRITER): Write SECURITY.md, ARCHITECTURE.md, TESTING.md, BACKEND_DATA.md  
- Agent 4 (PLATFORM-WRITER): Write FRONTEND.md, DEPLOYMENT.md, OBSERVABILITY.md, FRAMEWORKS.md, GLOSSARY.md
- Agent 5 (REVIEWER): Read all output files, validate quality, flag issues → write to _coordination/REVIEW.md

## Status Tracker
| Agent | Status | Files Done |
|-------|--------|-----------|
| Researcher | PENDING | - |
| Core Writer | COMPLETED | RULES.md, agents.md, workflows/WORKFLOW.md, DEFINITION_OF_DONE.md, MISTAKES.md, CLAUDE.md |
| Standards Writer | PENDING | - |
| Platform Writer | PENDING | - |
| Reviewer | PENDING | - |
