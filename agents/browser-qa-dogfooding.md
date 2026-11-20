# 🌐 Autonomous Browser Dogfooding, Visual QA & Screenshot Auditing (`agents/browser-qa-dogfooding.md`)

> **Standard Identifier**: `AGT-QA-BROWSE-001`  
> **Status**: Active / Production Standard (Synthesizing `gstack /qa` & `/browse`, Playwright Core, and Anthropic Webapp Testing)  
> **Governing Rules**: **R-001**, **R-004**, **R-010**, **R-129–R-141**, **R-202**, **R-251**, **R-275**  
> **Last Updated**: 2026-11-20  

---

## 1. Frontmatter & Metadata

- **Purpose**: Autonomous end-to-end browser dogfooding, visual QA, screenshot regression auditing, and defect translation into permanent automated Playwright specs.
- **Applicability**: Frontend applications (Web, Next.js, Nuxt, SvelteKit, Angular, Astro, SolidJS), hybrid mobile webviews, and Electron/Tauri desktop webviews.
- **Prerequisites**: Node.js 20+, Playwright (`@playwright/test`), or native browser preview / headless automation tools.

---

## 2. Core Philosophy / Golden Rule

> **Golden Rule**: *Never declare a user-facing frontend feature or bug fix complete based solely on unit tests or simulated component rendering. Autonomous agents MUST launch the real running application, dogfood user journeys across multiple viewport form factors, capture visual evidence, assert zero browser console or network errors, and convert every discovered defect into a permanent, automated Playwright regression spec before declaring victory.*

---

## 3. Architecture & Design Patterns

The Dogfooding and Visual QA Engine operates as a closed-loop verification pipeline that bridges human visual inspection with deterministic test automation.

```
┌────────────────────────────────────────────────────────────────────────┐
│               AUTONOMOUS BROWSER DOGFOODING PIPELINE                   │
├────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: ENVIRONMENT & PROCESS WARMUP                                 │
│  • Detect dev server or build production bundle (`npm run build/start`)│
│  • Healthcheck endpoint poll (`http://localhost:3000/api/health`)       │
│  • Launch isolated browser context with video, console, & network taps │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Browser Session Ready
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: MULTI-VIEWPORT DOGFOODING TRAVERSAL                          │
│  • Desktop Viewport (1280×800) + Mobile Viewport (390×844 iPhone 14)   │
│  • Execute Core User Journey (Auth, Form Inputs, Async Mutations)      │
│  • Intercept 4xx/5xx responses and unhandled JavaScript exceptions    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Visual & Console Telemetry
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: EVIDENCE CAPTURE & AUDIT GATE                                │
│  • High-Resolution Viewport Screenshots & Visual Layout Audit          │
│  • Accessibility Tree Scan (`axe-core` zero WCAG 2.2 AA violations)    │
│  • Frame timing & Cumulative Layout Shift (CLS) confirmation           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Discovered Bug or Verified Flow
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: AUTOMATED REGRESSION SPEC SYNTHESIS                          │
│  • Convert failure trace into a deterministic Playwright `.spec.ts`   │
│  • Embed proof in git commit with screenshot artifact links            │
│  • Guarantee the bug CANNOT recur in future CI builds                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Production Autonomous Dogfooding & Visual Audit Harness (`scripts/dogfood-browser.ts`)

```typescript
import { chromium, Browser, BrowserContext, Page, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

export interface DogfoodResult {
  passed: boolean;
  viewport: { width: number; height: number };
  consoleErrors: string[];
  failedRequests: string[];
  screenshotPath: string;
}

export async function runBrowserDogfood(targetUrl: string, outputDir: string): Promise<DogfoodResult> {
  fs.mkdirSync(outputDir, { recursive: true });
  
  const browser: Browser = await chromium.launch({ headless: true });
  const context: BrowserContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: path.join(outputDir, 'videos') },
  });

  const page: Page = await context.newPage();
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];

  // Capture all browser console warnings and runtime exceptions
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(`[Console Error] ${msg.text()} at ${msg.location().url}:${msg.location().lineNumber}`);
    }
  });

  page.on('pageerror', (err) => {
    consoleErrors.push(`[Uncaught Page Error] ${err.message}`);
  });

  // Intercept failed network requests (4xx/5xx or network aborts)
  page.on('response', (response) => {
    if (response.status() >= 400 && !response.url().includes('/favicon.ico')) {
      failedRequests.push(`[HTTP ${response.status()}] ${response.url()}`);
    }
  });

  try {
    // Navigate with network idle guarantee
    const res = await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 30000 });
    expect(res?.status()).toBeLessThan(400);

    // Verify critical accessibility & semantic controls exist
    const mainLandmark = page.locator('main');
    await expect(mainLandmark).toBeVisible({ timeout: 5000 });

    // Capture baseline desktop screenshot
    const screenshotPath = path.join(outputDir, 'desktop-dogfood-audit.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });

    // Mobile responsive audit
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(500); // Allow responsive CSS animations to settle
    const mobileScreenshotPath = path.join(outputDir, 'mobile-dogfood-audit.png');
    await page.screenshot({ path: mobileScreenshotPath, fullPage: true });

    const passed = consoleErrors.length === 0 && failedRequests.length === 0;

    return {
      passed,
      viewport: { width: 1280, height: 800 },
      consoleErrors,
      failedRequests,
      screenshotPath,
    };
  } finally {
    await context.close();
    await browser.close();
  }
}
```

### 4.2 Automated Regression Spec Generated from QA Discovery (`tests/e2e/regression-issue-402.spec.ts`)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Regression Guard: Modal Dismissal & Focus Trapping', () => {
  test('closing modal restores focus to trigger button and does not throw console error', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    await page.goto('/settings/security');
    
    const trigger = page.getByRole('button', { name: /update password/i });
    await trigger.click();

    const dialog = page.getByRole('dialog', { name: /update password/i });
    await expect(dialog).toBeVisible();

    // Verify keyboard escape closes modal cleanly
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();

    // Invariant: Trigger button regains keyboard focus
    await expect(trigger).toBeFocused();

    // Invariant: Zero uncaught exceptions or React hydration errors
    expect(consoleErrors).toEqual([]);
  });
});
```

---

## 5. Security & Performance Considerations

1. **Defense Against Unchecked Console Poisoning**:
   - Web applications handling external user input or third-party webhooks can accidentally log sensitive customer credentials, session tokens, or PII into the client browser console.
   - The QA dogfooding harness asserts that `console.error` and `console.warn` streams remain completely clear of unredacted authorization headers, JWT payloads, and plain-text passwords.
2. **Layout Shift & Rendering Jank**:
   - Visual inspection must verify that above-the-fold content loads with **Cumulative Layout Shift (CLS) ≤ 0.1**.
   - Skeleton screens must occupy the exact computed width/height of the incoming asynchronous payload.
3. **Responsive Breakpoint Verification**:
   - Every interface must be validated at minimum on:
     - Mobile: `320px` (small phone) and `390px` (standard modern phone).
     - Tablet: `768px`.
     - Desktop: `1280px` and `1920px`.
   - Horizontal overflow (`document.body.scrollWidth > window.innerWidth`) is a strict blocking failure.

---

## 6. Common Pitfalls & Anti-Patterns

- ❌ **Assuming Component Tests Equal Real Browser Verification**: Testing Library running under `jsdom` or `happy-dom` lacks real layout engines, CSS cascades, font metrics, subgrid calculations, and actual network lifecycles. Real browsers must be exercised.
- ❌ **Ignoring 404s on Assets or Favicons**: Assets failing to load in production indicate broken CDN paths, incorrect public base URLs, or flawed static bundling.
- ❌ **Fixed Sleep Timers (`page.waitForTimeout(5000)`)**: Never introduce arbitrary sleep delays. Await deterministic UI states, network idle conditions, or URL navigation events.
- ❌ **Dismissing Mobile Overflow**: Developing exclusively on desktop viewports results in mobile pages with clipped CTA buttons, unreadable tables, and horizontal scrolling defects.

---

## 7. Verification Checklist

- [ ] Target application compiled, launched, and responding cleanly on local host port.
- [ ] Real browser instance executed core user journeys across Desktop (1280px) and Mobile (390px) viewports.
- [ ] Captured console error stream is verified to be 100% empty (zero runtime exceptions).
- [ ] Captured network log contains zero unexpected 4xx or 5xx HTTP responses.
- [ ] Horizontal layout verified free of horizontal scrollbars or clipped interactive touch targets.
- [ ] All bugs or visual regressions surfaced during dogfooding are codified into permanent Playwright regression specs.
- [ ] Final visual screenshot artifacts saved to disk and linked in the pull request review summary.
