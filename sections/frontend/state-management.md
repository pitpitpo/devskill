# 🌐 Modern Frontend State Management Architecture

> **Standard Identifier**: `SEC-FRONTEND-STATE-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Frontend Architects, React / Next.js Engineers  
> **Classification**: Level 4 Frontend Engineering Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Distinguish rigorously between Server State and Client State. Server State is an asynchronous, remotely owned cache requiring deduplication and invalidation (TanStack Query). Client State is ephemeral, local, user-interface state (Zustand / Jotai). Never store remote API responses in global client stores.*

Legacy web applications stored everything in monolithic Redux stores, resulting in thousands of lines of boilerplate reducers, missing cache invalidation, out-of-date data, and complex synchronization bugs. Modern frontend engineering partitions state strictly by origin and lifecycle.

---

## 2. Frontend State Taxonomy

```
                   ┌────────────────────────────────────────────────────────┐
                   │                 FRONTEND STATE TAXONOMY                │
                   └──────────────────────────┬─────────────────────────────┘
                                              │
         ┌────────────────────────────────────┴────────────────────────────────────┐
         ▼                                                                         ▼
  ┌──────────────┐                                                          ┌──────────────┐
  │ SERVER STATE │                                                          │ CLIENT STATE │
  │ (Remote/Async│                                                          │ (Local/Sync) │
  ├──────────────┤                                                          ├──────────────┤
  │ Owned by DB  │                                                          │ Owned by UI  │
  │ • Stale-time │                                                          │ • Modal open │
  │ • Cache tags │                                                          │ • Form draft │
  │ • Retries    │                                                          │ • Dark mode  │
  ├──────────────┤                                                          ├──────────────┤
  │ Standard:    │                                                          │ Standard:    │
  │ TanStack Qry │                                                          │ Zustand      │
  └──────────────┘                                                          └──────────────┘
```

---

## 3. Server State Architecture: TanStack Query (React Query)

### 3.1 Query Key Factory Pattern
Query keys must be deterministic and centralized to prevent cache collisions and accidental invalidations:

```typescript
// features/orders/keys.ts
export const orderKeys = {
  all: ["orders"] as const,
  lists: () => [...orderKeys.all, "list"] as const,
  list: (filters: OrderFilters) => [...orderKeys.lists(), filters] as const,
  details: () => [...orderKeys.all, "detail"] as const,
  detail: (id: string) => [...orderKeys.details(), id] as const,
};
```

### 3.2 Optimistic Updates Implementation
```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { orderKeys } from "./keys";

export function useUpdateOrderStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ orderId, status }: { orderId: string; status: string }) => {
      const res = await fetch(`/api/orders/${orderId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      return res.json();
    },
    // Optimistic Update: Modify cache immediately before network completes
    onMutate: async ({ orderId, status }) => {
      await queryClient.cancelQueries({ queryKey: orderKeys.detail(orderId) });
      const previousOrder = queryClient.getQueryData(orderKeys.detail(orderId));

      queryClient.setQueryData<Order | undefined>(orderKeys.detail(orderId), (old) =>
        old ? { ...old, status } : old
      );

      return { previousOrder, orderId };
    },
    // Rollback if network fails
    onError: (_err, _vars, context) => {
      if (context?.previousOrder) {
        queryClient.setQueryData(
          orderKeys.detail(context.orderId),
          context.previousOrder
        );
      }
    },
    // Invalidate to guarantee synchronization with DB
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: orderKeys.detail(variables.orderId) });
    },
  });
}
```

---

## 4. Global Client State Architecture: Zustand, Pinia & Signals

When state is strictly ephemeral and shared across multiple UI components (e.g., active modal state, user preferences, sidebar collapse):

- **React / Next.js**: Zustand (with atomic selectors) or Jotai.
- **Vue / Nuxt**: Pinia Setup Stores (`defineStore`).
- **Svelte 5**: Shared `.svelte.ts` Runes classes/modules (`$state` / `$derived`).
- **Angular 19/20**: NgRx SignalStore (`signalStore`, `withState`, `withComputed`, `withMethods`).
- **SolidJS**: `createStore` with `produce` / `reconcile`.
- **URL State (All Frameworks)**: Keep search filters, sort order, pagination, and active tab in URL query parameters (`nuqs`, router search params) so state survives reloads and link sharing.

```typescript
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface UIState {
  isSidebarOpen: boolean;
  theme: "light" | "dark" | "system";
  toggleSidebar: () => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set) => ({
        isSidebarOpen: true,
        theme: "system",
        toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
        setTheme: (theme) => set({ theme }),
      }),
      { name: "ui-preferences-storage" }
    )
  )
);
```

---

## 5. Security & Performance Considerations

| Area | Focus | Standard Guideline |
| :--- | :--- | :--- |
| **Sensitive State Storage** | Token Protection | Never persist authentication tokens or PII in unencrypted `localStorage` |
| **Selector Subscriptions** | Render Performance | Always pass atomic selector functions (`useStore(s => s.item)`) to prevent full-tree re-renders |
| **Query Deduplication** | Network Saturation | Configure `staleTime: 60000` to prevent redundant network fetches on tab focus |
| **SSR Store Isolation** | Multi-User Leaks | Never use module-scoped singleton client stores on the server; create per-request instances |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Duplicating Server Data in Client Store** | Copying TanStack Query data into Zustand/Pinia | Out-of-sync state, double rendering, cache invalidation bugs | Read directly from server cache; use client store only for UI state |
| **Missing Selector Optimization** | Calling `const store = useStore()` | Component re-renders on ANY store update, even unrelated fields | Use precise selectors: `const isSidebarOpen = useStore(s => s.isSidebarOpen)` |
| **Zero Stale-Time Default** | Leaving `staleTime: 0` in TanStack Query | Unnecessary network requests triggered on every window focus | Set default `staleTime` to at least 30–60 seconds for general resources |
| **Effect-Synced Derived State** | Using `useEffect`/`watch` to mirror state into another state | Extra render pass, race conditions, stale intermediate frames | Compute derived values directly (`computed`, `$derived`, `createMemo`) |

---

## 7. Verification Checklist & Production Audit

- [ ] All remote server data is managed via server cache (TanStack Query / framework loaders); no API data duplicated in client stores.
- [ ] Query keys use the centralized Query Key Factory (`queryOptions`) pattern.
- [ ] Mutations with user-visible effects employ optimistic updates with rollback guards.
- [ ] Filters, pagination, and sort order are persisted in URL search parameters.
- [ ] State selector hooks (`useUIStore(state => state.isSidebarOpen)`) prevent unnecessary re-renders.
- [ ] Zero SSR module-level singleton stores leaking state across requests.
