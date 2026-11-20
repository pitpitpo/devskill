# ⚡ Web Performance & Core Web Vitals (CWV) Industrial Engineering

> **Standard Identifier**: `SEC-FRONTEND-PERF-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Frontend Engineers, Full-Stack Developers, Web Architects  
> **Classification**: Level 4 Core Systems Knowledge Base  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Web performance directly impacts conversion, user retention, and organic search rankings. Fast by default is not an afterthought—it requires strict architectural constraints on payload size, main-thread execution time, and layout stability.*

Google's Core Web Vitals (CWV) define the empirical thresholds for real-user experience (CrUX). Failing these metrics harms SEO visibility and user trust:
- **LCP (Largest Contentful Paint)**: Loading speed ($\le 2.5\text{s}$)
- **INP (Interaction to Next Paint)**: Interactivity & input responsiveness ($\le 200\text{ms}$)
- **CLS (Cumulative Layout Shift)**: Visual stability ($\le 0.1$)

This guide details optimization strategies, code splitting, asset pipelines, and automated CI auditing.

---

## 2. Core Web Vitals Optimization Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               CORE WEB VITALS PILLARS                  │
                    └──────────────────────────┬─────────────────────────────┘
                                               │
          ┌────────────────────────────────────┼────────────────────────────────────┐
          ▼                                    ▼                                    ▼
   ┌──────────────┐                     ┌──────────────┐                     ┌──────────────┐
   │     LCP      │                     │     INP      │                     │     CLS      │
   │  (Loading)   │                     │(Interactivity│                     │ (Stability)  │
   ├──────────────┤                     ├──────────────┤                     ├──────────────┤
   │ Target:      │                     │ Target:      │                     │ Target:      │
   │ <= 2.5s      │                     │ <= 200ms     │                     │ <= 0.1       │
   ├──────────────┤                     ├──────────────┤                     ├──────────────┤
   │ • Priority   │                     │ • Yield to   │                     │ • Explicit   │
   │   Hints      │                     │   Main Thread│                     │   Dimensions │
   │ • AVIF/WebP  │                     │ • Debounce / │                     │ • CSS Aspect │
   │ • Font Pre-  │                     │   Throttle   │                     │   Ratio      │
   │   loading    │                     │ • Web Worker │                     │ • Font-      │
   │ • CDN Edge   │                     │   Offloading │                     │   Display    │
   └──────────────┘                     └──────────────┘                     └──────────────┘
```

---

## 3. Pillar-by-Pillar Engineering Mitigations

### 3.1 Largest Contentful Paint (LCP) $\le 2.5\text{s}$
LCP measures when the largest visual element in the viewport renders (hero image, video poster, or large heading block).

#### Mitigations:
1. **Priority Hints**: Tag hero images with `fetchpriority="high"` and `loading="eager"`:
   ```html
   <link rel="preload" as="image" href="/hero.avif" type="image/avif" fetchpriority="high" />
   <img src="/hero.avif" alt="Hero Banner" fetchpriority="high" loading="eager" decoding="async" />
   ```
2. **Next-Gen Formats**: Deliver AVIF (primary) and WebP (fallback) with responsive `srcset`:
   ```html
   <picture>
     <source srcset="/hero-800.avif 800w, /hero-1600.avif 1600w" type="image/avif" />
     <source srcset="/hero-800.webp 800w, /hero-1600.webp 1600w" type="image/webp" />
     <img src="/hero-800.jpg" alt="Hero Banner" width="1600" height="900" />
   </picture>
   ```
3. **Self-Hosted Zero-Shift Fonts**: Preload primary Latin font subsets with `font-display: swap`:
   ```html
   <link rel="preload" href="/fonts/inter-subset.woff2" as="font" type="font/woff2" crossorigin />
   ```

---

### 3.2 Interaction to Next Paint (INP) $\le 200\text{ms}$
INP replaced FID (First Input Delay) to measure the overall responsiveness of a page to user interactions (clicks, taps, keypresses) throughout its full lifecycle.

#### The Long Task Problem & Yielding to Main Thread:
JavaScript runs on a single main thread. Any task exceeding $50\text{ms}$ blocks user input handling.

```typescript
// Anti-Pattern: Monolithic blocking loop (> 250ms)
function processLargeDataset(items: DataItem[]) {
  for (const item of items) {
    expensiveComputation(item); // Freezes browser UI
  }
}

// Remediated Standard: Cooperative scheduling with scheduler.yield() (strictly typed)
interface SchedulerWithYield {
  yield?: () => Promise<void>;
}

async function yieldToMain(): Promise<void> {
  const sched = (globalThis as { scheduler?: SchedulerWithYield }).scheduler;
  if (typeof sched?.yield === 'function') {
    await sched.yield();
    return;
  }
  await new Promise<void>((resolve) => setTimeout(resolve, 0));
}

async function processLargeDatasetResponsive(items: DataItem[]): Promise<void> {
  for (let i = 0; i < items.length; i++) {
    expensiveComputation(items[i]);

    // Every 50 items or when execution exceeds frame budget, yield to browser
    if (i % 50 === 0) {
      await yieldToMain();
    }
  }
}
```

---

### 3.3 Cumulative Layout Shift (CLS) $\le 0.1$
CLS measures unexpected layout movements caused by asynchronous content loading above existing content.

#### Mitigations:
1. **Explicit Dimensions & Aspect Ratios**: Always supply `width` and `height` attributes or modern CSS `aspect-ratio`:
   ```css
   .card-media {
     width: 100%;
     aspect-ratio: 16 / 9;
     background-color: var(--skeleton-bg); /* Placeholder visual cue */
   }
   ```
2. **Reserved Ad & Dynamic Component Slots**: Never insert banners or banners without pre-reserving minimum height in CSS.
3. **Font Fallback Matching**: Use `@font-face` metric overrides (`size-adjust`, `ascent-override`, `descent-override`) to ensure fallback system fonts occupy identical vertical height as web fonts, preventing layout shift on font swap.

---

## 4. Modern Bundle & Resource Optimization

### 4.1 Route & Component-Level Code Splitting (Dynamic Imports)
Heavy client libraries (e.g., chart rendering, rich text editors) must never be bundled into the initial vendor chunk:

```tsx
import dynamic from 'next/dynamic';

// Heavy chart library loaded lazily only when scrolled into view or tab activated
const DynamicAnalyticsChart = dynamic(() => import('@/components/AnalyticsChart'), {
  loading: () => <div className="h-64 animate-pulse bg-slate-100 rounded-lg" />,
  ssr: false, // Disables server rendering if canvas-dependent
});
```

### 4.2 Modern Compression & Caching Headers
Configure reverse proxies (Nginx / Cloudflare) for modern compression:
- **Brotli (`br`)**: Level 4–6 for dynamic responses, Level 11 for pre-compressed static assets.
- **Cache-Control**:
  - Hashed static assets (`/_next/static/*`): `Cache-Control: public, max-age=31536000, immutable`
  - HTML pages / dynamic routes: `Cache-Control: public, max-age=0, must-revalidate`

---

## 5. Automated CI Audit & Continuous Monitoring

Integrate **Lighthouse CI (LHCI)** into GitHub Actions to fail PRs that regress performance budgets:

```yaml
# .lighthouserc.json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:performance": ["error", {"minScore": 0.90}],
        "first-contentful-paint": ["error", {"maxNumericValue": 1800}],
        "largest-contentful-paint": ["error", {"maxNumericValue": 2500}],
        "interactive": ["error", {"maxNumericValue": 3000}],
        "cumulative-layout-shift": ["error", {"maxNumericValue": 0.1}]
      }
    }
  }
}
```

---

## 6. Security & Performance Considerations

| Area | Risk / Focus | Standard Guideline |
| :--- | :--- | :--- |
| **Third-Party Script Bloat** | Tag Manager / Analytics | Load non-critical analytics with `async`/`defer` or `next/script` `strategy="lazyOnload"` |
| **Font Blocking** | Render Delay | Preload subsetted web fonts (`woff2`) with `font-display: swap` |
| **CSP Restrictions** | Script Injection | Enforce strict Content Security Policy with nonces; ban `unsafe-inline` |

---

## 7. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Unsized Media Elements** | Missing `width`/`height` on `<img>` | Massive layout shifts (CLS > 0.25) when image loads | Always declare explicit dimensions or CSS `aspect-ratio` |
| **Monolithic JS Bundles** | Importing heavy libraries at root | High TBT and INP; users on mobile devices experience unresponsive UI | Use dynamic `import()` / route code-splitting to lazy load heavy components |
| **Lazy Loading Hero Image** | Setting `loading="lazy"` on above-the-fold hero | Severely regresses LCP score (> 3.5s) | Set `fetchpriority="high"` and `loading="eager"` on hero image |

---

## 8. Verification Checklist & Production Audit

- [ ] LCP target ($\le 2.5\text{s}$) verified on simulated mobile 4G network via Chrome DevTools.
- [ ] Hero visual has `fetchpriority="high"` and is not lazy loaded.
- [ ] All images specify explicit `width`/`height` or CSS `aspect-ratio`.
- [ ] Font subsets are self-hosted with `font-display: swap` and preloaded.
- [ ] Long tasks (> 50ms) yield periodically to the main thread via `scheduler.yield()`.
- [ ] Vendor bundles are audited with `@next/bundle-analyzer`, `rollup-plugin-visualizer`, or `source-map-explorer`.
- [ ] Static assets are delivered with `immutable` caching headers and Brotli compression.
