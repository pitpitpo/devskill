# 💎 SolidJS & SolidStart Fine-Grained Reactivity Guide (`frameworks/frontend/solidjs.md`)

> **Standard Identifier**: `FW-FRONTEND-SOLID-001`  
> **Framework**: SolidJS 1.9+ / SolidStart 1.x (Zero Virtual DOM, Fine-Grained Signals, Vinxi/Nitro)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-251–R-253**, **R-260**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *In SolidJS, components run **once** to construct a fine-grained reactive dependency graph — they never re-render. Never destructure `props`, never use `.map()` where `<For>` belongs, and keep reactive reads inside JSX expressions, `createMemo`, or `createEffect`.*

---

## 2. Fine-Grained Reactivity Mental Model (Solid vs. React)

| Concept | React (VDOM Re-render) | SolidJS (Compiled Fine-Grained Signals) |
|---|---|---|
| **Component Body** | Re-runs on every state change | Runs **once** on mount; only reactive DOM bindings update |
| **State Primitive** | `const [x, setX] = useState(0)` (value) | `const [x, setX] = createSignal(0)` (**getter function** `x()`) |
| **Derived Value** | `useMemo(() => ..., [deps])` | `const doubled = createMemo(() => x() * 2)` (auto-tracked) |
| **Side Effects** | `useEffect(() => ..., [deps])` | `createEffect(() => ...)` (auto-tracked; cleanup via `onCleanup`) |
| **Props Handling** | Destructuring `({ a, b })` is safe | **NEVER destructure `props`** — breaks getter reactivity; use `props.a` or `splitProps`/`mergeProps` |
| **Nested Objects** | Immutable spread updates | `createStore` + `setStore('items', i, 'done', true)` or `produce()` |

---

## 3. Production SolidJS Component & Store Patterns

```tsx
// src/components/TelemetryTable.tsx
import { For, Show, createMemo, createSignal, mergeProps, splitProps } from 'solid-js';
import { createStore, produce } from 'solid-js/store';

export interface MetricRow {
  readonly id: string;
  readonly service: string;
  latencyMs: number;
  status: 'ok' | 'degraded' | 'down';
}

interface TelemetryTableProps {
  readonly rows: readonly MetricRow[];
  readonly thresholdMs?: number;
  readonly onSelect?: (id: string) => void;
}

export function TelemetryTable(rawProps: TelemetryTableProps) {
  // ✅ Preserve reactivity: use mergeProps / splitProps instead of destructuring
  const merged = mergeProps({ thresholdMs: 200 }, rawProps);
  const [local, rest] = splitProps(merged, ['rows', 'thresholdMs']);

  const [query, setQuery] = createSignal('');
  const [pinnedIds, setPinnedIds] = createStore<Record<string, boolean>>({});

  const filtered = createMemo(() => {
    const q = query().trim().toLowerCase();
    return local.rows.filter((row) => !q || row.service.toLowerCase().includes(q));
  });

  const togglePin = (id: string) => {
    setPinnedIds(
      produce((draft) => {
        draft[id] = !draft[id];
      })
    );
  };

  return (
    <section class="space-y-3">
      <input
        type="search"
        value={query()}
        onInput={(e) => setQuery(e.currentTarget.value)}
        placeholder="Filter services..."
        aria-label="Filter services"
        class="w-full rounded-md border px-3 py-2"
      />

      <Show when={filtered().length > 0} fallback={<p class="text-sm text-slate-500">No matching services.</p>}>
        <ul class="divide-y rounded-lg border">
          {/* ✅ <For> keys by object reference so only modified DOM nodes update */}
          <For each={filtered()}>
            {(row) => (
              <li class="flex items-center justify-between p-3">
                <button type="button" onClick={() => rest.onSelect?.(row.id)} class="font-medium">
                  {row.service}
                </button>
                <div class="flex items-center gap-3 tabular-nums">
                  <span class={row.latencyMs > local.thresholdMs ? 'text-red-600 font-semibold' : 'text-slate-600'}>
                    {row.latencyMs}ms
                  </span>
                  <button type="button" onClick={() => togglePin(row.id)} aria-pressed={Boolean(pinnedIds[row.id])}>
                    {pinnedIds[row.id] ? 'Pinned' : 'Pin'}
                  </button>
                </div>
              </li>
            )}
          </For>
        </ul>
      </Show>
    </section>
  );
}
```

---

## 4. Full-Stack SolidStart (`"use server"`, `query`, `action`, `createAsync`)

```tsx
// src/routes/tasks.tsx
import { Suspense, For } from 'solid-js';
import { query, action, createAsync, type RouteDefinition } from '@solidjs/router';
import { z } from 'zod';
import { db } from '~/lib/server/db';

const createTaskSchema = z.object({ title: z.string().min(2).max(120) });

const getTasks = query(async () => {
  'use server';
  return db.task.findMany({ orderBy: { createdAt: 'desc' } });
}, 'tasks');

const addTask = action(async (formData: FormData) => {
  'use server';
  const parsed = createTaskSchema.safeParse({ title: formData.get('title') });
  if (!parsed.success) throw new Error('Invalid task title');
  await db.task.create({ data: parsed.data });
}, 'addTask');

export const route = {
  preload: () => getTasks(),
} satisfies RouteDefinition;

export default function TasksPage() {
  const tasks = createAsync(() => getTasks());

  return (
    <main class="mx-auto max-w-2xl space-y-4 p-6">
      <form action={addTask} method="post" class="flex gap-2">
        <input name="title" required class="flex-1 rounded border px-3 py-2" placeholder="New task..." />
        <button type="submit" class="rounded bg-blue-600 px-4 py-2 text-white">Add</button>
      </form>

      <Suspense fallback={<p>Loading tasks...</p>}>
        <ul class="divide-y rounded border">
          <For each={tasks()}>{(task) => <li class="p-3">{task.title}</li>}</For>
        </ul>
      </Suspense>
    </main>
  );
}
```

---

## 5. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Remediated Standard |
|---|---|---|
| **Destructuring props (`function Card({ title })`)** | Evaluates getter once during setup; freezes UI permanently | Access `props.title` inside JSX/memos, or use `splitProps` / `mergeProps` |
| **Using `array.map()` inside JSX** | Re-creates every DOM node whenever the array signal changes | Use `<For each={list()}>` (keyed by item) or `<Index each={primitives()}>` (keyed by index) |
| **Reading signals outside a tracking scope** | `const value = count()` at top of component body is static | Read `count()` inside JSX, `createMemo`, or `createEffect` |
| **Missing `onCleanup` for listeners/timers** | Memory leaks on conditional `<Show>` unmount | Register `onCleanup(() => clearInterval(id))` inside `createEffect` or component setup |
| **Missing `<ErrorBoundary>` / `<Suspense>`** | Unhandled async `createAsync` rejections crash subtree | Wrap async subtrees with `<ErrorBoundary>` and `<Suspense>` |

---

## 6. Verification Checklist

- [ ] `eslint-plugin-solid` enabled (`solid/reactivity`, `solid/no-destructure`, `solid/prefer-for`) with zero warnings.
- [ ] Zero destructured component props; `splitProps`/`mergeProps` used everywhere defaults or rest attributes are needed.
- [ ] Server-only database/secret code strictly isolated behind `"use server"` boundaries.
- [ ] Tests via `@solidjs/testing-library` + Vitest and Playwright E2E pass with Exit Code `0`.
