# 🚀 Astro 5+ Content Layer, Islands & Server Islands Production Guide (`frameworks/frontend/astro.md`)

> **Standard Identifier**: `FW-FRONTEND-ASTRO-001`  
> **Framework**: Astro 5+ (Zero-JS by Default, Content Layer API, Server Islands, Actions)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-251–R-253**, **R-260**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Ship 0 KB of JavaScript by default. Cache the static page shell at the CDN edge, hydrate interactive UI only inside isolated Client Islands with explicit directives, and stream personalized dynamic fragments lazily via Astro 5 Server Islands (`server:defer`).*

---

## 2. Astro 5 Islands + Server Islands Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                CDN-CACHED STATIC HTML SHELL (0 KB JS)                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Static Header + Nav (<header>)                                    │  │
│  │  └── [Server Island: <UserAvatar server:defer />] ──► Streamed    │  │
│  │      (Personalized per-cookie on SSR without busting page cache)  │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ Static Markdown / Content Layer Article Body (0 KB JS)            │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ [Client Island: <PricingCalc client:visible />] (React/Svelte/Vue)│  │
│  │  └── Hydrates ONLY when scrolled into viewport                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Client Hydration Directive Selection Matrix
| Directive | When JS Loads & Hydrates | Best For |
|---|---|---|
| *(none)* | **Never (0 KB JS)** | Cards, headers, layouts, prose, pure CSS disclosures |
| `client:load` | Immediately on page load | Above-the-fold critical interactive controls (search bar, checkout form) |
| `client:idle` | When browser main thread is idle | Secondary widgets (chat launcher, feedback widget) |
| `client:visible` | When scrolled into viewport (`IntersectionObserver`) | Below-the-fold carousels, charts, comment sections |
| `client:media="(max-width: 768px)"` | Only when CSS media query matches | Mobile-only drawer navigation |
| `server:defer` | Lazy on-demand server render + fallback slot | Personalized cart count, user menu, live inventory price on cached pages |

---

## 3. Content Layer API (Type-Safe Collections with Zod)

Astro 5 replaces legacy content folders with the unified **Content Layer API** (`src/content.config.ts`), supporting local Markdown/MDX, JSON, or remote CMS loaders with strict Zod validation:

```typescript
// src/content.config.ts
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const docs = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/data/docs' }),
  schema: z.object({
    title: z.string().min(3).max(120),
    description: z.string().max(160),
    publishedAt: z.coerce.date(),
    category: z.enum(['guide', 'reference', 'architecture']),
    draft: z.boolean().default(false),
  }),
});

export const collections = { docs };
```

---

## 4. Server Islands (`server:defer`) + Type-Safe Astro Actions

### 4.1 Hybrid Page with Static Shell + Deferred Server Island
```astro
---
// src/pages/products/[slug].astro
import BaseLayout from '../../layouts/BaseLayout.astro';
import LiveInventoryBadge from '../../components/LiveInventoryBadge.astro';
import AddToCartButton from '../../components/AddToCartButton'; // React/Svelte/Solid island
import { getProductBySlug } from '../../lib/catalog';

export const prerender = true; // Static shell cached globally at CDN edge!
const product = await getProductBySlug(Astro.params.slug!);
if (!product) return Astro.redirect('/404');
---

<BaseLayout title={product.name} description={product.summary}>
  <article class="mx-auto max-w-4xl space-y-6 p-6">
    <h1 class="text-3xl font-bold">{product.name}</h1>

    <!-- Server Island: renders live stock on-demand without un-caching the static page -->
    <LiveInventoryBadge server:defer sku={product.sku}>
      <span slot="fallback" class="inline-block h-5 w-28 animate-pulse rounded bg-slate-200"></span>
    </LiveInventoryBadge>

    <!-- Client Island: hydrated only when interactive -->
    <AddToCartButton client:idle sku={product.sku} priceCents={product.priceCents} />
  </article>
</BaseLayout>
```

### 4.2 Type-Safe Server Actions (`src/actions/index.ts`)
```typescript
import { defineAction, ActionError } from 'astro:actions';
import { z } from 'astro:schema';
import { subscribeEmail } from '../lib/newsletter';

export const server = {
  newsletterSubscribe: defineAction({
    accept: 'form',
    input: z.object({
      email: z.string().email(),
      consent: z.literal('on'),
    }),
    handler: async (input, context) => {
      if (!context.locals.rateLimitOk) {
        throw new ActionError({ code: 'TOO_MANY_REQUESTS', message: 'Please try again later.' });
      }
      await subscribeEmail(input.email);
      return { subscribed: true };
    },
  }),
};
```

---

## 5. Multi-Framework Coexistence & View Transitions

- **Single UI Framework Discipline**: Although Astro supports React, Vue, Svelte, and Solid islands in the same project, standardize on **one** interactive UI framework per repository to avoid shipping duplicate framework runtimes to the client.
- **Smooth Navigation**: Add `<ClientRouter />` (Astro 5's renamed `<ViewTransitions />`) in `<head>` for SPA-like transitions on static MPA pages, and use `transition:name="..."` on shared hero elements. Always clean up listeners in `astro:before-swap` and initialize scripts in `astro:page-load`.

---

## 6. Security, Performance & Anti-Patterns

| Anti-Pattern | Root Cause | Remediated Standard |
|---|---|---|
| **Over-using `client:load` everywhere** | Treating Astro like a standard SPA | Default to static `.astro` components; upgrade to `client:visible` or `client:idle` only where interactive |
| **Wrapping the entire page in one React/Vue island** | Destroys Zero-JS advantage | Keep layouts, headers, and prose in `.astro`; wrap only interactive leaf widgets |
| **Leaking server secrets via `PUBLIC_` prefix** | Misconfiguring `astro:env` | Declare typed schema in `astro.config.mjs` (`env.schema`) separating `context: 'server'` secrets from `'client'` public vars |
| **Raw `set:html` on untrusted CMS input** | XSS injection vector | Sanitize untrusted HTML with `DOMPurify` / `sanitize-html` before `set:html` |

---

## 7. Verification Checklist

- [ ] `astro check` and `astro build` exit with code `0` and zero TypeScript/schema errors.
- [ ] Every `src/content.config.ts` collection validates frontmatter via strict Zod schemas.
- [ ] Every client island uses the laziest valid hydration directive (`client:visible` / `client:idle` before `client:load`).
- [ ] Personalized fragments on static pages use `server:defer` Server Islands with layout-matched `slot="fallback"`.
- [ ] Secrets are defined via `astro:env/server` and never leaked into browser bundles.
- [ ] Lighthouse Performance ≥ 95 and initial page JS payload ≤ 30KB gzipped on content routes.
