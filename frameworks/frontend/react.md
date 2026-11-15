# ⚛️ React Production Guide (`react.md`)

> **Framework**: React 18 / 19
> **Classification**: Core Frontend Component Architecture
> **Core Philosophy**: "UI is a Pure Function of State; Minimize Renders, Maximize Predictability."

---

## 1. Overview & When to Use

React is the dominant UI library for building component-based user interfaces. Use React when:

- Building single-page applications (SPAs) or interactive dashboards
- You need a rich ecosystem of libraries (routing, state, forms, animations)
- Server-side rendering or static generation is required (via Next.js, Remix, or Astro)
- The team needs strong TypeScript support and component-level isolation

**Do NOT use React** for static marketing pages with no interactivity (use Astro or plain HTML), extremely small widgets where the 40KB runtime is unjustified, or performance-critical canvas/WebGL applications where direct DOM manipulation is required.

---

## 2. Core Concepts & Architecture

### Component Hierarchy Patterns

```
┌──────────────────────────────────────────────────┐
│                  App Shell                       │
│  ┌────────────────┐  ┌────────────────────────┐  │
│  │  Sidebar       │  │   Main Content         │  │
│  │  (Server Comp) │  │   ┌──────────────────┐ │  │
│  │                │  │   │  Feature Module   │ │  │
│  │                │  │   │  ┌──────────────┐ │ │  │
│  │                │  │   │  │ Client Comp  │ │ │  │
│  │                │  │   │  │ (interactive)│ │ │  │
│  │                │  │   │  └──────────────┘ │ │  │
│  │                │  │   └──────────────────┘ │  │
│  └────────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Compound Component Pattern

Use compound components when a group of components share implicit state and must work together as a unit (tabs, accordions, dropdown menus):

```typescript
import React, { createContext, useContext, useState, ReactNode } from 'react';

// 1. Shared context
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('Tab components must be used within <Tabs>');
  return ctx;
}

// 2. Root component owns the state
interface TabsProps {
  defaultTab: string;
  children: ReactNode;
  onChange?: (tab: string) => void;
}

export function Tabs({ defaultTab, children, onChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  const handleSetTab = (tab: string) => {
    setActiveTab(tab);
    onChange?.(tab);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleSetTab }}>
      <div role="tablist">{children}</div>
    </TabsContext.Provider>
  );
}

// 3. Child components consume context
export function TabTrigger({ value, children }: { value: string; children: ReactNode }) {
  const { activeTab, setActiveTab } = useTabsContext();
  return (
    <button
      role="tab"
      aria-selected={activeTab === value}
      onClick={() => setActiveTab(value)}
      className={activeTab === value ? 'border-b-2 border-blue-500 font-semibold' : ''}
    >
      {children}
    </button>
  );
}

export function TabContent({ value, children }: { value: string; children: ReactNode }) {
  const { activeTab } = useTabsContext();
  if (activeTab !== value) return null;
  return <div role="tabpanel">{children}</div>;
}

// Usage:
// <Tabs defaultTab="overview">
//   <TabTrigger value="overview">Overview</TabTrigger>
//   <TabTrigger value="settings">Settings</TabTrigger>
//   <TabContent value="overview"><OverviewPanel /></TabContent>
//   <TabContent value="settings"><SettingsPanel /></TabContent>
// </Tabs>
```

### Render Props Pattern

Use render props when a component needs to expose internal state or behavior to a consumer without dictating the rendered output:

```typescript
interface MouseTrackerProps {
  children: (position: { x: number; y: number }) => ReactNode;
}

function MouseTracker({ children }: MouseTrackerProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  return (
    <div onMouseMove={(e) => setPosition({ x: e.clientX, y: e.clientY })}>
      {children(position)}
    </div>
  );
}

// Usage:
// <MouseTracker>
//   {({ x, y }) => <Tooltip style={{ left: x, top: y }}>Cursor here</Tooltip>}
// </MouseTracker>
```

### Higher-Order Components (HOCs) — Legacy but Still Relevant

HOCs wrap a component to inject cross-cutting behavior. Prefer hooks for new code, but understand HOCs for existing codebases:

```typescript
function withAuth<P extends object>(WrappedComponent: React.ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { user, isLoading } = useAuth();

    if (isLoading) return <Skeleton />;
    if (!user) return <Navigate to="/login" />;

    return <WrappedComponent {...props} />;
  };
}

// Usage: export default withAuth(DashboardPage);
```

> **Rule**: In new code, replace HOCs with custom hooks + wrapper components. HOCs obscure prop origins and break TypeScript inference.

---

## 3. Hooks Deep Dive

### Rules of Hooks (Non-Negotiable)

1. **Only call hooks at the top level** — never inside conditions, loops, or nested functions.
2. **Only call hooks from React function components or custom hooks** — never from plain JS functions.
3. **Custom hooks must start with `use`** — this enables the linter to enforce rule 1 and 2.

### Essential Custom Hook Patterns

#### Debounced Value Hook

```typescript
import { useState, useEffect } from 'react';

export function useDebouncedValue<T>(value: T, delayMs: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debouncedValue;
}
```

#### Media Query Hook

```typescript
import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}

// Usage: const isMobile = useMediaQuery('(max-width: 768px)');
```

#### Previous Value Hook

```typescript
import { useRef, useEffect } from 'react';

export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);

  useEffect(() => {
    ref.current = value;
  });

  return ref.current;
}
```

#### Local Storage Hook with SSR Safety

```typescript
import { useState, useEffect, useCallback } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue((prev) => {
        const newValue = value instanceof Function ? value(prev) : value;
        window.localStorage.setItem(key, JSON.stringify(newValue));
        return newValue;
      });
    },
    [key]
  );

  return [storedValue, setValue] as const;
}
```

---

## 4. State Management Decision Matrix

| Scenario | Recommended Tool | Rationale |
|---|---|---|
| Local component UI state (modals, toggles) | `useState` / `useReducer` | No external library needed |
| Shared client state (theme, sidebar, auth) | **Zustand** | Tiny (1KB), no providers, selector-based re-renders |
| Atomic/fine-grained state (forms, filters) | **Jotai** | Bottom-up atoms, excellent for derived state |
| Server/async state (API data, caching) | **TanStack Query** | Handles caching, deduplication, background refetch |
| Complex domain state with middleware | **Zustand + Immer middleware** | Immutable updates without spread hell |
| Global state passed through tree | `React Context` | Only for infrequently changing values (theme, locale) |

### Zustand — Production Store Pattern

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      immer((set) => ({
        user: null,
        token: null,
        isAuthenticated: false,

        login: async (credentials) => {
          const { user, token } = await api.login(credentials);
          set((state) => {
            state.user = user;
            state.token = token;
            state.isAuthenticated = true;
          });
        },

        logout: () => {
          set((state) => {
            state.user = null;
            state.token = null;
            state.isAuthenticated = false;
          });
        },
      })),
      { name: 'auth-storage' }
    ),
    { name: 'AuthStore' }
  )
);

// Selector pattern — component only re-renders when selected slice changes
function UserAvatar() {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;
  return <img src={user.avatarUrl} alt={user.name} />;
}
```

### TanStack Query — Server State Management

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Query keys factory — prevents key collisions
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: ProjectFilters) => [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
};

// Query hook
export function useProjects(filters: ProjectFilters) {
  return useQuery({
    queryKey: projectKeys.list(filters),
    queryFn: () => api.getProjects(filters),
    staleTime: 5 * 60 * 1000,       // 5 minutes before refetch
    gcTime: 30 * 60 * 1000,         // 30 minutes in garbage collection
    placeholderData: keepPreviousData, // Keep old data while fetching new
  });
}

// Mutation with optimistic update
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deleteProject(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: projectKeys.lists() });
      const previous = queryClient.getQueryData(projectKeys.lists());

      queryClient.setQueriesData(
        { queryKey: projectKeys.lists() },
        (old: Project[] | undefined) => old?.filter((p) => p.id !== id) ?? []
      );

      return { previous };
    },
    onError: (_err, _id, context) => {
      queryClient.setQueriesData(
        { queryKey: projectKeys.lists() },
        context?.previous
      );
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
}
```

---

## 5. React 19 Features

### Server Components

Server Components run exclusively on the server, producing zero client-side JavaScript. Use them for data fetching, database access, and heavy dependencies:

```typescript
// This component ships ZERO JS to the browser
async function ProjectList() {
  const projects = await db.project.findMany({
    orderBy: { createdAt: 'desc' },
    take: 20,
  });

  return (
    <ul>
      {projects.map((project) => (
        <li key={project.id}>
          <h3>{project.name}</h3>
          <p>{project.description}</p>
          {/* Client component only where interactivity is needed */}
          <DeleteButton projectId={project.id} />
        </li>
      ))}
    </ul>
  );
}
```

### Server Actions

```typescript
// actions.ts
'use server';

import { revalidatePath } from 'next/cache';

export async function addToCart(productId: string) {
  await db.cart.add({ productId, userId: await getCurrentUserId() });
  revalidatePath('/cart');
}
```

### The `use` Hook

React 19 introduces `use()` for reading promises and context within render:

```typescript
import { use, Suspense } from 'react';

// use() can read a promise directly in render
function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise);
  return (
    <ul>
      {comments.map((c) => <li key={c.id}>{c.body}</li>)}
    </ul>
  );
}

// Parent creates the promise, child reads it
function PostPage({ postId }: { postId: string }) {
  const commentsPromise = fetchComments(postId); // Start fetching immediately

  return (
    <article>
      <PostContent id={postId} />
      <Suspense fallback={<CommentsSkeleton />}>
        <Comments commentsPromise={commentsPromise} />
      </Suspense>
    </article>
  );
}
```

### `useActionState` (replaces `useFormState`)

```typescript
'use client';

import { useActionState } from 'react';
import { createProjectAction, type ActionState } from '@/app/actions';

const initialState: ActionState = { success: false };

export function CreateProjectForm() {
  const [state, formAction, isPending] = useActionState(createProjectAction, initialState);

  return (
    <form action={formAction}>
      <input name="name" required minLength={3} />
      {state.errors?.name && <p className="text-red-500">{state.errors.name[0]}</p>}

      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create Project'}
      </button>

      {state.success && <p className="text-green-600">Project created!</p>}
    </form>
  );
}
```

### `useOptimistic`

```typescript
'use client';

import { useOptimistic } from 'react';

function TodoList({ todos, addTodoAction }: Props) {
  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    todos,
    (state, newTodo: string) => [
      ...state,
      { id: `temp-${Date.now()}`, text: newTodo, pending: true },
    ]
  );

  return (
    <form action={async (formData) => {
      const text = formData.get('text') as string;
      addOptimisticTodo(text);
      await addTodoAction(text);
    }}>
      <input name="text" required />
      <button type="submit">Add</button>
      <ul>
        {optimisticTodos.map((todo) => (
          <li key={todo.id} className={todo.pending ? 'opacity-50' : ''}>
            {todo.text}
          </li>
        ))}
      </ul>
    </form>
  );
}
```

---

## 6. Concurrency & Non-Blocking Transitions

React 18+ introduces concurrent rendering to keep user input responsive during expensive renders.

```typescript
import React, { useState, useTransition } from 'react';

export function SearchCatalog({ items }: { items: string[] }) {
  const [query, setQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);
  const [isPending, startTransition] = useTransition();

  function handleSearch(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    // 1. High-priority immediate update (input stays responsive)
    setQuery(value);

    // 2. Low-priority transition (heavy filtering deferred)
    startTransition(() => {
      const results = items.filter((item) =>
        item.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredItems(results);
    });
  }

  return (
    <div className="space-y-4">
      <input
        type="text"
        value={query}
        onChange={handleSearch}
        placeholder="Filter catalog..."
        className="border p-2 rounded w-full"
      />
      {isPending && <p className="text-sm text-gray-500">Updating list...</p>}
      <ul className="divide-y">
        {filteredItems.map((item) => (
          <li key={item} className="py-1">{item}</li>
        ))}
      </ul>
    </div>
  );
}
```

### `useDeferredValue` — For Deferred Expensive Renders

```typescript
import { useDeferredValue, memo } from 'react';

function SearchResults({ query }: { query: string }) {
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <div className={isStale ? 'opacity-60' : ''}>
      <HeavyResultsList query={deferredQuery} />
    </div>
  );
}

// Only re-renders when deferredQuery actually changes
const HeavyResultsList = memo(function HeavyResultsList({ query }: { query: string }) {
  const results = computeExpensiveSearch(query);
  return <ul>{results.map((r) => <li key={r.id}>{r.title}</li>)}</ul>;
});
```

---

## 7. Performance Optimization

### Memoization Decision Table

| Technique | When to Use | When NOT to Use |
|---|---|---|
| `React.memo` | Heavy components re-rendering frequently with identical props | Lightweight leaf components with cheap JSX |
| `useMemo` | Expensive calculations (>1,000 array iterations, complex parsing) | Simple calculations (`a + b`, short filters) |
| `useCallback` | Callbacks passed to memoized children or hook dependencies | Standard handlers on native elements (`<button onClick>`) |

### Code Splitting with `React.lazy` and `Suspense`

```typescript
import React, { lazy, Suspense } from 'react';

// Split heavy components into separate chunks
const AdminDashboard = lazy(() => import('./AdminDashboard'));
const AnalyticsChart = lazy(() => import('./AnalyticsChart'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/analytics" element={<AnalyticsChart />} />
      </Routes>
    </Suspense>
  );
}
```

### Virtualized Lists for Large Data Sets

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

function VirtualizedList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50, // estimated row height in px
    overscan: 5,            // render 5 extra items outside viewport
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              transform: `translateY(${virtualItem.start}px)`,
              height: `${virtualItem.size}px`,
              width: '100%',
            }}
          >
            <ItemRow item={items[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 8. Forms — React Hook Form + Zod

### Production Form Pattern

```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email('Invalid email address'),
  name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  role: z.enum(['admin', 'editor', 'viewer']),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain uppercase letter')
    .regex(/[0-9]/, 'Must contain a number'),
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

export function CreateUserForm({ onSubmit }: { onSubmit: (data: CreateUserInput) => Promise<void> }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    setError,
  } = useForm<CreateUserInput>({
    resolver: zodResolver(CreateUserSchema),
    defaultValues: { role: 'viewer' },
  });

  const handleFormSubmit = async (data: CreateUserInput) => {
    try {
      await onSubmit(data);
      reset();
    } catch (err) {
      if (err instanceof ApiError && err.field) {
        setError(err.field as keyof CreateUserInput, { message: err.message });
      } else {
        setError('root', { message: 'An unexpected error occurred' });
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} aria-invalid={!!errors.email} />
        {errors.email && <p role="alert" className="text-red-500">{errors.email.message}</p>}
      </div>

      <div>
        <label htmlFor="name">Name</label>
        <input id="name" type="text" {...register('name')} aria-invalid={!!errors.name} />
        {errors.name && <p role="alert" className="text-red-500">{errors.name.message}</p>}
      </div>

      <div>
        <label htmlFor="role">Role</label>
        <select id="role" {...register('role')}>
          <option value="viewer">Viewer</option>
          <option value="editor">Editor</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...register('password')} aria-invalid={!!errors.password} />
        {errors.password && <p role="alert" className="text-red-500">{errors.password.message}</p>}
      </div>

      {errors.root && <p role="alert" className="text-red-500">{errors.root.message}</p>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : 'Create User'}
      </button>
    </form>
  );
}
```

---

## 9. Accessibility (a11y) Checklist

### Mandatory Practices

- [ ] Every `<img>` has a meaningful `alt` (or `alt=""` for decorative images)
- [ ] All form inputs have associated `<label>` elements (use `htmlFor`/`id` pairs)
- [ ] Interactive elements are keyboard accessible (`Tab`, `Enter`, `Escape`)
- [ ] Error messages are announced with `role="alert"` or `aria-live="polite"`
- [ ] Color contrast meets WCAG 2.1 AA (4.5:1 for text, 3:1 for large text)
- [ ] Focus management on route changes (focus the `<main>` or `<h1>`)
- [ ] Modals trap focus and return focus to trigger on close
- [ ] Use semantic HTML (`<nav>`, `<main>`, `<article>`, `<aside>`, `<header>`, `<footer>`)

### Focus Trap for Modals

```typescript
import { useEffect, useRef } from 'react';

export function useTrappedFocus(isOpen: boolean) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    firstElement?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    };

    containerRef.current.addEventListener('keydown', handleKeyDown);
    return () => containerRef.current?.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return containerRef;
}
```

---

## 10. Testing — Vitest + React Testing Library

### Test Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80,
      },
    },
  },
});
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

### Testing Patterns

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { CreateUserForm } from './CreateUserForm';

describe('CreateUserForm', () => {
  it('shows validation errors for empty required fields', async () => {
    const onSubmit = vi.fn();
    render(<CreateUserForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByRole('button', { name: /create user/i }));

    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits valid form data', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<CreateUserForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/name/i), 'John Doe');
    await userEvent.type(screen.getByLabelText(/password/i), 'SecurePass1');
    await userEvent.click(screen.getByRole('button', { name: /create user/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'user@example.com',
        name: 'John Doe',
        role: 'viewer',
        password: 'SecurePass1',
      });
    });
  });

  it('displays server-side errors', async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError('Email already exists', 'email')
    );
    render(<CreateUserForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'dupe@example.com');
    await userEvent.type(screen.getByLabelText(/name/i), 'Jane');
    await userEvent.type(screen.getByLabelText(/password/i), 'SecurePass1');
    await userEvent.click(screen.getByRole('button', { name: /create user/i }));

    expect(await screen.findByText(/email already exists/i)).toBeInTheDocument();
  });
});
```

### Testing Hooks

```typescript
import { renderHook, act } from '@testing-library/react';
import { useDebouncedValue } from './useDebouncedValue';

describe('useDebouncedValue', () => {
  beforeEach(() => { vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); });

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebouncedValue('hello', 300));
    expect(result.current).toBe('hello');
  });

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 300),
      { initialProps: { value: 'hello' } }
    );

    rerender({ value: 'world' });
    expect(result.current).toBe('hello'); // Not yet updated

    act(() => { vi.advanceTimersByTime(300); });
    expect(result.current).toBe('world'); // Now updated
  });
});
```

---

## 11. Production Error Boundaries

Never let an unhandled component error crash the entire application:

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.props.onError?.(error, errorInfo);
    // Send to Sentry, Datadog, or central telemetry
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-4 border border-red-300 bg-red-50 rounded text-red-800">
            <h2 className="font-bold text-lg">Component Failed to Load</h2>
            <p className="text-sm">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="mt-2 text-blue-600 underline"
            >
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
```

### Strategic Boundary Placement

```typescript
function App() {
  return (
    <ErrorBoundary fallback={<FullPageError />} onError={reportToSentry}>
      <Header />
      <main>
        <ErrorBoundary fallback={<SidebarFallback />}>
          <Sidebar />
        </ErrorBoundary>
        <ErrorBoundary fallback={<ContentFallback />}>
          <MainContent />
        </ErrorBoundary>
      </main>
    </ErrorBoundary>
  );
}
```

> **Rule**: Place error boundaries around independent feature sections so a failure in one section doesn't take down others.

---

## 12. Routing Patterns (React Router v6+ / TanStack Router)

### Type-Safe Routing with TanStack Router

```typescript
import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

const projectSearchSchema = z.object({
  page: z.number().catch(1),
  sort: z.enum(['name', 'date', 'status']).catch('date'),
  filter: z.string().optional(),
});

export const Route = createFileRoute('/projects/')({
  validateSearch: projectSearchSchema,
  loaderDeps: ({ search }) => ({ search }),
  loader: async ({ deps: { search } }) => {
    return fetchProjects(search);
  },
  component: ProjectListPage,
});

function ProjectListPage() {
  const projects = Route.useLoaderData();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <div>
      <ProjectFilters
        sort={search.sort}
        onSortChange={(sort) => navigate({ search: { ...search, sort } })}
      />
      <ProjectGrid projects={projects} />
      <Pagination page={search.page} />
    </div>
  );
}
```

---

## 13. Anti-Patterns to Eliminate

| Anti-Pattern | Problem | Correct Approach |
|---|---|---|
| Mirroring props in state | State diverges from source of truth | Derive values during render or use a key to reset |
| `useEffect` for data transformation | Extra render cycle, stale values | Calculate derived state in component body |
| Index as key in dynamic lists | State corruption on sort/filter | Use stable unique IDs (`item.id`) |
| Prop drilling 5+ levels deep | Fragile, hard to refactor | Use Zustand, Jotai, or context for shared state |
| Giant monolith components | Untestable, impossible to reuse | Extract hooks and sub-components (< 200 lines/file) |
| Fetching in `useEffect` without cleanup | Race conditions, memory leaks | Use TanStack Query or `use()` with Suspense |
| Missing dependency array entries | Stale closures, subtle bugs | Enable `react-hooks/exhaustive-deps` ESLint rule |
| `any` types on props | No type safety, runtime crashes | Define explicit interfaces for all component props |

---

## 14. Security Considerations

1. **XSS Prevention**: Never use `dangerouslySetInnerHTML` without sanitizing through `dompurify`. Prefer rendering structured data as React elements.
2. **Sensitive Data in State**: Never store passwords, tokens, or PII in React state that gets logged by devtools or error reporters. Use secure cookies or `httpOnly` tokens.
3. **Third-Party Dependencies**: Audit with `npm audit` regularly. Pin exact versions for security-critical packages.
4. **CSP Headers**: Configure Content Security Policy headers to prevent inline script injection. React is compatible with `nonce`-based CSP.
5. **URL Injection**: Always validate and sanitize user-provided URLs before passing to `href` attributes. Reject `javascript:` protocol URLs.

---

## 15. Production Readiness Checklist

- [ ] ESLint configured with `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`
- [ ] TypeScript strict mode enabled (`strict: true` in `tsconfig.json`)
- [ ] Error boundaries around all major UI sections
- [ ] `React.StrictMode` enabled in development
- [ ] Bundle analyzed with `source-map-explorer` or `@next/bundle-analyzer`
- [ ] Code-split routes with `React.lazy` / dynamic imports
- [ ] Accessibility tested with axe-core / Lighthouse
- [ ] All forms validated with Zod schemas (client + server)
- [ ] TanStack Query configured with global error handler
- [ ] Performance profiled with React DevTools Profiler
- [ ] No `console.log` in production (strip with build tool)
- [ ] Key prop audit — no index keys on dynamic lists
- [ ] Images use lazy loading and `srcset` / `sizes`

---

## 16. References & Further Reading

- [React Documentation (react.dev)](https://react.dev)
- [React 19 Blog Post](https://react.dev/blog/2024/12/05/react-19)
- [TanStack Query v5 Docs](https://tanstack.com/query/latest)
- [Zustand GitHub](https://github.com/pmndrs/zustand)
- [React Hook Form](https://react-hook-form.com)
- [Zod Documentation](https://zod.dev)
- [Testing Library](https://testing-library.com/docs/react-testing-library/intro)
- [Vitest](https://vitest.dev)
- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/WAI/WCAG21/quickref/)
- [TanStack Router](https://tanstack.com/router/latest)
