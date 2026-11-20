# ☸️ Agentic Kubernetes Forensics, Auditing & Operations (`kstack-cluster-operations.md`)

> **Standard Identifier**: `SEC-DEVOPS-KSTACK-001`  
> **Status**: Active / Production Standard (Synthesizing `kubetail-org/kstack` + Kubernetes 1.32+ SRE Operations)  
> **Target Audience**: SREs, Platform Engineers, Autonomous Ops Agents  
> **Cross-References**: [`kubernetes-cloud.md`](kubernetes-cloud.md), [`observability-telemetry.md`](observability-telemetry.md), [`workflows/incident-response.md`](../../workflows/incident-response.md), [`RULES.md`](../../RULES.md) (`R-153`–`R-162`, `R-200`, `R-232`)

---

## 1. Core Philosophy: Read-Only First, Correlated Forensics, Zero Leaked Debug State

Kubernetes troubleshooting fails when engineers or agents randomly run `kubectl delete pod` (destroying crash evidence), inspect logs in isolation without cluster events, or leave privileged debug containers and temporary jobs running in production clusters.

This standard adapts the **`kstack`** operational model into strict, repeatable SRE playbooks:
1. **Default Read-Only Posture**: Monitoring, investigation, and auditing MUST use read-only verbs (`get`, `describe`, `logs`, `top`, `events`). Any mutating action (`apply`, `patch`, `scale`, `delete`, `rollout undo`) requires explicit operator confirmation (`R-200`).
2. **Correlated Triage**: Never diagnose from logs alone—always correlate **Node/Pod Conditions + Ranked Events + Resource Pressure + Container Logs + Recent Rollouts**.
3. **Four-Pillar Proactive Auditing**: Continuously audit **Security**, **Network**, **Cost**, and **Outdated/CVE** posture.
4. **Zero-Leak Ephemeral Hygiene (`/cleanup`)**: Every temporary debug pod, ephemeral container, or diagnostic resource MUST be tagged with an ownership label (`app.kubernetes.io/managed-by=devskill-debug`) and cleaned up deterministically when the session ends.

---

## 2. Monitoring & Triage Playbooks (`/cluster-status`, `/events`)

### 2.1 Dense Cluster Health Snapshot (`/cluster-status`)
Run this exact read-only sequence to build a complete cluster picture in < 10 seconds:
```bash
# 1. Context safety check (NEVER operate blindly on the wrong cluster!)
kubectl config current-context

# 2. Node health & pressure conditions (Ready, MemoryPressure, DiskPressure, PIDPressure)
kubectl get nodes -o wide
kubectl get nodes -o json | jq -r '
  .items[] | .metadata.name as $n |
  .status.conditions[] | select(.type != "Ready" and .status == "True" or (.type == "Ready" and .status != "True")) |
  "\($n)\t\(.type)=\(.status)\t\(.reason // "")"
'

# 3. Non-healthy workloads across all namespaces
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded
kubectl get pods -A -o json | jq -r '
  .items[] | select(any(.status.containerStatuses[]?; .restartCount >= 3 or .ready == false)) |
  "\(.metadata.namespace)/\(.metadata.name)\tphase=\(.status.phase)\trestarts=\([.status.containerStatuses[]?.restartCount] | add // 0)"
'
```

### 2.2 Severity-Ranked Cluster Events (`/events`)
```bash
# Warning events sorted chronologically (most recent last)
kubectl get events -A --field-selector=type=Warning --sort-by='.lastTimestamp' | tail -n 50
```

---

## 3. Deep Root-Cause Investigation (`/investigate`, `/logs`, `/metrics`, `/exec`)

Execute the 5-step correlated forensic ladder before proposing any remediation:

| Step | Question Answered | Concrete Read-Only Command |
| :--- | :--- | :--- |
| **1. Pod & Termination State** | OOMKilled (exit 137), SIGTERM (143), CrashLoopBackOff, ImagePullBackOff, or Unschedulable? | `kubectl describe pod <pod> -n <ns>` |
| **2. Previous Crash Logs** | What did the process print right before dying? (Crucial for CrashLoopBackOff!) | `kubectl logs <pod> -n <ns> -c <container> --previous --tail=200` |
| **3. Live Streaming Logs** | What errors are firing right now across all replicas? | `kubectl logs -l app=<name> -n <ns> --all-containers --tail=100 --prefix` |
| **4. Resource & Node Metrics** | Is CPU throttling (`limits.cpu`), memory approaching limit, or node exhausted? | `kubectl top pod <pod> -n <ns> --containers && kubectl top nodes` |
| **5. Rollout Diff Correlation** | Did a recent deployment or ConfigMap change trigger the regression? | `kubectl rollout history deployment/<name> -n <ns>` |

### Safe Ephemeral Debugging (`/exec`)
Prefer **ephemeral debug containers** (`kubectl debug`) over installing debugging packages (`curl`, `tcpdump`, `bash`) into production distroless images (`R-233`):
```bash
# Attach an ephemeral diagnostic container to a distroless/scratch pod without restarting it
kubectl debug -it <pod> -n <ns> \
  --image=nicolaka/netshoot:v0.13 \
  --target=<app-container> \
  --profile=restricted
```
> **Warning**: Never run `--profile=sysadmin` or `hostPID`/`hostNetwork` node shells in production without incident-commander approval and an audit ticket (`R-200`).

---

## 4. The Four-Pillar Cluster Audit Suite

### 4.1 Security & RBAC Audit (`/audit-security`)
Check for privilege escalations, overly broad `cluster-admin` bindings, and Pod Security violations:
```bash
# 1. List all subjects bound to cluster-admin
kubectl get clusterrolebindings -o json | jq -r '
  .items[] | select(.roleRef.name == "cluster-admin") |
  "\(.metadata.name)\t\(.subjects // [] | map("\(.kind):\(.namespace // "")/\(.name)") | join(", "))"
'

# 2. Detect privileged containers, hostNetwork, or runAsRoot pods
kubectl get pods -A -o json | jq -r '
  .items[] | .metadata as $m |
  .spec.containers[]? |
  select(.securityContext.privileged == true or .securityContext.runAsUser == 0 or .securityContext.allowPrivilegeEscalation != false) |
  "\($m.namespace)/\($m.name)\tcontainer=\(.name)\tprivileged=\(.securityContext.privileged // false)"
'

# 3. Verify Pod Security Admission labels on namespaces
kubectl get ns --show-labels | grep -v "pod-security.kubernetes.io/enforce"
```
**Target Standard**: All application namespaces enforce `pod-security.kubernetes.io/enforce=restricted`, `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, and `capabilities.drop: ["ALL"]` (`R-233`).

### 4.2 Network & Policy Audit (`/audit-network`)
```bash
# 1. Find namespaces lacking any NetworkPolicy (open flat-network blast radius)
comm -23 \
  <(kubectl get ns -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | sort) \
  <(kubectl get networkpolicies -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"\n"}{end}' | sort -u)

# 2. Inspect Services with zero ready endpoints (blackholed traffic)
kubectl get endpointslices -A -o json | jq -r '
  .items[] | select((.endpoints // [] | map(select(.conditions.ready == true)) | length) == 0) |
  "\(.metadata.namespace)/\(.metadata.name)"
'
```
**Target Standard**: Every production namespace enforces a default-deny ingress + egress `NetworkPolicy` with explicit allowlists and TLS/mTLS termination at the Gateway API / Ingress boundary.

### 4.3 Cost & Resource Right-Sizing Audit (`/audit-cost`)
Identify pods missing resource requests/limits (noisy-neighbor & OOM risk) or heavily over-provisioned (cloud spend waste):
```bash
# Flag containers without CPU/memory requests or memory limits
kubectl get pods -A -o json | jq -r '
  .items[] | .metadata as $m | .spec.containers[]? |
  select(.resources.requests.cpu == null or .resources.requests.memory == null or .resources.limits.memory == null) |
  "\($m.namespace)/\($m.name)\tcontainer=\(.name)\treq_cpu=\(.resources.requests.cpu // "NONE")\tlim_mem=\(.resources.limits.memory // "NONE")"
'
```
**Right-Sizing Rule**: Compare `requests` against 14-day p95 actual usage (`metrics-server` / Prometheus `container_memory_working_set_bytes`). Set memory `requests == limits` for Guaranteed QoS on latency-critical services; avoid tight CPU `limits` that cause CFS throttling unless strict multi-tenant capping is required.

### 4.4 Outdated APIs & Vulnerability Audit (`/audit-outdated`)
```bash
# 1. Detect deprecated/removed Kubernetes APIs before cluster upgrades (Pluto)
pluto detect-all-in-cluster --output wide

# 2. Scan live cluster images and misconfigurations (Trivy)
trivy k8s --report summary --severity CRITICAL,HIGH cluster
```

---

## 5. Zero-Leak Teardown & State Hygiene (`/cleanup`, `/forget`)

Every diagnostic session MUST end cleanly so orphaned debug artifacts never linger in production:
```bash
# Label any temporary diagnostic pod/job at creation:
#   -l app.kubernetes.io/managed-by=devskill-debug

# Verify and remove all temporary debug objects after investigation
kubectl get all -A -l app.kubernetes.io/managed-by=devskill-debug
kubectl delete all -A -l app.kubernetes.io/managed-by=devskill-debug
```
- **Cluster Context Hygiene (`/forget`)**: Clear cached cluster snapshots, temporary kubeconfig overrides, and diagnostic log dumps from local agent state once the incident closes so sensitive pod metadata or tokens are never leaked across sessions (`R-064`, `R-175`).

---

## 6. Verification Checklist

- [ ] Confirmed `kubectl config current-context` before executing any cluster command.
- [ ] Correlated pod conditions, Warning events, `--previous` logs, metrics, and rollout history before proposing remediation.
- [ ] Audited RBAC `cluster-admin` bindings and Pod Security `restricted` posture.
- [ ] Verified default-deny `NetworkPolicy` coverage and zero blackholed `EndpointSlice` targets.
- [ ] Checked missing resource requests/limits and deprecated Kubernetes APIs prior to upgrades.
- [ ] Confirmed zero leftover `managed-by=devskill-debug` pods, jobs, or local diagnostic dumps.
