# 🔄 Frontend State Management Standards (`state-management.md`)

> **Classification**: Frontend Architecture & State Taxonomy  
> **Core Philosophy**: "Server State Belongs in the Cache; Client State Belongs in URL or Minimal Stores."

---

## 1. The State Taxonomy

```
                              APPLICATION STATE
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
           SERVER STATE                              CLIENT STATE
     (Asynchronous, Remote, Cache)            (Synchronous, Local, Ephemeral)
                 │                                         │
        TanStack Query / SWR                  ┌────────────┴────────────┐
                 │                            ▼                         ▼
      - Automatic caching               URL SEARCH PARAMS         UI STORES
      - Background revalidation        (Shareable state)        (Zustand / Jotai)
      - Deduping requests               - Pagination             - Sidebar open/closed
      - Optimistic updates              - Active filters         - Modal visibility
                                        - Sort order             - Local drafts
```

---

## 2. TanStack Query Standards

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchUserProjects, createProject } from '@/api/projects';

// Query Keys must be structured as hierarchical tuples
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: { status?: string }) => [...projectKeys.lists(), { filters }] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
};

export function useProjects(status?: string) {
  return useQuery({
    queryKey: projectKeys.list({ status }),
    queryFn: () => fetchUserProjects(status),
    staleTime: 1000 * 60 * 5, // Data fresh for 5 minutes (no background refetch)
    gcTime: 1000 * 60 * 30,    // Keep unused data in garbage collector for 30 min
  });
}
```

---

## 3. Zustand for Client-Only UI State

```typescript
import { create } from 'zustand';

interface UIState {
  isSidebarOpen: boolean;
  activeModal: string | null;
  toggleSidebar: () => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  activeModal: null,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  openModal: (modalId) => set({ activeModal: modalId }),
  closeModal: () => set({ activeModal: null }),
}));
```
