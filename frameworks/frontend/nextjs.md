# 🌐 Next.js Production Guide (`nextjs.md`)

> **Framework**: Next.js 14 / 15 (App Router)  
> **Classification**: Production Fullstack Frontend Standard  
> **Core Philosophy**: "Server-First by Default; Push Client Components to the Leaves."

---

## 1. App Router Architecture & Component Boundaries

In the App Router, every component is a **React Server Component (RSC)** by default. Server Components execute exclusively on the server, producing zero JavaScript bundle overhead on the client.

```
                  ┌─────────────────────────────────────────┐
                  │    SERVER COMPONENT (app/page.tsx)      │
                  │  - Direct DB / ORM queries              │
                  │  - Read secret API keys                 │
                  │  - Heavy server-side dependencies       │
                  └────────────────────┬────────────────────┘
                                       │ passes serializable props
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │     CLIENT COMPONENT ('use client')     │
                  │  - Interactive UI (onClick, onChange)   │
                  │  - React Hooks (useState, useEffect)    │
                  │  - Browser APIs (localStorage, window)  │
                  └─────────────────────────────────────────┘
```

### The Boundary Rule
Never declare `'use client'` at the page level. Keep pages and layouts as Server Components. Extract only the interactive leaves (buttons, form inputs, modals) into dedicated Client Components.

---

## 2. Server Actions & Secure Form Mutations

Server Actions allow asynchronous RPC mutations directly from client or server components.

```typescript
// app/actions/create-project.ts
'use server';

import { z } from 'zod';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import { revalidatePath } from 'next/cache';

const CreateProjectSchema = z.object({
  name: z.string().trim().min(3).max(50),
  description: z.string().trim().max(300).optional(),
});

export type ActionState = {
  success: boolean;
  message?: string;
  errors?: Record<string, string[]>;
};

export async function createProjectAction(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const session = await auth();
  if (!session?.user?.id) {
    return { success: false, message: 'Unauthorized' };
  }

  const rawData = {
    name: formData.get('name'),
    description: formData.get('description'),
  };

  const validation = CreateProjectSchema.safeParse(rawData);
  if (!validation.success) {
    return {
      success: false,
      errors: validation.error.flatten().fieldErrors,
    };
  }

  try {
    await db.project.create({
      data: {
        ...validation.data,
        ownerId: session.user.id,
      },
    });

    revalidatePath('/dashboard/projects');
    return { success: true };
  } catch (error) {
    console.error('Failed to create project:', error);
    return { success: false, message: 'Internal server error' };
  }
}
```

---

## 3. Data Fetching & Cache Management

Next.js extends `fetch` with granular caching tiers:

```typescript
// 1. Static Data (Cached indefinitely until tag is revalidated)
const staticData = await fetch('https://api.internal/catalog', {
  next: { tags: ['catalog'] },
});

// 2. Time-Based Revalidation (ISR - 60 seconds)
const revalidatedData = await fetch('https://api.internal/metrics', {
  next: { revalidate: 60 },
});

// 3. Dynamic Data (Never cached, fetched on every request)
const dynamicData = await fetch('https://api.internal/user/profile', {
  cache: 'no-store',
});
```

---

## 4. Security & Environment Guardrails

1. **Prevent Secret Exfiltration**:
   - Variables prefixed with `NEXT_PUBLIC_` are injected into browser bundles.
   - Database credentials, private API keys, and signing tokens must NEVER use the `NEXT_PUBLIC_` prefix.
   - Use the `server-only` package to prevent accidental imports:
     ```typescript
     import 'server-only';
     export const privateKey = process.env.STRIPE_SECRET_KEY;
     ```
2. **Sanitize Dynamic HTML**:
   - Never use `dangerouslySetInnerHTML` without sanitizing via `dompurify` or `sanitize-html`.
3. **Route Handlers Security**:
   - Protect API route handlers (`app/api/.../route.ts`) with explicit CSRF checks, rate limiting, and session verification.

---

## 5. Performance Checklist

- [ ] Use `next/image` with explicit `width`, `height`, and `sizes` to eliminate layout shift (CLS).
- [ ] Use `next/font` for local or Google font preloading without layout pop.
- [ ] Implement `loading.tsx` and React Suspense boundaries for progressive streaming.
- [ ] Analyze bundle sizes with `@next/bundle-analyzer` to keep initial JS < 100KB gzipped.
