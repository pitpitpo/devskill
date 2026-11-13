# 🐳 Production Docker & Container Standards (`docker-containers.md`)

> **Classification**: Containerization & Runtime Security Standard  
> **Core Philosophy**: "Minimal Footprint, Multi-Stage Builds, Rootless Execution, Fast Cache Hits."

---

## 1. The Gold Standard Multi-Stage Dockerfile (Node.js / Next.js)

```dockerfile
# Stage 1: Dependency resolution
FROM node:20-alpine AS deps
WORKDIR /app
RUN apk add --no-cache libc6-compat
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Stage 2: Source compilation
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# Stage 3: Minimal, secure production runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Create dedicated non-root system user and group
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only build artifacts and standalone output
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# Proper signal handling
ENTRYPOINT ["node", "server.js"]
```

---

## 2. Container Security Rules

1. **Never Run as Root**: Always define an explicit non-root user (`USER 1001`).
2. **Drop Linux Capabilities**:
   ```yaml
   # docker-compose or Kubernetes securityContext
   security_opt:
     - no-new-privileges:true
   cap_drop:
     - ALL
   cap_add:
     - NET_BIND_SERVICE
   ```
3. **Read-Only Root Filesystem**:
   Run containers with `read_only: true` and mount ephemeral volumes (`tmpfs`) for temporary scratch space.
4. **Mandatory `.dockerignore`**:
   Never copy `.git`, `.env*`, `node_modules`, `tests`, or coverage directories into Docker context.
