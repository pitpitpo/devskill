# 🚀 Architecture Blueprint: Fullstack Next.js 15 App Router + Python FastAPI

> **Standard Identifier**: `SCAF-NEXTJS-FASTAPI-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Fullstack Engineers, Solutions Architects  
> **Classification**: Level 4 Scaffolding & Architecture Blueprint  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Pair the world's most productive UI layer (Next.js 15 React Server Components) with the world's most versatile asynchronous AI/data backend (Python FastAPI). Maintain end-to-end type safety by automatically generating TypeScript client SDKs directly from FastAPI's OpenAPI specification.*

This architecture delivers:
- **Instant Server Rendering & Streaming**: Next.js 15 App Router handles edge routing, SEO, static caching, and dynamic Suspense streaming.
- **High-Performance Async Backend**: FastAPI handles async database transactions, AI/ML integrations, background tasks, and strict Pydantic v2 data validation.
- **Zero-Manual-Types**: Any change to backend Pydantic models automatically updates frontend TypeScript types on build.

---

## 2. System Topology & Data Flow

```
                      ┌────────────────────────────────────────────────────────┐
                      │                     USER BROWSER                       │
                      └──────────────────────────┬─────────────────────────────┘
                                                 │
                                ┌────────────────┴────────────────┐
                                │ HTTP / HTTPS                    │
                                ▼                                 ▼
                     ┌───────────────────────┐         ┌───────────────────────┐
                     │   NEXT.JS 15 (APP)    │         │      STATIC ASSETS    │
                     │  React Server Comps   │         │    (CDN / Edge Cache) │
                     └──────────┬────────────┘         └───────────────────────┘
                                │ Server-to-Server Internal Calls (or Server Actions)
                                ▼
                     ┌───────────────────────┐
                     │    FASTAPI BACKEND    │
                     │   (Python 3.12+ /     │
                     │    Pydantic v2)       │
                     └──────────┬────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
      ┌───────────────────────┐     ┌───────────────────────┐
      │   POSTGRESQL (ACID)   │     │      REDIS CACHE      │
      └───────────────────────┘     └───────────────────────┘
```

---

## 3. Automated End-to-End Type Generation Pipeline

FastAPI automatically serves its OpenAPI schema at `/openapi.json`. In the Next.js frontend package, run `openapi-typescript` to generate strict TypeScript types:

```json
// frontend/package.json
{
  "scripts": {
    "codegen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/schema.d.ts"
  }
}
```

### Type-Safe Frontend Fetch Client (`openapi-fetch`)
```typescript
// frontend/src/lib/api/client.ts
import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const apiClient = createClient<paths>({
  baseUrl: process.env.INTERNAL_API_URL || "http://localhost:8000",
});

// Example Server Component Usage with full autocompletion and compile-time type safety:
export async function fetchOrderDetails(orderId: string) {
  const { data, error } = await apiClient.GET("/api/v1/orders/{order_id}", {
    params: {
      path: { order_id: orderId },
    },
    headers: {
      "Authorization": `Bearer ${process.env.INTERNAL_SERVICE_SECRET}`,
    },
  });

  if (error) {
    throw new Error(`Failed to load order: ${error.detail}`);
  }

  return data; // Strictly typed to backend OrderResponse Pydantic schema!
}
```

---

## 4. Production Docker Compose Local Dev Parity

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: app_development
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user -d app_development"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://dev_user:dev_password@db:5432/app_development
      REDIS_URL: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      INTERNAL_API_URL: http://backend:8000
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 5. Verification Checklist & Production Audit

- [ ] OpenAPI schema updates automatically trigger TypeScript type regeneration in CI.
- [ ] Next.js Server Components call FastAPI internal network endpoints with private service tokens.
- [ ] CORS is restricted to explicit frontend domains in production.
- [ ] Frontend uses `openapi-fetch` for zero-overhead, strictly typed network requests.
- [ ] Docker Compose environment boots reliably with healthy dependent services.
