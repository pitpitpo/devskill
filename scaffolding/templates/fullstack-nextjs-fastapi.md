# 📦 Fullstack Architecture Blueprint: Next.js + FastAPI (`fullstack-nextjs-fastapi.md`)

> **Stack**: Next.js 15 (Frontend) + FastAPI (Backend API) + PostgreSQL + Redis  
> **Use Case**: Modern SaaS, AI-powered applications, high-performance dashboards

---

## 1. Directory Structure

```
my-saas-app/
├── apps/
│   ├── web/                    # Next.js 15 App Router frontend
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── package.json
│   │   └── Dockerfile
│   └── api/                    # FastAPI backend service
│       ├── app/
│       │   ├── api/v1/
│       │   ├── core/
│       │   ├── models/
│       │   ├── schemas/
│       │   └── main.py
│       ├── pyproject.toml
│       └── Dockerfile
├── packages/
│   └── openapi-client/         # Auto-generated TypeScript client from FastAPI OpenAPI
├── docker-compose.yml          # Local dev environment
└── .github/workflows/ci.yml
```

---

## 2. API Contract & Automatic Client Generation

1. FastAPI automatically exports OpenAPI specification at `/openapi.json`.
2. Generate type-safe TypeScript clients in the frontend monorepo using `openapi-typescript` or `orval`:
   ```bash
   npx openapi-typescript http://localhost:8000/openapi.json -o packages/openapi-client/schema.d.ts
   ```
3. Frontend imports strict types directly:
   ```typescript
   import type { paths } from '@/packages/openapi-client/schema';
   type UserResponse = paths['/users/{id}']['get']['responses'][200]['content']['application/json'];
   ```
