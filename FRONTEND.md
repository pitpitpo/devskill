# FRONTEND.md — Universal Frontend Engineering & Design Craft Master Skill

> **Standard Identifier**: `DEVSKILL-FRONTEND-MASTER-001`  
> **Scope**: Framework-Agnostic Master Constitution for the Entire Web Frontend Ecosystem  
> **Governing Rules**: **R-001**, **R-034**, **R-074**, **R-075**, **R-085**, **R-125–R-139**, **R-251–R-253**, **R-259–R-260**  
> **Last Updated**: 2026-11-19

> **Golden Rule**: *Every pixel ships a contract to the user: semantic HTML first, CSS platform primitives before JavaScript, fine-grained reactivity without bloat, WCAG 2.2 AA accessibility by default, Core Web Vitals enforced in CI, and zero visual slop.*

---

## 1. The Frontend Framework Selection Matrix (2026)

Choose the simplest rendering model and framework that satisfies the product's interactivity, SEO, and team constraints. Never ship a 100KB SPA runtime for a content site, and never fight static HTML when building a collaborative canvas.

| Framework | Core Paradigm | Killer Strengths (2025–2026) | Ideal Workload | Deep-Dive Skill |
|---|---|---|---|---|
| **Next.js 16 + React 19.2** | RSC + Streaming SSR + React Compiler | `"use cache"`, Turbopack, Server Actions, `use()`, `useActionState`, massive ecosystem | Full-stack SaaS, e-commerce, multi-team web apps | [`frameworks/frontend/nextjs.md`](frameworks/frontend/nextjs.md), [`frameworks/frontend/react.md`](frameworks/frontend/react.md) |
| **Vue 3.5 + Nuxt 4** | Proxy Reactivity + Hybrid Nitro SSR | Reactive props destructure, `defineModel`, Vapor Mode, Nuxt 4 `app/` structure | Full-stack apps, rapid team velocity, hybrid SSR/SPA | [`frameworks/frontend/vue-nuxt.md`](frameworks/frontend/vue-nuxt.md) |
| **Svelte 5 + SvelteKit 2** | Compile-Time Signals (Runes) | `$state`/`$derived`/`$effect` in `.svelte.ts`, Snippets, progressive Form Actions | Ultra-fast interactive apps, small bundles, edge SSR | [`frameworks/frontend/sveltekit.md`](frameworks/frontend/sveltekit.md) |
| **Angular 19 / 20** | Signals + Zoneless Architecture | Native Zoneless change detection, `linkedSignal`, `httpResource`, `@defer` incremental hydration | Large enterprise apps, strict DI, monorepos | [`frameworks/frontend/angular.md`](frameworks/frontend/angular.md) |
| **Astro 5** | Zero-JS Content + Server Islands | `server:defer` Server Islands, Content Layer API, Actions, multi-framework islands | Marketing, docs, blogs, e-commerce storefronts | [`frameworks/frontend/astro.md`](frameworks/frontend/astro.md) |
| **SolidJS / SolidStart** | Fine-Grained Signals (Zero VDOM) | Direct DOM updates, `"use server"` RPC, `createStore`, highest JS perf/byte | High-frequency dashboards, data-dense trading/telemetry UIs | [`frameworks/frontend/solidjs.md`](frameworks/frontend/solidjs.md) |
| **Tailwind CSS v4 (Oxide)** | Rust Utility Engine + CSS-First Tokens | `@import "tailwindcss"`, `@theme` OKLCH tokens, native `@container` queries | Universal styling layer across every framework above | [`frameworks/frontend/tailwindcss.md`](frameworks/frontend/tailwindcss.md) |

---

## 2. Universal Design Engineering & Anti-Slop Visual Craft (R-251)

Great frontend engineering fuses software architecture with visual craft. Generic, low-craft interfaces fail users regardless of how clean the underlying TypeScript is.

### 2.1 Three-Tier Semantic Design Token Hierarchy
Never hardcode raw hex codes (`#3b82f6`), arbitrary pixels (`p-[13px]`), or magic z-indexes (`z-[9999]`) inside components. Enforce three strict token layers using **OKLCH** (perceptually uniform lightness across hues):

```css
/* 1. Primitive Palette (never referenced directly by feature components) */
:root {
  --palette-neutral-50:  oklch(0.985 0.002 247);
  --palette-neutral-900: oklch(0.175 0.012 255);
  --palette-brand-600:   oklch(0.550 0.195 258);
  --palette-danger-600:  oklch(0.560 0.215 27);
}

/* 2. Semantic Tokens (adapt automatically across light/dark/high-contrast themes) */
:root {
  --surface-canvas:  var(--palette-neutral-50);
  --text-primary:    var(--palette-neutral-900);
  --accent-primary:  var(--palette-brand-600);
  --status-danger:   var(--palette-danger-600);
  --radius-control:  0.5rem;
  --z-dropdown:      20;
  --z-modal:         40;
  --z-toast:         50;
}
```

### 2.2 Visual Craft Non-Negotiables
- **Typographic Hierarchy**: Pair at most two typefaces (sans/serif + monospace for code/numbers). Use `font-variant-numeric: tabular-nums` for tables, prices, KPIs, and timers so numbers align vertically without jitter. Cap body line length at `60ch–72ch` (`max-w-prose`).
- **Spatial Rhythm & Density**: Adhere strictly to a 4px/8px spacing grid. Vary layout rhythm intentionally — avoid repetitive identical 3-column card grids everywhere.
- **Complete Interactive State Matrix**: Every interactive control MUST style all 6 states explicitly: `default`, `hover`, `focus-visible` (never remove outlines without a high-contrast replacement), `active`, `disabled`, and `loading`/`error`.
- **Intentional Motion**: Animate only GPU-composited properties (`transform`, `opacity`, `clip-path`). Keep UI transitions crisp (`150ms–250ms ease-out`) and wrap animations in `@media (prefers-reduced-motion: reduce)`.
- **Zero Layout Thrash**: Render structural skeleton loaders matching exact final dimensions instead of jarring spinners that collapse and expand the page.

→ Deep dive: [`sections/frontend/design-systems-ui-craft.md`](sections/frontend/design-systems-ui-craft.md)

---

## 3. Web Platform First — Native APIs Before JavaScript (R-252)

Before installing a 40KB npm package, verify whether the modern baseline web platform already solves it natively with zero runtime cost and built-in accessibility:

| Problem | Legacy JS Library | Modern Baseline Web Platform API |
|---|---|---|
| Modal dialogs & focus trapping | Custom portal + focus-trap | Native `<dialog>` + `.showModal()` + `::backdrop` + `inert` |
| Popovers, tooltips, menus | Heavy Popper.js / custom portal | **Popover API** (`popover="auto"`, `popovertarget`) + **CSS Anchor Positioning** |
| Component-responsive layouts | `ResizeObserver` JS hacks | **CSS Container Queries** (`container-type: inline-size`, `@container`) |
| Parent-conditional styling | JS state toggling classes | **CSS `:has()`** selector (e.g., `form:has(:invalid) button`) |
| Page & state transitions | Heavy JS transition libraries | **View Transitions API** (`document.startViewTransition()`, `@view-transition`) |
| Accordions / Disclosures | Custom state + ARIA wiring | `<details name="group"><summary>...</summary></details>` |
| Style specificity wars | `!important` overrides | **CSS Cascade Layers** (`@layer reset, base, tokens, components, utilities;`) |
| RTL / Multi-language layout | Duplicate `.rtl` stylesheets | **CSS Logical Properties** (`margin-inline`, `padding-block`, `inset-inline-start`) |
| Responsive nested alignment | Fixed JS heights | **CSS Subgrid** (`grid-template-rows: subgrid`) |

---

## 4. Universal Frontend Architecture & Rendering Spectrum

```
Static Content ◄────────────────────────────────────────────────────────► High-Frequency App
  │                   │                     │                     │                 │
  ▼                   ▼                     ▼                     ▼                 ▼
Static HTML /     Astro 5 +            Next.js 16 RSC /      SvelteKit 2 /     SolidJS / SPA /
MPA (0 KB JS)     Server Islands       Nuxt 4 Hybrid SSR     Angular Zoneless  Canvas/WebGL
```

### Architectural Rules Across All Frameworks (R-253)
1. **Strict Server/Client Boundary**: Never import secrets, DB clients, or private environment variables into browser bundles. Never store per-request user/session state in module-level globals on an SSR server (causes catastrophic cross-user data leaks).
2. **Co-location by Feature**: Group routes, UI components, hooks/composables, validation schemas, and tests inside feature folders (`features/billing/*`), not bloated horizontal folders of 200 unrelated files.
3. **Headless Behavior + Styled Skin**: Separate complex keyboard/ARIA interaction state (dialog, combobox, tabs, menu via Radix, React Aria, Ark UI, Bits UI, Reka UI, or Angular CDK) from visual styling.
4. **No Waterfall Fetching**: Parallelize independent server requests (`Promise.all`) or push data loading to route loaders / Server Components instead of cascading `useEffect` / `onMounted` client chains.
5. **Typed Contracts at Every Boundary**: Validate all API payloads, form inputs, and URL search params with runtime schemas (Zod / Valibot / ArkType) on both client (UX) and server (security).

---

## 5. Universal State Taxonomy

Every piece of frontend state belongs to exactly one of five buckets. Misclassifying state is the #1 root cause of stale UIs and cascading re-renders:

| State Category | Owner | Lifecycle | Universal Tooling |
|---|---|---|---|
| **1. URL / Navigation State** | Browser URL | Shareable, bookmarkable (filters, sort, pagination, active tab) | Framework Router search params, `nuqs` |
| **2. Server Cache State** | Remote Backend DB | Async, stale-while-revalidate, optimistic mutations | TanStack Query (React/Vue/Svelte/Solid/Angular), Nuxt `useAsyncData`, Angular `httpResource` |
| **3. Form State** | Active `<form>` | Dirty tracking, field validation, pending submission | Native FormData + Actions, React Hook Form + Zod, Superforms, Angular Reactive Forms |
| **4. Ephemeral Local UI State** | Component Instance | Dropdown open, hover, active accordion | React `useState`, Vue `ref`, Svelte `$state`, Angular/Solid `signal` |
| **5. Shared Client UI State** | Browser Session | Theme, sidebar collapse, multi-step wizard draft, toast queue | Zustand / Jotai, Pinia, Svelte `.svelte.ts` Runes, NgRx SignalStore, Solid Store |

**Non-Negotiable Invariant**: *Derive, never duplicate.* If a value can be computed from existing state or server cache (e.g., `filteredItems`, `cartTotal`, `isFormValid`), compute it via a derived primitive (`computed`, `$derived`, `createMemo`, or plain render expression) — never synchronize it with an effect.

→ Deep dive: [`sections/frontend/state-management.md`](sections/frontend/state-management.md)

---

## 6. Core Web Vitals & Performance Budgets

Enforce real-user (CrUX) and synthetic CI budgets on every PR:

| Metric | Good (Ship Gate) | Needs Improvement | Primary Engineering Controls |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | **≤ 2.5s** | ≤ 4.0s | SSR/CDN HTML, `fetchpriority="high"` on hero image, AVIF/WebP `srcset`, preload subset `woff2` |
| **INP** (Interaction to Next Paint) | **≤ 200ms** | ≤ 500ms | Yield long tasks (>50ms) with `scheduler.yield()`, Web Workers for heavy compute, fine-grained reactivity, list virtualization |
| **CLS** (Cumulative Layout Shift) | **≤ 0.1** | ≤ 0.25 | Explicit `width`/`height` or CSS `aspect-ratio`, metric-matched fallback fonts, reserved skeleton slots |
| **Initial JS Payload** | **≤ 150KB gzipped** | ≤ 250KB | Route-level code splitting, dynamic `import()` for charts/editors, tree-shaking, zero moment.js/lodash-full |

→ Deep dive: [`sections/frontend/web-performance.md`](sections/frontend/web-performance.md)

---

## 7. Accessibility (WCAG 2.2 AA Mandatory)

- **Semantic HTML First**: Use `<button>` for actions, `<a href>` for navigation, `<main>`, `<nav>`, `<header>`, `<section>`, and proper single-`<h1>` heading order before adding ARIA attributes.
- **Full Keyboard Operability**: Every interactive flow works via `Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`, and arrow keys (roving `tabindex` for menus/tabs/lists).
- **Focus Visibility & Management**: High-contrast `:focus-visible` rings (≥ 3:1 contrast); move focus cleanly into opened dialogs and restore focus to the trigger on close.
- **Contrast & Touch Targets**: Minimum `4.5:1` for normal text, `3:1` for large text and UI boundaries; minimum `24×24px` (WCAG 2.2 AA) and recommended `44×44px` touch targets on mobile.
- **Accessible Forms & Live Regions**: Explicit `<label for="...">`, `aria-invalid`, `aria-describedby` linking error text, and `role="alert"` / `aria-live="polite"` for async status updates.

→ Deep dive: [`sections/frontend/accessibility.md`](sections/frontend/accessibility.md)

---

## 8. Frontend Security Hardening (R-260)

Every production web frontend MUST enforce defense-in-depth at the browser boundary:

```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{RANDOM}' 'strict-dynamic'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; require-trusted-types-for 'script';
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

- **Zero Tokens in `localStorage`/`sessionStorage`**: Store session tokens in `HttpOnly; Secure; SameSite=Lax` (or `Strict`) cookies; never expose JWTs or refresh tokens to XSS-accessible JS storage.
- **XSS & Injection Defense**: Never pass untrusted HTML to `dangerouslySetInnerHTML`, `v-html`, `{@html}`, or `[innerHTML]` without strict sanitization (`DOMPurify` + Trusted Types policy). Validate all `href` URLs against `javascript:` / `data:` schemes.
- **CSRF & Origin Protection**: Enforce `SameSite` cookies + origin/CSRF token verification on all state-mutating endpoints and Server/Form Actions.
- **Client Validation Is UX Only**: Every form constraint MUST be re-validated authoritatively on the server.

---

## 9. Internationalization (i18n), RTL & SEO

- **i18n**: Externalize all user-facing strings; format dates, numbers, lists, and currencies via native `Intl.DateTimeFormat`, `Intl.NumberFormat`, and `Intl.PluralRules`; build layouts exclusively with CSS logical properties (`ps-*`, `pe-*`, `ms-*`, `me-*`, `text-start`) so Arabic/Hebrew RTL works automatically.
- **SEO**: Unique `<title>` and `<meta name="description">` per route, canonical URLs, Open Graph / Twitter metadata, Schema.org JSON-LD structured data, dynamic `sitemap.xml` & `robots.txt`, and server-rendered indexable HTML.

---

## 10. Universal Frontend Testing Pyramid

| Layer | Tooling | Verification Scope |
|---|---|---|
| **Static Type & Lint** | TypeScript `strict` (`tsgo`/`tsc`), Biome / ESLint + a11y plugin | Zero `any`, zero unused hooks/signals, static a11y rules |
| **Unit** | Vitest | Pure domain logic, formatters, validators, state reducers/stores |
| **Component** | Testing Library (React/Vue/Svelte/Angular/Solid) + MSW | User-centric queries (`getByRole`, `getByLabelText`), loading/error/empty states |
| **Accessibility** | `axe-core` (`@axe-core/playwright` / `vitest-axe`) | Automated WCAG 2.2 AA zero-violation gate on every critical route |
| **E2E & Visual** | Playwright | Auth, checkout, core user journeys, responsive screenshot regression, console/network zero-error gate |
| **Performance** | Lighthouse CI (LHCI) | Performance ≥ 90, Accessibility ≥ 95, LCP ≤ 2.5s, CLS ≤ 0.1 |

---

## 11. Universal Frontend Ship Gate Checklist

- [ ] **Semantic & Accessible**: Zero `axe-core` WCAG 2.2 AA violations; full keyboard navigation verified.
- [ ] **Visual Craft**: Semantic design tokens (OKLCH/CSS variables); zero arbitrary magic sizes; complete hover/focus/disabled/loading/error/empty states; `prefers-reduced-motion` honored.
- [ ] **Web Platform First**: Native `<dialog>`, Popover, CSS Grid/Container Queries used before adding JS libraries.
- [ ] **Performance**: Lighthouse Performance ≥ 90; LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1; initial JS ≤ 150KB gzipped.
- [ ] **State Hygiene**: Zero server data duplicated in client stores; zero module-level request state on SSR servers.
- [ ] **Security**: Strict nonce-based CSP, `HttpOnly` session cookies, sanitized rich HTML, server-side validation on all mutations.
- [ ] **i18n & SEO**: Zero hardcoded strings (when localized), logical RTL properties, valid metadata & JSON-LD on public routes.
- [ ] **Tests**: Typecheck, linter, unit/component tests, and Playwright E2E journeys pass with Exit Code `0`.
