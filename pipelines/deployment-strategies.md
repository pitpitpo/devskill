# 🚀 Production Deployment Strategies (`deployment-strategies.md`)

> **Classification**: Continuous Delivery & Release Engineering  
> **Core Philosophy**: "Zero Downtime Deployments, Progressive Exposure, Instant Rollbacks."

---

## 1. Strategy Comparison

```
1. ROLLING UPDATE (Kubernetes Default)
   Replace old pods with new pods incrementally.
   [Old] [Old] [Old] ──► [Old] [Old] [New] ──► [Old] [New] [New] ──► [New] [New] [New]

2. BLUE / GREEN DEPLOYMENT (Instant Cutover)
   Maintain two identical environments.
   Traffic ──► [Blue: Active v1.0]
               [Green: Idle   v2.0]  (Switch router instantly) ──► Traffic to Green

3. CANARY DEPLOYMENT (Risk Mitigation)
   Route 5% of real user traffic to new version; monitor error metrics before full rollout.
   Traffic ──► 95% to v1.0
          └──►  5% to v2.0 (Canary)
```

---

## 2. Automated Rollback Thresholds

Every canary or automated deployment must configure automatic rollback triggers:
1. **HTTP 5xx Error Rate**: If error rate exceeds 0.5% for > 60 seconds, trigger immediate rollback.
2. **P99 Latency**: If P99 latency spikes by > 50% compared to baseline, rollback.
3. **Container Crashes (`CrashLoopBackOff`)**: If new pods crash within 3 minutes, rollback.
