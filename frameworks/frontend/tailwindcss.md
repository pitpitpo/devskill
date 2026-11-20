# 🎨 Tailwind CSS v4 (Oxide Engine) & Semantic Design Token Architecture (`frameworks/frontend/tailwindcss.md`)

> **Standard Identifier**: `FW-FRONTEND-TAILWIND-001`  
> **Framework**: Tailwind CSS v4+ (Rust Oxide Engine, CSS-First `@theme`, Native Container Queries)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-251**, **R-252**, **R-259**  
> **Last Updated**: 2026-11-19

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Tailwind CSS v4 moves configuration out of JavaScript (`tailwind.config.ts`) into standard CSS (`@import "tailwindcss";` + `@theme`). Pair CSS-first OKLCH semantic design tokens with `cva` (class-variance-authority) and `cn()` (`tailwind-merge` v3 + `clsx`) so utility-first styling scales cleanly without class soup or arbitrary pixel drift.*

### What Changed in Tailwind CSS v4 (Oxide Engine)
- **CSS-First Setup**: Single `@import "tailwindcss";` replaces `@tailwind base/components/utilities;` and `tailwind.config.js`.
- **Automatic Content Detection**: Oxide automatically discovers templates (respecting `.gitignore`); use `@source "../packages/ui";` only for external monorepo directories.
- **Native Modern CSS**: Built-in `@container` queries (`@container`, `@md:grid-cols-2`), `@starting-style` (`starting:opacity-0`), OKLCH color palette, 3D transforms, and CSS Cascade Layers (`@layer theme, base, components, utilities`).
- **First-Party Vite Plugin**: Prefer `@tailwindcss/vite` (or `@tailwindcss/postcss` for Next.js/webpack) for millisecond incremental rebuilds.

---

## 2. CSS-First Semantic Design Tokens (`src/styles/app.css`)

```css
@import "tailwindcss";

/* Optional: class-based dark mode toggle (default is prefers-color-scheme) */
@custom-variant dark (&:where(.dark, .dark *));

/* Semantic CSS custom properties (OKLCH for uniform perceptual contrast) */
:root {
  --surface-canvas:     oklch(0.988 0.003 250);
  --surface-elevated:   oklch(1.000 0.000 0);
  --text-primary:       oklch(0.175 0.014 255);
  --text-muted:         oklch(0.460 0.015 255);
  --border-subtle:      oklch(0.895 0.008 250);
  --accent-primary:     oklch(0.540 0.195 258);
  --accent-foreground:  oklch(0.990 0.002 250);
  --danger-primary:     oklch(0.560 0.215 27);
  --danger-foreground:  oklch(0.990 0.002 250);
}

.dark {
  --surface-canvas:     oklch(0.145 0.010 255);
  --surface-elevated:   oklch(0.190 0.012 255);
  --text-primary:       oklch(0.955 0.006 250);
  --text-muted:         oklch(0.700 0.012 255);
  --border-subtle:      oklch(0.285 0.014 255);
  --accent-primary:     oklch(0.680 0.170 258);
  --accent-foreground:  oklch(0.145 0.010 255);
}

/* Expose tokens as first-class Tailwind v4 utilities (bg-canvas, text-ink, border-subtle, etc.) */
@theme inline {
  --color-canvas:            var(--surface-canvas);
  --color-elevated:          var(--surface-elevated);
  --color-ink:               var(--text-primary);
  --color-ink-muted:         var(--text-muted);
  --color-subtle:            var(--border-subtle);
  --color-primary:           var(--accent-primary);
  --color-primary-fg:        var(--accent-foreground);
  --color-destructive:       var(--danger-primary);
  --color-destructive-fg:    var(--danger-foreground);

  --font-sans: "Inter Variable", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --radius-control: 0.5rem;
}

/* Custom reusable utility */
@utility focus-ring {
  @apply focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary;
}
```

---

## 3. Component Variant Architecture (`cva` + `tailwind-merge` v3)

```typescript
// src/lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge'; // Use tailwind-merge >= 3.0 for Tailwind v4

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

```tsx
// src/components/ui/Button.tsx (React 19 — no forwardRef required)
import type { ComponentPropsWithRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-(--radius-control) text-sm font-medium transition-colors focus-ring disabled:pointer-events-none disabled:opacity-50 select-none',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-fg hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-fg hover:bg-destructive/90',
        outline: 'border border-subtle bg-elevated text-ink hover:bg-canvas',
        ghost: 'text-ink hover:bg-canvas',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4',
        lg: 'h-11 px-6 text-base',
        icon: 'size-10 p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends ComponentPropsWithRef<'button'>,
    VariantProps<typeof buttonVariants> {
  readonly isLoading?: boolean;
}

export function Button({
  className,
  variant,
  size,
  isLoading = false,
  disabled,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      aria-busy={isLoading || undefined}
      disabled={disabled || isLoading}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    >
      {children}
    </button>
  );
}
```

---

## 4. Built-In Container Queries, RTL Logical Properties & v3 → v4 Migration

- **Native Container Queries**: Wrap cards/widgets in `@container` and style child breakpoints with `@sm:flex-row @lg:grid-cols-3` — zero extra plugins required in v4.
- **Logical Properties for RTL**: Prefer `ps-4`, `pe-4`, `ms-auto`, `me-2`, `text-start`, `border-s` over physical `pl-`, `pr-`, `ml-`, `mr-`, `text-left`.
- **Key v3 → v4 Breaking Changes to Catch**:
  - `border` default color changed from `gray-200` to `currentColor` — always specify `border-subtle` explicitly.
  - `ring` default width changed from `3px` to `1px` — use `ring-2` or `outline-2` explicitly.
  - Renamed utilities: `shadow-sm` → `shadow-xs`, `rounded-sm` → `rounded-xs`, `bg-opacity-*` → `bg-primary/50`, `outline-none` → `outline-hidden`.
  - CSS variable shorthand: `bg-[--my-var]` → `bg-(--my-var)`.

---

## 5. Security & Performance Considerations

| Area | Focus | Standard Guideline |
|---|---|---|
| **Static Extraction** | Purging & Bundle Size | Never construct dynamic class names with template interpolation (`bg-${color}-500`); use explicit static lookup maps |
| **Specificity Collisions** | Visual Regression | Always merge caller `className` overrides through `cn()` (`tailwind-merge` v3 + `clsx`) |
| **CSS Injection** | Untrusted User Input | Never pass user-supplied strings directly into `class` or inline `style` attributes |
| **Paint & Composite Cost** | Smooth 60/120fps | Avoid animating `width`/`height`/`top`; restrict transitions to `transform` and `opacity`; limit stacked `backdrop-blur-*` layers |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Remediated Standard |
|---|---|---|
| **Mixing `tailwind.config.js` with v4 `@theme`** | Partial migration drift | Consolidate all tokens in `@theme` inside your CSS entrypoint |
| **Dynamic string interpolation (`text-${status}-600`)** | Oxide scanner only extracts statically visible strings | Use a typed map: `{ ok: 'text-emerald-600', error: 'text-red-600' }` |
| **Arbitrary value proliferation (`w-[347px] mt-[13px]`)** | Bypassing the spacing/type scale | Enforce theme tokens and standard 4px scale steps |
| **Using `tailwind-merge` v2 with Tailwind v4** | New v4 utilities fail to deduplicate | Upgrade to `tailwind-merge >= 3.0` |

---

## 7. Verification Checklist & Production Audit

- [ ] Entry stylesheet uses `@import "tailwindcss";` and `@theme inline` semantic tokens (OKLCH).
- [ ] All reusable primitives use `cva` + `cn()` (`tailwind-merge` v3 + `clsx`).
- [ ] Zero dynamic template-interpolated utility classes (`bg-${x}-500`).
- [ ] Logical properties (`ps-*`, `ms-*`, `text-start`) used for RTL compatibility.
- [ ] Dark mode and high-contrast focus rings (`focus-visible`) verified on all interactive elements.
- [ ] Single minified production CSS bundle generated with zero unused utility bloat.
