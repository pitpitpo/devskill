# 💚 Vue 3 & Nuxt 3 Production Guide (`vue-nuxt.md`)

> **Framework**: Vue 3.4+ / Nuxt 3.13+
> **Classification**: Full-Stack Frontend Framework with Hybrid Rendering
> **Core Philosophy**: "Reactivity is Transparent; Conventions Over Configuration; Ship Less JavaScript."

---

## 1. Overview & When to Use

Vue 3 with Nuxt 3 is a batteries-included full-stack framework built on top of Vue's Composition API, Nitro server engine, and Vite. Use Vue + Nuxt when:

- Building full-stack web applications with hybrid rendering (SSR + SPA + SSG per-route)
- You want file-based routing, auto-imports, and zero-config TypeScript
- SEO matters and you need server-rendered HTML with hydration
- Your team values explicit reactivity (`ref`, `computed`) over implicit magic
- You need a server layer (API routes, middleware) without a separate backend

**Do NOT use Vue + Nuxt** when:

- Building a tiny widget or micro-frontend where the ~50KB runtime is unjustified — use vanilla JS or Svelte
- You need React Native or a mature cross-platform mobile story — Vue's mobile ecosystem (Capacitor/Ionic) is less mature
- Your project is entirely static with zero interactivity — use Astro or plain HTML/CSS
- Your team is deeply invested in React's ecosystem and switching cost exceeds benefit
- You need bleeding-edge streaming SSR with React Server Components–level granularity — Nuxt's model is different

---

## 2. Core Architecture

### Vue 3 Composition API Mental Model

```
┌──────────────────────────────────────────────────────────┐
│                      Component (.vue SFC)                │
│                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │  <script     │   │  <template>  │   │  <style      │  │
│  │   setup      │──▶│  Reactive    │   │   scoped>    │  │
│  │   lang="ts"> │   │  Template    │   │  CSS Modules │  │
│  │              │   │              │   │              │  │
│  │  ref()       │   │  v-bind      │   │  :deep()     │  │
│  │  computed()  │   │  v-if/v-for  │   │  :global()   │  │
│  │  watch()     │   │  @click      │   │              │  │
│  │  composable()│   │  {{ interp }}│   │              │  │
│  └─────────────┘   └──────────────┘   └──────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                Vue Reactivity System                     │
│                                                          │
│   ref(value)  ──▶  Proxy-wrapped primitive               │
│   reactive(obj) ─▶  Deep Proxy on object                 │
│   computed()  ──▶  Cached derived value (lazy)           │
│   watch()     ──▶  Side-effect on dependency change      │
│   watchEffect() ▶  Auto-tracked side-effect              │
└──────────────────────────────────────────────────────────┘
```

### Nuxt 3 Request Lifecycle

```
Browser Request
      │
      ▼
┌─────────────────┐
│  Nitro Server    │
│  (H3 + unjs)     │
│                   │
│  ┌─────────────┐ │     ┌──────────────────┐
│  │ Server       │ │     │ server/middleware/ │
│  │ Middleware   │◀├─────│ (auth, logging)   │
│  └──────┬──────┘ │     └──────────────────┘
│         │        │
│  ┌──────▼──────┐ │     ┌──────────────────┐
│  │ Route       │ │     │ server/api/       │
│  │ Matching    │─├────▶│ (API endpoints)   │
│  └──────┬──────┘ │     └──────────────────┘
│         │        │
│  ┌──────▼──────┐ │
│  │ SSR Render  │ │  pages/ → app.vue → layouts/
│  │ (Vue +      │ │
│  │  useAsyncData│ │
│  │  resolution)│ │
│  └──────┬──────┘ │
│         │        │
│  ┌──────▼──────┐ │
│  │ HTML Stream │ │
│  │ Response    │ │
│  └─────────────┘ │
└─────────────────┘
      │
      ▼
Browser (Hydration → SPA Navigation)
```

---

## 3. Vue 3 Composition API — Production Patterns

### 3.1 Refs vs Reactive — The Golden Rule

**Use `ref()` by default. Use `reactive()` only for complex objects you never reassign.**

```typescript
// ✅ GOOD — ref for primitives and reassignable values
import { ref, computed } from 'vue';

const count = ref(0);                    // Ref<number>
const user = ref<User | null>(null);     // Ref<User | null>
const items = ref<Product[]>([]);        // Ref<Product[]>

// Reassignment works naturally
user.value = await fetchUser(id);
items.value = [...items.value, newItem];

// ❌ BAD — reactive loses reactivity on reassignment
import { reactive } from 'vue';

let state = reactive({ user: null, items: [] });
// This BREAKS reactivity — `state` is now a plain object
state = { user: newUser, items: newItems };
```

```typescript
// ✅ GOOD use of reactive — deeply nested, never reassigned
const formState = reactive({
  name: '',
  email: '',
  address: {
    street: '',
    city: '',
    zip: '',
  },
  errors: {} as Record<string, string>,
});

// Mutate properties directly (no .value needed)
formState.name = 'Jane';
formState.address.city = 'Berlin';
```

### 3.2 Composables — The Reusability Unit

Composables are the Vue 3 equivalent of React hooks. They encapsulate reactive state and logic.

```typescript
// composables/useDebounce.ts
import { ref, watch, type Ref } from 'vue';

export function useDebounce<T>(source: Ref<T>, delayMs: number = 300): Ref<T> {
  const debounced = ref(source.value) as Ref<T>;
  let timeout: ReturnType<typeof setTimeout>;

  watch(source, (newVal) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      debounced.value = newVal;
    }, delayMs);
  });

  return debounced;
}
```

```typescript
// composables/usePagination.ts
import { ref, computed, type Ref } from 'vue';

interface UsePaginationOptions {
  initialPage?: number;
  pageSize?: number;
}

interface UsePaginationReturn<T> {
  currentPage: Ref<number>;
  pageSize: Ref<number>;
  totalPages: Ref<number>;
  paginatedItems: Ref<T[]>;
  nextPage: () => void;
  prevPage: () => void;
  goToPage: (page: number) => void;
}

export function usePagination<T>(
  items: Ref<T[]>,
  options: UsePaginationOptions = {}
): UsePaginationReturn<T> {
  const currentPage = ref(options.initialPage ?? 1);
  const pageSize = ref(options.pageSize ?? 20);

  const totalPages = computed(() =>
    Math.max(1, Math.ceil(items.value.length / pageSize.value))
  );

  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    return items.value.slice(start, start + pageSize.value);
  });

  const goToPage = (page: number) => {
    currentPage.value = Math.max(1, Math.min(page, totalPages.value));
  };

  const nextPage = () => goToPage(currentPage.value + 1);
  const prevPage = () => goToPage(currentPage.value - 1);

  return {
    currentPage,
    pageSize,
    totalPages,
    paginatedItems: paginatedItems as Ref<T[]>,
    nextPage,
    prevPage,
    goToPage,
  };
}
```

```typescript
// composables/useApi.ts — Production-grade data fetching composable
import { ref, shallowRef, type Ref } from 'vue';

interface UseApiReturn<T> {
  data: Ref<T | null>;
  error: Ref<Error | null>;
  loading: Ref<boolean>;
  execute: (...args: unknown[]) => Promise<T>;
  reset: () => void;
}

export function useApi<T>(
  fetcher: (...args: unknown[]) => Promise<T>
): UseApiReturn<T> {
  const data = shallowRef<T | null>(null);
  const error = ref<Error | null>(null);
  const loading = ref(false);

  const execute = async (...args: unknown[]): Promise<T> => {
    loading.value = true;
    error.value = null;

    try {
      const result = await fetcher(...args);
      data.value = result;
      return result;
    } catch (err) {
      error.value = err instanceof Error ? err : new Error(String(err));
      throw error.value;
    } finally {
      loading.value = false;
    }
  };

  const reset = () => {
    data.value = null;
    error.value = null;
    loading.value = false;
  };

  return { data, error, loading, execute, reset };
}
```

### 3.3 Component Patterns with `<script setup>`

```vue
<!-- components/UserCard.vue -->
<script setup lang="ts">
import { computed } from 'vue';

// ✅ Props with TypeScript — compiler extracts types, no runtime overhead
interface Props {
  user: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
    role: 'admin' | 'editor' | 'viewer';
  };
  highlighted?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  highlighted: false,
});

// ✅ Typed emits
const emit = defineEmits<{
  select: [userId: string];
  remove: [userId: string];
}>();

// ✅ Expose only what parent needs
defineExpose({
  focus: () => {
    // focus logic
  },
});

const initials = computed(() =>
  props.user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
);

const roleBadgeClass = computed(() => {
  const classes: Record<string, string> = {
    admin: 'bg-red-100 text-red-800',
    editor: 'bg-blue-100 text-blue-800',
    viewer: 'bg-gray-100 text-gray-600',
  };
  return classes[props.user.role] ?? classes.viewer;
});
</script>

<template>
  <div
    :class="[
      'rounded-lg border p-4 transition-shadow',
      highlighted ? 'border-blue-500 shadow-md' : 'border-gray-200',
    ]"
    @click="emit('select', user.id)"
  >
    <div class="flex items-center gap-3">
      <img
        v-if="user.avatar"
        :src="user.avatar"
        :alt="`${user.name} avatar`"
        class="h-10 w-10 rounded-full object-cover"
        loading="lazy"
      />
      <div
        v-else
        class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 text-sm font-medium"
      >
        {{ initials }}
      </div>

      <div class="flex-1 min-w-0">
        <p class="truncate font-medium text-gray-900">{{ user.name }}</p>
        <p class="truncate text-sm text-gray-500">{{ user.email }}</p>
      </div>

      <span :class="['rounded-full px-2 py-0.5 text-xs font-medium', roleBadgeClass]">
        {{ user.role }}
      </span>
    </div>

    <button
      class="mt-3 text-sm text-red-600 hover:text-red-800"
      @click.stop="emit('remove', user.id)"
    >
      Remove
    </button>
  </div>
</template>
```

---

## 4. Nuxt 3 — File-Based Conventions

### 4.1 Directory Structure (Production)

```
project-root/
├── .nuxt/                    # Generated — NEVER edit
├── app.vue                   # Root component (wraps <NuxtPage>)
├── app.config.ts             # Runtime app configuration
├── nuxt.config.ts            # Build-time configuration
├── pages/
│   ├── index.vue             # → /
│   ├── about.vue             # → /about
│   ├── users/
│   │   ├── index.vue         # → /users
│   │   └── [id].vue          # → /users/:id (dynamic segment)
│   └── blog/
│       └── [...slug].vue     # → /blog/* (catch-all)
├── components/
│   ├── ui/                   # Auto-imported as <UiButton>
│   │   ├── Button.vue
│   │   └── Modal.vue
│   └── feature/
│       └── UserCard.vue      # Auto-imported as <FeatureUserCard>
├── composables/              # Auto-imported composables
│   ├── useAuth.ts
│   └── useApi.ts
├── layouts/
│   ├── default.vue           # Default layout
│   └── dashboard.vue         # Named layout
├── middleware/
│   ├── auth.ts               # Named route middleware
│   └── admin.global.ts       # Global middleware (runs on every route)
├── plugins/
│   ├── api.ts                # Plugin — runs on app init
│   └── sentry.client.ts      # Client-only plugin (.client.ts suffix)
├── server/
│   ├── api/
│   │   ├── users/
│   │   │   ├── index.get.ts  # GET /api/users
│   │   │   ├── index.post.ts # POST /api/users
│   │   │   └── [id].get.ts   # GET /api/users/:id
│   │   └── health.ts         # GET /api/health
│   ├── middleware/
│   │   └── cors.ts           # Server middleware (H3)
│   └── utils/
│       └── db.ts             # Server-only utilities
├── public/                   # Static assets (served at /)
├── assets/                   # Build-processed assets (CSS, images)
│   └── css/
│       └── main.css
└── types/
    └── index.d.ts            # Global type declarations
```

### 4.2 Data Fetching — `useAsyncData` and `useFetch`

```vue
<!-- pages/users/[id].vue -->
<script setup lang="ts">
// ✅ GOOD — useFetch is the convenience wrapper for useAsyncData + $fetch
// It deduplicates requests, handles SSR→client transfer, and caches

interface User {
  id: string;
  name: string;
  email: string;
  createdAt: string;
}

const route = useRoute();

// useFetch automatically:
// 1. Runs on server during SSR
// 2. Transfers payload to client (no duplicate fetch on hydration)
// 3. Re-fetches when route.params.id changes (reactive key)
const {
  data: user,
  status,     // 'idle' | 'pending' | 'success' | 'error'
  error,
  refresh,
} = await useFetch<User>(`/api/users/${route.params.id}`, {
  // Transform response before caching
  transform: (response) => ({
    ...response,
    createdAt: new Date(response.createdAt).toLocaleDateString(),
  }),
  // Only re-fetch when these change
  watch: [() => route.params.id],
});

// ❌ BAD — never use raw fetch() or $fetch in components
// It won't deduplicate, won't transfer SSR payload, causes hydration mismatch
// const user = await $fetch(`/api/users/${route.params.id}`);  // WRONG

// For multiple parallel requests, use useAsyncData with Promise.all
const { data: dashboardData } = await useAsyncData('dashboard', () =>
  Promise.all([
    $fetch<User>('/api/users/me'),
    $fetch<{ count: number }>('/api/notifications/count'),
    $fetch<Activity[]>('/api/activity/recent'),
  ])
);

// Lazy loading — component renders immediately, data loads in background
const { data: recommendations, status: recsStatus } = await useFetch<Product[]>(
  '/api/recommendations',
  { lazy: true }
);
</script>

<template>
  <div>
    <div v-if="status === 'pending'" class="animate-pulse">
      <div class="h-8 w-48 rounded bg-gray-200" />
      <div class="mt-2 h-4 w-32 rounded bg-gray-200" />
    </div>

    <div v-else-if="error" class="rounded border border-red-200 bg-red-50 p-4">
      <p class="text-red-800">Failed to load user: {{ error.message }}</p>
      <button class="mt-2 text-sm text-red-600 underline" @click="refresh()">
        Retry
      </button>
    </div>

    <div v-else-if="user">
      <h1 class="text-2xl font-bold">{{ user.name }}</h1>
      <p class="text-gray-500">{{ user.email }}</p>
      <p class="text-sm text-gray-400">Joined {{ user.createdAt }}</p>
    </div>
  </div>
</template>
```

### 4.3 Hybrid Rendering — Route Rules

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  // Per-route rendering strategy
  routeRules: {
    // Static pages — pre-rendered at build time
    '/': { prerender: true },
    '/about': { prerender: true },
    '/blog/**': { prerender: true },

    // ISR — regenerate every 60 seconds
    '/products/**': { isr: 60 },

    // SPA mode — no SSR (dashboard behind auth)
    '/dashboard/**': { ssr: false },

    // SSR with CDN caching
    '/api/products/**': {
      cors: true,
      headers: { 'cache-control': 's-maxage=600, stale-while-revalidate=60' },
    },

    // Redirect rules
    '/old-path': { redirect: '/new-path' },
  },

  // Nitro server engine configuration
  nitro: {
    preset: 'node-server',  // or 'vercel', 'cloudflare-pages', 'netlify'
    compressPublicAssets: true,
    minify: true,

    // Server-side caching
    storage: {
      cache: {
        driver: 'redis',
        host: process.env.REDIS_HOST,
        port: 6379,
      },
    },
  },
});
```

---

## 5. Pinia — State Management

### 5.1 Setup Store (Recommended Pattern)

```typescript
// stores/auth.ts
import { skipHydrate } from 'pinia';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);
  const returnUrl = ref<string | null>(null);

  // Getters (computed)
  const isAuthenticated = computed(() => !!token.value);
  const isAdmin = computed(() => user.value?.role === 'admin');
  const displayName = computed(() => user.value?.name ?? 'Anonymous');

  // Actions
  async function login(email: string, password: string): Promise<void> {
    try {
      const response = await $fetch<{ user: User; token: string }>('/api/auth/login', {
        method: 'POST',
        body: { email, password },
      });

      user.value = response.user;
      token.value = response.token;

      // Navigate to return URL or dashboard
      const redirect = returnUrl.value ?? '/dashboard';
      returnUrl.value = null;
      await navigateTo(redirect);
    } catch (error) {
      // Let the component handle the error
      throw createError({
        statusCode: 401,
        statusMessage: 'Invalid credentials',
      });
    }
  }

  async function logout(): Promise<void> {
    try {
      await $fetch('/api/auth/logout', { method: 'POST' });
    } finally {
      user.value = null;
      token.value = null;
      await navigateTo('/login');
    }
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return;

    try {
      user.value = await $fetch<User>('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` },
      });
    } catch {
      // Token expired or invalid
      await logout();
    }
  }

  return {
    // State
    user,
    token: skipHydrate(token), // Don't serialize token in SSR payload
    returnUrl,
    // Getters
    isAuthenticated,
    isAdmin,
    displayName,
    // Actions
    login,
    logout,
    fetchUser,
  };
});
```

### 5.2 Store with Server-Side Initialization

```typescript
// stores/products.ts
interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
  inStock: boolean;
}

interface ProductFilters {
  category: string | null;
  minPrice: number;
  maxPrice: number;
  inStockOnly: boolean;
}

export const useProductStore = defineStore('products', () => {
  const items = ref<Product[]>([]);
  const filters = reactive<ProductFilters>({
    category: null,
    minPrice: 0,
    maxPrice: Infinity,
    inStockOnly: false,
  });
  const loading = ref(false);

  // Derived state
  const filteredProducts = computed(() => {
    return items.value.filter((product) => {
      if (filters.category && product.category !== filters.category) return false;
      if (product.price < filters.minPrice) return false;
      if (product.price > filters.maxPrice) return false;
      if (filters.inStockOnly && !product.inStock) return false;
      return true;
    });
  });

  const categories = computed(() =>
    [...new Set(items.value.map((p) => p.category))].sort()
  );

  const totalValue = computed(() =>
    filteredProducts.value.reduce((sum, p) => sum + p.price, 0)
  );

  // Actions
  async function fetchProducts(): Promise<void> {
    loading.value = true;
    try {
      items.value = await $fetch<Product[]>('/api/products');
    } finally {
      loading.value = false;
    }
  }

  function setFilter<K extends keyof ProductFilters>(
    key: K,
    value: ProductFilters[K]
  ): void {
    filters[key] = value;
  }

  function resetFilters(): void {
    filters.category = null;
    filters.minPrice = 0;
    filters.maxPrice = Infinity;
    filters.inStockOnly = false;
  }

  return {
    items,
    filters,
    loading,
    filteredProducts,
    categories,
    totalValue,
    fetchProducts,
    setFilter,
    resetFilters,
  };
});
```

---

## 6. Server Engine (Nitro + H3)

### 6.1 API Routes

```typescript
// server/api/users/index.get.ts
import { z } from 'zod';

const querySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().optional(),
  role: z.enum(['admin', 'editor', 'viewer']).optional(),
});

export default defineEventHandler(async (event) => {
  // Validate query parameters
  const query = await getValidatedQuery(event, querySchema.parse);

  const { page, limit, search, role } = query;
  const offset = (page - 1) * limit;

  // Database query (using Drizzle ORM as example)
  const db = useDatabase();

  let queryBuilder = db.select().from(users);

  if (search) {
    queryBuilder = queryBuilder.where(
      or(
        like(users.name, `%${search}%`),
        like(users.email, `%${search}%`)
      )
    );
  }

  if (role) {
    queryBuilder = queryBuilder.where(eq(users.role, role));
  }

  const [items, [{ total }]] = await Promise.all([
    queryBuilder.limit(limit).offset(offset),
    db.select({ total: count() }).from(users),
  ]);

  return {
    data: items,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  };
});
```

```typescript
// server/api/users/index.post.ts
import { z } from 'zod';

const createUserSchema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'editor', 'viewer']).default('viewer'),
});

export default defineEventHandler(async (event) => {
  // Validate request body
  const body = await readValidatedBody(event, createUserSchema.parse);

  // Check for duplicate email
  const existing = await db
    .select()
    .from(users)
    .where(eq(users.email, body.email))
    .get();

  if (existing) {
    throw createError({
      statusCode: 409,
      statusMessage: 'A user with this email already exists',
    });
  }

  const newUser = await db.insert(users).values({
    id: crypto.randomUUID(),
    ...body,
    createdAt: new Date(),
  }).returning().get();

  setResponseStatus(event, 201);
  return newUser;
});
```

### 6.2 Server Middleware

```typescript
// server/middleware/auth.ts
export default defineEventHandler(async (event) => {
  // Skip auth for public routes
  const publicPaths = ['/api/auth/login', '/api/auth/register', '/api/health'];
  const path = getRequestURL(event).pathname;

  if (publicPaths.some((p) => path.startsWith(p))) return;
  if (!path.startsWith('/api/')) return; // Only protect API routes

  const authHeader = getRequestHeader(event, 'authorization');

  if (!authHeader?.startsWith('Bearer ')) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Missing or invalid authorization header',
    });
  }

  const token = authHeader.slice(7);

  try {
    const payload = await verifyJWT(token);
    // Attach user to event context for downstream handlers
    event.context.auth = {
      userId: payload.sub,
      role: payload.role,
      email: payload.email,
    };
  } catch {
    throw createError({
      statusCode: 401,
      statusMessage: 'Token expired or invalid',
    });
  }
});
```

### 6.3 Server Utilities & Caching

```typescript
// server/utils/cache.ts
import { defineCachedFunction } from 'nitropack/runtime';

// Cache expensive computations with Nitro's built-in caching
export const getPopularProducts = defineCachedFunction(
  async () => {
    const db = useDatabase();
    return db
      .select()
      .from(products)
      .orderBy(desc(products.salesCount))
      .limit(50)
      .all();
  },
  {
    maxAge: 60 * 5,        // Cache for 5 minutes
    name: 'popular-products',
    getKey: () => 'all',   // Static cache key
  }
);

// Cache with dynamic keys
export const getUserProfile = defineCachedFunction(
  async (userId: string) => {
    return db.select().from(users).where(eq(users.id, userId)).get();
  },
  {
    maxAge: 60,
    name: 'user-profile',
    getKey: (userId: string) => userId,
  }
);
```

---

## 7. TypeScript Integration

### 7.1 Auto-Generated Types

Nuxt auto-generates types for routes, components, composables, and API responses.

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  typescript: {
    strict: true,
    typeCheck: true,  // Enable vue-tsc type checking in dev
    shim: false,      // Disable legacy shim (not needed with Volar)
  },

  // Module configuration
  modules: [
    '@pinia/nuxt',
    '@nuxtjs/i18n',
    '@vueuse/nuxt',
    'nuxt-security',
  ],
});
```

```typescript
// types/index.d.ts — Augment Nuxt types
declare module '#app' {
  interface PageMeta {
    requiresAuth?: boolean;
    requiredRole?: 'admin' | 'editor' | 'viewer';
  }
}

// Augment H3 event context
declare module 'h3' {
  interface H3EventContext {
    auth?: {
      userId: string;
      role: string;
      email: string;
    };
  }
}

export {};
```

### 7.2 Typed Route Middleware

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware(async (to, from) => {
  const auth = useAuthStore();

  // Check page meta
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    auth.returnUrl = to.fullPath;
    return navigateTo('/login');
  }

  if (to.meta.requiredRole && auth.user?.role !== to.meta.requiredRole) {
    return abortNavigation(
      createError({
        statusCode: 403,
        statusMessage: 'Insufficient permissions',
      })
    );
  }
});
```

```vue
<!-- pages/admin/settings.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'dashboard',
  middleware: 'auth',
  requiresAuth: true,
  requiredRole: 'admin',
});
</script>
```

---

## 8. Performance Optimization

### 8.1 Component-Level Optimization

```vue
<script setup lang="ts">
import { shallowRef, triggerRef } from 'vue';

// ✅ shallowRef for large arrays/objects — only top-level .value triggers reactivity
const largeDataset = shallowRef<DataPoint[]>([]);

function updateDataset(newData: DataPoint[]) {
  // Direct mutation doesn't trigger watchers (efficient)
  largeDataset.value.push(...newData);
  triggerRef(largeDataset); // Manually trigger when ready
}

// ✅ v-once for content that never changes
// ✅ v-memo for expensive template sections
</script>

<template>
  <!-- v-once: renders once, skips all future updates -->
  <header v-once>
    <h1>{{ appTitle }}</h1>
    <p>{{ appDescription }}</p>
  </header>

  <!-- v-memo: re-renders only when dependencies change -->
  <div
    v-for="item in items"
    :key="item.id"
    v-memo="[item.id, item.selected]"
  >
    <ExpensiveComponent :item="item" />
  </div>
</template>
```

### 8.2 Lazy Loading & Code Splitting

```vue
<script setup lang="ts">
// ✅ Lazy components — auto code-split by Nuxt
// Just prefix component name with "Lazy"
</script>

<template>
  <!-- Only loaded when `showChart` becomes true -->
  <LazyDashboardChart v-if="showChart" :data="chartData" />

  <!-- Below-the-fold content -->
  <LazyFeedbackWidget />
</template>
```

```typescript
// nuxt.config.ts — Advanced optimization
export default defineNuxtConfig({
  experimental: {
    payloadExtraction: true,   // Extract SSR payload to static files
    renderJsonPayloads: true,  // Use JSON instead of JS for SSR payload
    treeshakeClientOnly: true, // Remove server-only code from client bundle
  },

  vite: {
    build: {
      rollupOptions: {
        output: {
          // Manual chunk splitting for optimal caching
          manualChunks: {
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'ui-vendor': ['@headlessui/vue', '@heroicons/vue'],
          },
        },
      },
    },
  },

  // Image optimization
  image: {
    provider: 'ipx',
    quality: 80,
    formats: ['avif', 'webp'],
    screens: {
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
    },
  },
});
```

### 8.3 Performance Benchmarks

| Metric | Target | Optimization |
|--------|--------|-------------|
| LCP (Largest Contentful Paint) | < 2.5s | SSR + `<NuxtImg>` with `loading="eager"` for hero |
| FID (First Input Delay) | < 100ms | Code-split heavy components, defer non-critical JS |
| CLS (Cumulative Layout Shift) | < 0.1 | Set explicit `width`/`height` on images, use `<NuxtImg>` |
| TTI (Time to Interactive) | < 3.5s | `ssr: false` for heavy dashboard pages behind auth |
| Bundle Size (gzipped) | < 100KB initial | Tree-shaking, lazy components, `shallowRef` |

---

## 9. Testing with Vitest

### 9.1 Composable Testing

```typescript
// composables/__tests__/usePagination.test.ts
import { describe, it, expect } from 'vitest';
import { ref } from 'vue';
import { usePagination } from '../usePagination';

describe('usePagination', () => {
  const createItems = (count: number) =>
    Array.from({ length: count }, (_, i) => ({ id: i + 1, name: `Item ${i + 1}` }));

  it('paginates items correctly', () => {
    const items = ref(createItems(50));
    const { paginatedItems, totalPages, currentPage } = usePagination(items, {
      pageSize: 10,
    });

    expect(paginatedItems.value).toHaveLength(10);
    expect(paginatedItems.value[0]).toEqual({ id: 1, name: 'Item 1' });
    expect(totalPages.value).toBe(5);
    expect(currentPage.value).toBe(1);
  });

  it('navigates pages', () => {
    const items = ref(createItems(30));
    const { paginatedItems, currentPage, nextPage, prevPage } = usePagination(
      items,
      { pageSize: 10 }
    );

    nextPage();
    expect(currentPage.value).toBe(2);
    expect(paginatedItems.value[0]).toEqual({ id: 11, name: 'Item 11' });

    nextPage();
    expect(currentPage.value).toBe(3);

    // Should not exceed max page
    nextPage();
    expect(currentPage.value).toBe(3);

    prevPage();
    expect(currentPage.value).toBe(2);
  });

  it('clamps to valid page range', () => {
    const items = ref(createItems(25));
    const { goToPage, currentPage, totalPages } = usePagination(items, {
      pageSize: 10,
    });

    goToPage(100);
    expect(currentPage.value).toBe(totalPages.value);

    goToPage(-5);
    expect(currentPage.value).toBe(1);
  });

  it('reacts to items changes', () => {
    const items = ref(createItems(10));
    const { totalPages } = usePagination(items, { pageSize: 5 });

    expect(totalPages.value).toBe(2);

    items.value = createItems(20);
    expect(totalPages.value).toBe(4);
  });
});
```

### 9.2 Component Testing

```typescript
// components/__tests__/UserCard.test.ts
import { describe, it, expect } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import UserCard from '../UserCard.vue';

describe('UserCard', () => {
  const defaultUser = {
    id: '1',
    name: 'Jane Smith',
    email: 'jane@example.com',
    role: 'editor' as const,
  };

  it('renders user information', async () => {
    const wrapper = await mountSuspended(UserCard, {
      props: { user: defaultUser },
    });

    expect(wrapper.text()).toContain('Jane Smith');
    expect(wrapper.text()).toContain('jane@example.com');
    expect(wrapper.text()).toContain('editor');
  });

  it('shows initials when no avatar', async () => {
    const wrapper = await mountSuspended(UserCard, {
      props: { user: defaultUser },
    });

    expect(wrapper.text()).toContain('JS');
  });

  it('emits select event on click', async () => {
    const wrapper = await mountSuspended(UserCard, {
      props: { user: defaultUser },
    });

    await wrapper.trigger('click');
    expect(wrapper.emitted('select')).toEqual([['1']]);
  });

  it('emits remove event on remove button click', async () => {
    const wrapper = await mountSuspended(UserCard, {
      props: { user: defaultUser },
    });

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('remove')).toEqual([['1']]);
    // Should NOT also emit select (stopPropagation)
    expect(wrapper.emitted('select')).toBeUndefined();
  });

  it('applies highlighted style', async () => {
    const wrapper = await mountSuspended(UserCard, {
      props: { user: defaultUser, highlighted: true },
    });

    const root = wrapper.find('div');
    expect(root.classes()).toContain('border-blue-500');
  });
});
```

### 9.3 API Route Testing

```typescript
// server/api/__tests__/users.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { setup, $fetch, createError } from '@nuxt/test-utils';

describe('/api/users', () => {
  await setup({ server: true });

  describe('GET /api/users', () => {
    it('returns paginated users', async () => {
      const response = await $fetch('/api/users?page=1&limit=5');

      expect(response.data).toBeInstanceOf(Array);
      expect(response.data.length).toBeLessThanOrEqual(5);
      expect(response.pagination).toEqual(
        expect.objectContaining({
          page: 1,
          limit: 5,
          total: expect.any(Number),
          totalPages: expect.any(Number),
        })
      );
    });

    it('validates query parameters', async () => {
      await expect(
        $fetch('/api/users?page=-1')
      ).rejects.toMatchObject({
        statusCode: 400,
      });
    });
  });

  describe('POST /api/users', () => {
    it('creates a new user', async () => {
      const newUser = {
        name: 'Test User',
        email: `test-${Date.now()}@example.com`,
        role: 'viewer',
      };

      const response = await $fetch('/api/users', {
        method: 'POST',
        body: newUser,
      });

      expect(response).toMatchObject({
        id: expect.any(String),
        name: newUser.name,
        email: newUser.email,
      });
    });

    it('rejects duplicate emails', async () => {
      const email = `dupe-${Date.now()}@example.com`;

      await $fetch('/api/users', {
        method: 'POST',
        body: { name: 'First', email, role: 'viewer' },
      });

      await expect(
        $fetch('/api/users', {
          method: 'POST',
          body: { name: 'Second', email, role: 'viewer' },
        })
      ).rejects.toMatchObject({
        statusCode: 409,
      });
    });
  });
});
```

---

## 10. Security Considerations

### 10.1 XSS Prevention

Vue automatically escapes template interpolation (`{{ }}`). The primary attack vector is `v-html`:

```vue
<!-- ❌ DANGEROUS — never use v-html with user input -->
<div v-html="userProvidedContent" />

<!-- ✅ SAFE — Vue auto-escapes interpolation -->
<div>{{ userProvidedContent }}</div>

<!-- ✅ If you MUST render HTML, sanitize first -->
<script setup lang="ts">
import DOMPurify from 'dompurify';

const props = defineProps<{ rawHtml: string }>();
const sanitizedHtml = computed(() => DOMPurify.sanitize(props.rawHtml));
</script>

<template>
  <div v-html="sanitizedHtml" />
</template>
```

### 10.2 Server-Side Security

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['nuxt-security'],

  security: {
    headers: {
      contentSecurityPolicy: {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'strict-dynamic'"],
        'style-src': ["'self'", "'unsafe-inline'"],  // Required for Vue scoped styles
        'img-src': ["'self'", 'data:', 'https:'],
        'connect-src': ["'self'", process.env.API_URL!],
      },
      xFrameOptions: 'DENY',
      xContentTypeOptions: 'nosniff',
      referrerPolicy: 'strict-origin-when-cross-origin',
    },
    rateLimiter: {
      tokensPerInterval: 100,
      interval: 60000, // 1 minute
    },
    corsHandler: {
      origin: [process.env.FRONTEND_URL!],
      methods: ['GET', 'POST', 'PUT', 'DELETE'],
    },
  },
});
```

### 10.3 Environment Variables

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    // Server-only (NEVER exposed to client)
    databaseUrl: process.env.DATABASE_URL,
    jwtSecret: process.env.JWT_SECRET,
    stripeSecretKey: process.env.STRIPE_SECRET_KEY,

    // Public — available on both server and client
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'https://example.com',
    },
  },
});
```

```typescript
// ✅ Access in server routes
export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event);
  console.log(config.databaseUrl); // Available ✅
});

// ✅ Access in components/composables
const config = useRuntimeConfig();
console.log(config.public.apiBase);  // Available ✅
// console.log(config.databaseUrl);  // undefined on client ✅ (safe)
```

---

## 11. Common Pitfalls & Anti-Patterns

| # | Anti-Pattern | Why It Fails | Correct Approach |
|---|-------------|-------------|-----------------|
| 1 | Using `reactive()` with reassignment | Breaks reactivity proxy link | Use `ref()` for values that get reassigned |
| 2 | Calling `$fetch` directly in components | Duplicates requests on SSR→client | Use `useFetch()` or `useAsyncData()` |
| 3 | Accessing `ref.value` in templates | `.value` is auto-unwrapped in templates | Use `{{ myRef }}` not `{{ myRef.value }}` |
| 4 | Destructuring reactive objects | Loses reactivity on primitives | Use `toRefs()` or keep object intact |
| 5 | Missing `await` on `useFetch` | Causes hydration mismatch | Always `await useFetch()` in `<script setup>` |
| 6 | Using `onMounted` for data fetching | Breaks SSR (doesn't run on server) | Use `useFetch()` or `useAsyncData()` |
| 7 | Putting secrets in `runtimeConfig.public` | Exposes to client bundle | Use `runtimeConfig` (not `.public`) for secrets |
| 8 | Using `v-if` and `v-for` on same element | `v-if` has higher priority in Vue 3 | Wrap with `<template v-for>` and put `v-if` inside |
| 9 | Not using `key` on `v-for` lists | Causes incorrect DOM reuse | Always use unique, stable `:key` |
| 10 | Large Pinia stores with everything | Monolith state, poor code-splitting | Split into domain-specific stores |

---

## 12. Verification Checklist

Before shipping to production, verify:

- [ ] **TypeScript strict mode** enabled (`typescript.strict: true` in nuxt.config)
- [ ] **No `any` types** in component props, store state, or API responses
- [ ] **All `useFetch`/`useAsyncData` calls are `await`ed** in `<script setup>`
- [ ] **SSR rendering** produces correct HTML (check `view-source:` in browser)
- [ ] **Hydration mismatch warnings** = 0 in browser console
- [ ] **Environment variables** — secrets are in `runtimeConfig`, not `runtimeConfig.public`
- [ ] **Bundle size** — run `npx nuxi analyze` and verify initial JS < 100KB gzipped
- [ ] **Lighthouse Performance score** ≥ 90 on representative pages
- [ ] **Error boundaries** — `<NuxtErrorBoundary>` wraps independent page sections
- [ ] **SEO meta tags** — `useHead()` or `useSeoMeta()` on every public page
- [ ] **Loading states** — every `useFetch` handles `status === 'pending'`
- [ ] **API validation** — all `server/api/` routes validate input with Zod
- [ ] **Security headers** — CSP, X-Frame-Options, CORS configured via `nuxt-security`
- [ ] **Image optimization** — all images use `<NuxtImg>` with `sizes` attribute
- [ ] **Test coverage** — composables ≥ 90%, components ≥ 80%, API routes ≥ 85%
