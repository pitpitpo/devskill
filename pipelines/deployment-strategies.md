# 🚢 Production Deployment Strategies: Blue/Green, Canary & Progressive Delivery

> **Standard Identifier**: `PL-DEPLOY-STRATEGIES-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Platform Engineers, SREs, Release Architects  
> **Classification**: Level 4 Pipeline Engineering Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Decouple deployment from release. Deploy new code silently to production infrastructure, verify health with synthetic traffic, and progressively shift customer traffic using automated metrics gates that abort instantly on error rate spikes.*

Traditional "big bang" deployments (stopping old containers and starting new ones simultaneously) guarantee service interruption, database migration lockups, and high blast radius on regressions. Modern production delivery mandates zero-downtime progressive deployment topologies.

---

## 2. Deployment Topology Comparison Matrix

```
                      ┌────────────────────────────────────────────────────────┐
                      │              DEPLOYMENT PATTERNS COMPARISON            │
                      └──────────────────────────┬─────────────────────────────┘
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          ▼                                      ▼                                      ▼
   ┌──────────────┐                       ┌──────────────┐                       ┌──────────────┐
   │ ROLLING      │                       │ BLUE / GREEN │                       │ CANARY       │
   │ UPDATE       │                       │ CUTOVER      │                       │ RELEASE      │
   ├──────────────┤                       ├──────────────┤                       ├──────────────┤
   │ Replace pods │                       │ Stand up 100%│                       │ Route 1% ->  │
   │ incrementally│                       │ parallel env │                       │ 5% -> 25%    │
   │ in place     │                       │ Switch router│                       │ -> 100%      │
   └──────────────┘                       └──────────────┘                       └──────────────┘
```

| Strategy | Zero Downtime? | Resource Overhead | Rollback Speed | Blast Radius | Complexity | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rolling Update** | Yes (if configured properly) | 10% - 25% (maxSurge) | Moderate (reverse rollout) | Medium (all users hit new pods over minutes) | Low (native Kubernetes) | Stateless background services, low-risk internal tools |
| **Blue/Green** | Yes | 100% (doubles fleet temporarily) | Instant (flip router back) | High during cutover; instant revert | Medium | Core API services requiring atomic instant cutover |
| **Canary** | Yes | 10% - 20% | Instant (reset router weight to 0%) | Minimal (< 1% of users during triage) | High (requires service mesh or Argo Rollouts) | High-volume critical consumer applications |

---

## 3. Kubernetes Native Rolling Update Configuration

To achieve true zero-downtime rolling updates in Kubernetes, configure `maxSurge`, `maxUnavailable`, and lifecycle pre-stop hooks:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Create up to 3 extra pods before killing old ones
      maxUnavailable: 0    # Never permit fewer than 10 available pods during rollout
  template:
    spec:
      containers:
      - name: api
        image: registry.internal/api:v2.4.0
        lifecycle:
          preStop:
            exec:
              # Wait 15s to allow ingress load balancer to remove pod from endpoints
              command: ["/bin/sh", "-c", "sleep 15"]
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 3
          failureThreshold: 2
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
```

---

## 4. Canary Progressive Delivery with Argo Rollouts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: billing-service
spec:
  replicas: 20
  strategy:
    canary:
      # Automated traffic routing steps
      steps:
      - setWeight: 5
      - pause: { duration: 10m } # Bake for 10 minutes
      - analysis:
          templates:
          - templateName: error-rate-analysis
      - setWeight: 25
      - pause: { duration: 30m }
      - setWeight: 50
      - pause: { duration: 15m }
      - setWeight: 100
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: error-rate-analysis
spec:
  metrics:
  - name: success-rate
    interval: 60s
    successCondition: result[0] >= 0.999 # 99.9% success rate required
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(http_requests_total{service="billing",status=~"2.*"}[2m])) 
          / 
          sum(rate(http_requests_total{service="billing"}[2m]))
```

---

## 5. Backward-Compatible Database Migrations (Expand/Contract)

Application deployments cannot roll out safely if database schema changes break old running pods.

```
   Phase 1: EXPAND
   • Add new nullable column or view (both old & new pods work)
   • Deploy code that writes to both old and new columns
               │
               ▼
   Phase 2: BACKFILL
   • Asynchronously migrate legacy data to new column
               │
               ▼
   Phase 3: CONTRACT
   • Deploy code that reads & writes exclusively from new column
   • Drop deprecated old column in subsequent migration
```

---


---

## 5. Security & Performance Considerations

| Area | Focus | Standard Guideline |
| :--- | :--- | :--- |
| **Zero-Downtime Drainage** | Traffic Loss Prevention | Configure `preStop` sleep hook (15s) ensuring ingress deregistration |
| **Automated Metric Rollback** | Outage Containment | Abort canary rollout immediately if error rate exceeds 0.1% |
| **RBAC Deployment Gate** | Unauthorized Deployments | Restrict production deployment pipelines to signed tags and approved environments |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Dropping Capacity During Rollout** | Setting `maxUnavailable: 25%` on small fleet | Traffic overwhelms remaining pods, causing cascading HTTP 503 errors | Configure `maxUnavailable: 0` and `maxSurge: 25%` |
| **Breaking DB Migrations** | Renaming database column in same release | Old pods crash instantly before new pods finish deploying | Always use the multi-phase Expand/Contract migration pattern |
| **Missing Readiness Probes** | Pod declared ready before warming cache/connections | User traffic routed to cold pod, causing timeout spikes | Configure realistic `readinessProbe` with `initialDelaySeconds` |

## 6. Verification Checklist & Production Audit

- [ ] Deployments configure `maxUnavailable: 0` to prevent drop in capacity during rollout.
- [ ] Container pods define `preStop` sleep hook (10–15s) ensuring clean deregistration from ingress routers.
- [ ] Canary deployments automate rollbacks based on real-time Prometheus error rate metrics.
- [ ] Database migrations strictly follow the Expand/Contract multi-phase methodology.
- [ ] Automated smoke tests execute against newly deployed preview pods before opening customer traffic.
