# 🧡 Svelte 5 Runes & SvelteKit 2 Full-Stack Production Architecture (`frameworks/frontend/sveltekit.md`)

> **Standard Identifier**: `FW-FRONTEND-SVELTE-001`  
> **Framework**: Svelte 5 (Runes + Snippets) & SvelteKit 2+  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-251–R-253**, **R-260**  
> **Last Updated**: 2026-11-19

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Svelte 5 compiles declarative components into surgical, zero-VDOM DOM updates powered by universal signal-based Runes (`$state`, `$derived`, `$effect`, `$props`). Combine Svelte 5 Runes and Snippets with SvelteKit 2 Server Loaders, Form Actions (`use:enhance`), and request-scoped `event.locals` for ultra-fast, progressively enhanced full-stack applications.*

---

## 2. Svelte 5 Runes & Modern Syntax Reference

| Rune / Feature | Purpose | Notes & Guardrails |
|---|---|---|
| **`$state(initial)`** | Deeply reactive fine-grained state | Works in `.svelte` AND plain `.svelte.ts` modules |
| **`$state.raw(initial)`** | Shallow reactive state (no deep proxy) | Use for large immutable arrays/API payloads (faster, lower memory) |
| **`$state.snapshot(val)`** | Plain non-proxied clone | Required before passing reactive objects to `structuredClone`, `postMessage`, or external SDKs |
| **`$derived(expr)` / `$derived.by(fn)`** | Lazily computed memoized value | Always prefer over `$effect` for computing values from state |
| **`$effect(() => { ... return cleanup })`** | Post-DOM side effects (auto-tracked) | Strictly for DOM sync, timers, subscriptions — never for syncing state |
| **`$props()` & `$bindable()`** | Typed component inputs & explicit two-way bindings | Replaces legacy `export let` |
| **`{#snippet name(args)} ... {@render name(args)}`** | Composable typed template fragments | Replaces legacy `<slot>` and `let:` directives |
| **`onclick={handler}`** | Standard HTML DOM event attributes | Replaces legacy `on:click` directive |

---

## 3. Universal Reactivity in `.svelte.ts` Modules

Never share mutable module-level `$state` singletons across SSR requests on the server. Instantiate reactive state classes inside Svelte context (`setContext`/`getContext`) so every SSR request stays strictly isolated:

```typescript
// src/lib/state/filter-state.svelte.ts
export class FilterState {
  search = $state('');
  priority = $state<'ALL' | 'LOW' | 'MEDIUM' | 'HIGH'>('ALL');

  readonly isFiltered = $derived(this.search.trim().length > 0 || this.priority !== 'ALL');

  reset(): void {
    this.search = '';
    this.priority = 'ALL';
  }
}
```

---

## 4. Production SvelteKit 2 Full-Stack Implementation

### 4.1 Request Auth & Security Hook (`src/hooks.server.ts`)
```typescript
import type { Handle } from '@sveltejs/kit';
import { verifySessionCookie } from '$lib/server/auth';

export const handle: Handle = async ({ event, resolve }) => {
  const sessionToken = event.cookies.get('session');
  event.locals.user = sessionToken ? await verifySessionCookie(sessionToken) : null;

  const response = await resolve(event);
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  return response;
};
```

### 4.2 Server Loader (with Streaming) & Form Actions (`src/routes/items/+page.server.ts`)
```typescript
import { error, fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { db } from '$lib/server/db';
import { z } from 'zod';

const createItemSchema = z.object({
  title: z.string().trim().min(3, 'Title must be at least 3 characters').max(100),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH']),
});

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) throw redirect(303, '/login');

  // Critical data awaited for SSR; non-critical analytics streamed asynchronously
  const items = await db.item.findMany({
    where: { tenantId: locals.user.tenantId },
    orderBy: { createdAt: 'desc' },
  });

  return {
    items,
    streamedSummary: db.item.count({ where: { tenantId: locals.user.tenantId } }),
  };
};

export const actions: Actions = {
  create: async ({ request, locals }) => {
    if (!locals.user) throw error(401, 'Unauthorized');

    const formData = await request.formData();
    const raw = {
      title: String(formData.get('title') ?? ''),
      priority: String(formData.get('priority') ?? 'MEDIUM'),
    };
    const parsed = createItemSchema.safeParse(raw);

    if (!parsed.success) {
      return fail(400, {
        errors: parsed.error.flatten().fieldErrors,
        values: raw,
      });
    }

    try {
      await db.item.create({
        data: { ...parsed.data, tenantId: locals.user.tenantId },
      });
      return { success: true };
    } catch (err: unknown) {
      console.error('Failed to create item', err);
      return fail(500, { message: 'Database transaction failed' });
    }
  },
};
```

### 4.3 Svelte 5 Component with Runes, Snippets & `use:enhance` (`src/routes/items/+page.svelte`)
```svelte
<script lang="ts">
  import { enhance } from '$app/forms';
  import type { PageProps } from './$types';

  let { data, form }: PageProps = $props();

  let search = $state('');
  let isSubmitting = $state(false);

  const filteredItems = $derived(
    data.items.filter((item) => item.title.toLowerCase().includes(search.trim().toLowerCase()))
  );
</script>

{#snippet priorityBadge(priority: 'LOW' | 'MEDIUM' | 'HIGH')}
  <span class="rounded px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-700">
    {priority}
  </span>
{/snippet}

<main class="mx-auto max-w-2xl space-y-6 p-6">
  <header class="flex items-baseline justify-between">
    <h1 class="text-2xl font-bold">Project Items</h1>
    {#await data.streamedSummary then total}
      <span class="text-sm text-slate-500 tabular-nums">{total} total</span>
    {/await}
  </header>

  <form
    method="POST"
    action="?/create"
    use:enhance={() => {
      isSubmitting = true;
      return async ({ update }) => {
        await update();
        isSubmitting = false;
      };
    }}
    class="space-y-4 rounded-lg border p-4"
  >
    <div>
      <label for="title" class="block text-sm font-medium">Title</label>
      <input
        id="title"
        name="title"
        value={form?.values?.title ?? ''}
        required
        aria-invalid={Boolean(form?.errors?.title)}
        class="mt-1 w-full rounded border px-3 py-2"
      />
      {#if form?.errors?.title}
        <p role="alert" class="mt-1 text-sm text-red-600">{form.errors.title[0]}</p>
      {/if}
    </div>

    <select name="priority" aria-label="Priority" class="rounded border px-3 py-2">
      <option value="LOW">Low</option>
      <option value="MEDIUM" selected>Medium</option>
      <option value="HIGH">High</option>
    </select>

    <button
      type="submit"
      disabled={isSubmitting}
      class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
    >
      {isSubmitting ? 'Adding...' : 'Add Item'}
    </button>
  </form>

  <input
    type="search"
    bind:value={search}
    placeholder="Filter items..."
    aria-label="Filter items"
    class="w-full rounded border px-3 py-2"
  />

  <ul class="divide-y rounded-lg border">
    {#each filteredItems as item (item.id)}
      <li class="flex items-center justify-between p-3">
        <span>{item.title}</span>
        {@render priorityBadge(item.priority)}
      </li>
    {:else}
      <li class="p-4 text-center text-slate-500">No matching items found.</li>
    {/each}
  </ul>
</main>
```

---

## 5. Security & Performance Considerations

| Dimension | Risk / Vector | Mitigation Protocol |
|---|---|---|
| **Secret Exposure** | Leaking private API keys to browser | Import secrets strictly from `$env/static/private` or `$env/dynamic/private` |
| **Action CSRF** | Cross-Site Request Forgery | SvelteKit enforces origin verification by default; never disable `csrf.checkOrigin` |
| **SSR Cross-User State Leak** | Module-scoped `$state` or writable store on server | Keep per-request data strictly in `event.locals` and `setContext()` per component tree |
| **XSS via `{@html}`** | Unsanitized user markup | Sanitize with DOMPurify before `{@html}`; prefer plain text interpolation |
| **Large Proxy Overhead** | Deep proxying 10,000+ table rows with `$state` | Use `$state.raw()` for large immutable lists/datasets |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Remediated Standard |
|---|---|---|
| **Using `$effect` to compute derived values** | Carrying over React `useEffect` habits | Replace with `$derived(...)` or `$derived.by(...)` |
| **Mixing Svelte 4 (`export let`, `$:`, `on:click`, `<slot>`) with Svelte 5 Runes** | Partial migration syntax drift | Standardize on Runes (`$props`, `$derived`, `onclick`, `{#snippet}`/`{@render}`) |
| **Shared global state in `+page.server.ts`** | Module-level `let currentUser` | Store request-scoped auth and tenant state strictly in `event.locals` |
| **Catching `redirect()` or `error()` inside `try/catch`** | Swallowing SvelteKit control-flow throws | Check `isRedirect(err)` / `isHttpError(err)` or place `throw redirect(...)` outside `try` |

---

## 7. Verification Checklist & Production Audit

- [ ] `svelte-check --tsconfig ./tsconfig.json` exits with `0` errors and `0` warnings.
- [ ] Zero legacy Svelte 4 reactive labels (`$:`) or untyped `any` catches in new code.
- [ ] All forms use progressive `<form method="POST">` + `use:enhance` + server-side Zod validation returning `fail(...)`.
- [ ] Private credentials imported exclusively via `$env/*/private`; zero SSR module-scoped user singletons.
- [ ] Production adapter configured (`@sveltejs/adapter-node`, `adapter-cloudflare`, or `adapter-vercel`).
- [ ] Vitest component tests (`@testing-library/svelte`) and Playwright E2E journeys pass with Exit Code `0`.
