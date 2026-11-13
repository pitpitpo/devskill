# 🚨 Incident Response & Blameless Post-Mortems (`incident-response.md`)

> **Classification**: Production Site Reliability & Disaster Recovery  
> **Target**: On-Call Engineers, SREs, Incident Commanders

---

## 1. Severity Levels & SLA Response Times

| Severity | Definition | Response SLA | Update Cadence |
|---|---|---|---|
| **P0 (Critical)** | Core service completely down; revenue/data loss active (e.g. checkout broken) | **< 15 minutes** | Every 30 minutes |
| **P1 (Major)** | Major functionality degraded, no workaround available | **< 30 minutes** | Every 1 hour |
| **P2 (Moderate)**| Non-critical feature down, partial customer impact | **< 2 hours** | Every 4 hours |
| **P3 (Minor)** | Minor bug, workaround exists | **Next business day** | As resolved |

---

## 2. Incident Command Protocol

During a P0/P1 incident:
1. **Designate Incident Commander (IC)**: The IC directs the triage and coordinates efforts. They do NOT debug code directly.
2. **Mitigate First, Root-Cause Later**: Rollback to the previous stable release, scale resources, or toggle the feature flag off. Do not spend hours diagnosing the bug while production is down.
3. **Dedicated Channel**: Open an incident war room Slack channel (`#inc-YYYYMMDD-service`).

---

## 3. Blameless Post-Mortem Structure

Within 48 hours of resolving a P0/P1 incident, publish a post-mortem document:
- **Incident Summary**: What happened, start time, end time, total customer impact.
- **Root Cause (5 Whys)**: Deep causal analysis without assigning personal blame.
- **Timeline**: Chronological events from detection to mitigation.
- **Action Items**: Preventative measures assigned to specific owners with ticket IDs.
