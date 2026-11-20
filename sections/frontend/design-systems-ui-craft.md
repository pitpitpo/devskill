# 🎨 Design Systems, Modern CSS Platform & UI Craft (`sections/frontend/design-systems-ui-craft.md`)

> **Standard Identifier**: `SEC-FRONTEND-DESIGN-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Design Systems Engineers, Frontend Architects, Product Engineers  
> **Governing Rules**: **R-001**, **R-125–R-139**, **R-251**, **R-252**, **R-259**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *A design system is a compiler for product consistency, not a collection of static mockups. Encode visual decisions as semantic tokens, enforce behavior via headless accessible primitives, lean on modern baseline CSS instead of JavaScript layout hacks, and eliminate generic AI/template UI slop.*

---

## 2. W3C DTCG Design Token Architecture

Structure tokens in three unidirectional layers so themes (light, dark, high-contrast, white-label brands) swap cleanly with zero component code changes:

```
Layer 1: Primitive Tokens   (--color-slate-900, --space-4, --font-sans)
            │
            ▼  (alias only)
Layer 2: Semantic Tokens    (--surface-canvas, --surface-elevated, --text-primary, --border-subtle)
            │
            ▼  (consumed by UI)
Layer 3: Component Tokens   (--button-bg-primary, --input-ring-focus, --card-padding)
```

### 2.1 Perceptually Uniform OKLCH Palette & Dark Mode
Unlike HSL (where `50%` lightness yellow looks blinding while `50%` blue looks dark), **OKLCH** guarantees predictable contrast ratios across hues:

```css
@layer tokens {
  :root {
    color-scheme: light dark;

    /* Semantic surfaces & inks */
    --surface-canvas:   light-dark(oklch(0.988 0.003 250), oklch(0.145 0.010 255));
    --surface-elevated: light-dark(oklch(1.000 0.000 0),   oklch(0.190 0.012 255));
    --surface-sunken:   light-dark(oklch(0.955 0.006 250), oklch(0.115 0.008 255));

    --text-primary:     light-dark(oklch(0.175 0.014 255), oklch(0.955 0.006 250));
    --text-secondary:   light-dark(oklch(0.450 0.015 255), oklch(0.720 0.012 255));

    --border-subtle:    light-dark(oklch(0.895 0.008 250), oklch(0.285 0.014 255));
    --accent-primary:   light-dark(oklch(0.540 0.190 258), oklch(0.680 0.170 258));
    --accent-contrast:  oklch(0.990 0.002 250);

    /* Fluid typography scale */
    --text-display: clamp(2rem, 1.35rem + 2.8vw, 3.75rem);
    --text-h1:      clamp(1.625rem, 1.25rem + 1.5vw, 2.5rem);
    --text-h2:      clamp(1.25rem, 1.05rem + 0.8vw, 1.75rem);
    --text-body:    1rem;
    --text-caption: 0.8125rem;

    /* Elevation & Motion */
    --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
    --duration-fast:  150ms;
    --duration-base:  220ms;
  }
}
```

---

## 3. Modern Baseline CSS Platform Patterns (2025–2026)

### 3.1 Cascade Layers (`@layer`) — Zero Specificity Wars
Declare explicit layer precedence at the very top of your global stylesheet so reset styles never override components and utilities always win cleanly without `!important`:

```css
@layer reset, tokens, base, components, utilities;
```

### 3.2 Component-Driven Responsiveness with `@container`
Media queries couple components to viewport width, breaking reuse in sidebars vs. full-width pages. Use **Container Queries**:

```css
.metric-shell {
  container-type: inline-size;
  container-name: metric;
}

.metric-card {
  display: grid;
  gap: 0.75rem;
}

@container metric (min-width: 28rem) {
  .metric-card {
    grid-template-columns: 1fr auto;
    align-items: center;
  }
}
```

### 3.3 Native Popover + CSS Anchor Positioning + `<dialog>`
Replace fragile z-index/portal JS positioning libraries with top-layer native primitives:

```html
<button popovertarget="row-actions" style="anchor-name: --row-btn;">Actions</button>

<menu id="row-actions" popover="auto" class="action-menu">
  <li><button type="button">Duplicate</button></li>
  <li><button type="button">Archive</button></li>
</menu>
```

```css
.action-menu {
  position-anchor: --row-btn;
  inset: auto;
  top: anchor(bottom);
  right: anchor(right);
  margin-block-start: 0.375rem;
  transition: opacity var(--duration-fast) var(--ease-out-quart),
              transform var(--duration-fast) var(--ease-out-quart),
              overlay var(--duration-fast) allow-discrete,
              display var(--duration-fast) allow-discrete;
}

@starting-style {
  .action-menu:popover-open {
    opacity: 0;
    transform: translateY(-4px);
  }
}
```

### 3.4 View Transitions & Reduced Motion Guard
```css
@view-transition {
  navigation: auto;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 4. Headless Component Architecture & API Ergonomics

### 4.1 The Headless + Styled Split
Never build complex WAI-ARIA widgets (Combobox, Dialog, Select, DatePicker, Toast, Tabs, Tooltip) from scratch unless your team owns dedicated accessibility specialists. Pair a battle-tested headless library with your semantic design tokens:

| Ecosystem | Recommended Headless Primitives |
|---|---|
| **React / Next.js** | Radix UI, Base UI, React Aria Components, Ariakit |
| **Vue / Nuxt** | Reka UI (formerly Radix Vue), Ark UI |
| **Svelte 5** | Bits UI, Melt UI, Ark UI |
| **Angular** | Angular CDK (`@angular/cdk`), Angular Aria / ng-primitives |
| **SolidJS** | Kobalte, Ark UI |

### 4.2 Component API Design Rules
1. **Explicit Variants Over Boolean Explosion**: Prefer `variant="primary" | "secondary" | "danger"` over `isPrimary isSecondary isDanger` (impossible states become unrepresentable).
2. **Compound Composition Over Prop Bloat**: Prefer `<Card><Card.Header /><Card.Body /><Card.Footer /></Card>` over `<Card title="..." subtitle="..." footerText="..." icon={...} showDivider />`.
3. **Controlled & Uncontrolled Parity**: Interactive form/disclosure primitives should support both uncontrolled (`defaultValue`) and controlled (`value` + `onValueChange`) usage.
4. **Native Attribute Forwarding**: Always forward standard HTML/ARIA attributes (`id`, `aria-*`, `data-*`, `disabled`) to the underlying semantic element.

---

## 5. Anti-Slop UI Craft Rubric

Reject and refactor any UI exhibiting these common failure modes:

| Visual Slop Anti-Pattern | Engineering & Design Fix |
|---|---|
| **Uniform Card-Grid Monotony** (every section is 3 identical rounded cards) | Match layout to information density: editorial split hero, dense tabular grid with `tabular-nums`, sticky master-detail pane, or asymmetric bento |
| **Pill & Badge Overload** (every metadata label wrapped in neon rounded pills) | Use typographic hierarchy, muted secondary inks, hairline dividers, and reserve status badges strictly for mutable lifecycle states |
| **Invisible / Missing Focus Rings** (`outline: none`) | Style crisp 2px `:focus-visible` rings with `outline-offset: 2px` meeting ≥ 3:1 contrast |
| **Broken Empty / Error / Loading States** | Design dedicated empty states with clear primary action, actionable inline error recovery, and layout-matched skeletons |
| **Non-Tabular Numeric Jitter** | Apply `font-variant-numeric: tabular-nums` to prices, counts, timestamps, and metrics |
| **Overflow & Truncation Bugs** | Test long strings (`min-w-0` on flex/grid children, `overflow-wrap: anywhere`, `text-wrap: balance` on headings) |
| **Hardcoded Physical Directions** (`margin-left`, `text-align: left`) | Use CSS logical properties (`margin-inline-start`, `text-align: start`) for automatic RTL readiness |

---

## 6. Verification Checklist

- [ ] All colors, radii, spacing, and typography derive from semantic CSS tokens (OKLCH / CSS custom properties).
- [ ] Zero `!important` hacks; stylesheet uses explicit `@layer` ordering.
- [ ] Every interactive component implements all 6 states (`default`, `hover`, `focus-visible`, `active`, `disabled`, `loading/error`).
- [ ] Complex widgets (Dialog, Select, Combobox, Tabs) use vetted headless primitives with full keyboard + screen reader support.
- [ ] Responsive behavior tested at `320px`, `768px`, `1280px`, and `1920px` with zero horizontal overflow (`scrollWidth <= clientWidth`).
- [ ] Dark mode and `prefers-reduced-motion: reduce` verified visually and in automated Playwright/axe checks.
- [ ] Visual regression snapshots (Playwright `toHaveScreenshot()` or Chromatic) protect core design system primitives in CI.
