# 🐳 Production Docker Containerization & Security Hardening

> **Standard Identifier**: `SEC-DEVOPS-DOCKER-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: DevOps Engineers, Security Architects, Backend Engineers  
> **Classification**: Level 4 Infrastructure Engineering Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Containers are immutable, ephemeral, single-concern runtime environments. Never run containers as root, never include build toolchains in final runtime layers, and standardize on Google Distroless or Chainguard base images to minimize the vulnerability attack surface.*

Compromised container runtimes often result from excessive base image utilities (`curl`, `wget`, `bash`, package managers) that allow attackers to download payloads and escalate privileges. Production Docker engineering mandates:
- Multi-stage compilation separating build dependencies from the final image.
- Unprivileged user execution (`USER 10001:10001` or `nonroot`).
- Read-only root filesystems (`readOnlyRootFilesystem: true`).
- Dropped Linux capabilities (`ALL` dropped, adding back only what is required).

---

## 2. Multi-Stage Build Architecture

```
   ┌─────────────────────────────────────────────────────────┐
   │                  BUILDER STAGE                          │
   │  Base: node:20-alpine / golang:1.22-alpine              │
   │  • Compiles source code, installs dependencies          │
   │  • Output size: ~1.2 GB                                 │
   └────────────────────────────┬────────────────────────────┘
                                │ Copy ONLY compiled artifacts
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │                  RUNTIME STAGE                          │
   │  Base: gcr.io/distroless/nodejs20-debian12:nonroot      │
   │  • Contains zero package managers, shells, or compilers │
   │  • Runs as unprivileged non-root user (UID 65532)        │
   │  • Output size: ~65 MB (< 5% of build stage!)           │
   └─────────────────────────────────────────────────────────┘
```

---

## 3. Industrial-Grade Production Dockerfiles

### 3.1 Node.js / Next.js Production Dockerfile (Standalone)
```dockerfile
# 1. Dependency Resolution Stage
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# 2. Builder Stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# 3. Minimal Production Runtime Stage
FROM gcr.io/distroless/nodejs20-debian12:nonroot AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Copy standalone build output and static public files
COPY --from=builder --chown=nonroot:nonroot /app/public ./public
COPY --from=builder --chown=nonroot:nonroot /app/.next/standalone ./
COPY --from=builder --chown=nonroot:nonroot /app/.next/static ./.next/static

USER nonroot
EXPOSE 3000

CMD ["server.js"]
```

### 3.2 Go High-Performance Microservice Dockerfile (Scratch Base)
```dockerfile
# 1. Compiler Stage
FROM golang:1.22-alpine AS builder
RUN apk add --no-cache ca-certificates git
WORKDIR /build

COPY go.mod go.sum ./
RUN go mod download

COPY . .
# CGO_ENABLED=0 builds a completely static Linux ELF binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-s -w -extldflags '-static'" \
    -o /build/api-service ./cmd/api

# Create non-root user credentials to copy into scratch
RUN echo "appuser:x:10001:10001:App User:/:/sbin/nologin" > /etc/passwd_app

# 2. Ultra-Minimal Runtime (Absolute Zero Attack Surface)
FROM scratch
WORKDIR /

# Copy SSL root certificates and user credentials
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /etc/passwd_app /etc/passwd
COPY --from=builder /build/api-service /api-service

USER 10001:10001
EXPOSE 8080

ENTRYPOINT ["/api-service"]
```

---

## 4. Container Security Hardening Matrix

| Security Control | Purpose | Implementation |
| :--- | :--- | :--- |
| **Non-Root Execution** | Prevents host privilege escalation if container breakout occurs | `USER 10001:10001` in Dockerfile |
| **Read-Only Root Filesystem** | Stops attackers from dropping executables or scripts in `/tmp` | `readOnlyRootFilesystem: true` in Kubernetes security context |
| **Drop Linux Capabilities** | Strips dangerous kernel capabilities (e.g. `CAP_NET_RAW`, `CAP_SYS_ADMIN`) | `securityContext.capabilities.drop: ["ALL"]` |
| **No New Privileges** | Disallows `setuid` binaries from gaining root | `allowPrivilegeEscalation: false` |
| **Resource Constraints** | Prevents container-level memory leaks from freezing the host VM | Explicit `resources.limits.memory` and `resources.limits.cpu` |

---

## 5. Verification Checklist & Production Audit

- [ ] All Dockerfiles use multi-stage builds separating compilation from runtime.
- [ ] Base images specify immutable digests (e.g., `node:20-alpine@sha256:...`) or distroless tags.
- [ ] No container runs with `USER root`.
- [ ] Package managers (`apk`, `apt-get`) and shells are absent from the final runtime image.
- [ ] Trivy vulnerability scan passes with zero High/Critical unpatched CVEs.
- [ ] Container passes the CIS Docker Benchmark audit.
