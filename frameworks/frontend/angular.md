# 🅰️ Angular 19 / 20+ Signals-First & Zoneless Production Architecture (`frameworks/frontend/angular.md`)

> **Standard Identifier**: `FW-FRONTEND-ANGULAR-001`  
> **Framework**: Angular 19 / 20+ (Standalone-by-Default, Signals, Zoneless Change Detection)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-251–R-253**, **R-260**  
> **Last Updated**: 2026-11-19

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Modern Angular is Signals-first, Standalone-by-default, and Zoneless. Never introduce NgModules, Zone.js monkey-patching, or manual `BehaviorSubject` boilerplate where `signal()`, `computed()`, `linkedSignal()`, and `httpResource()` express reactive state cleanly with O(1) change detection.*

---

## 2. Modern Angular Paradigm Shift (Legacy vs. Angular 19/20)

| Concern | Legacy Angular (Avoid in New Code) | Modern Angular 19 / 20 Standard |
|---|---|---|
| **Component Declaration** | `NgModule` declarations | **Standalone by default** (`standalone: true` is implicit in v19+) |
| **Change Detection** | Zone.js global dirty-checking | **Zoneless** (`provideZonelessChangeDetection()` + `ChangeDetectionStrategy.OnPush`) |
| **Component I/O** | `@Input()`, `@Output()`, `EventEmitter` | Signal inputs/outputs: `input()`, `input.required()`, `output()`, `model()` |
| **Reactive State** | `BehaviorSubject` + manual `async` pipe | `signal()`, `computed()`, `linkedSignal()`, NgRx SignalStore |
| **Async Data Fetching** | Manual `ngOnInit` + `subscribe()` + leak bugs | `resource()` / `httpResource()` or RxJS `toSignal()` |
| **Template Control Flow** | `*ngIf`, `*ngFor`, `*ngSwitch` | Built-in `@if`, `@for (...; track item.id)`, `@switch`, `@defer` |
| **Dependency Injection** | Constructor parameter injection | Functional `inject()` (supports composable helpers and strict typing) |

---

## 3. Application Bootstrap (Zoneless + SSR + Incremental Hydration)

```typescript
// src/app/app.config.ts
import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { provideClientHydration, withEventReplay, withIncrementalHydration } from '@angular/platform-browser';
import { routes } from './app.routes';
import { authInterceptor } from './core/http/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes, withComponentInputBinding(), withViewTransitions()),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor])),
    provideClientHydration(withEventReplay(), withIncrementalHydration()),
  ],
};
```

---

## 4. Production Signal Component with `httpResource`, `linkedSignal` & `@defer`

```typescript
// src/app/features/orders/order-list.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  linkedSignal,
  output,
  signal,
} from '@angular/core';
import { httpResource } from '@angular/common/http';
import { CurrencyPipe } from '@angular/common';

export interface OrderSummary {
  readonly id: string;
  readonly reference: string;
  readonly status: 'draft' | 'paid' | 'shipped';
  readonly totalCents: number;
}

@Component({
  selector: 'app-order-list',
  imports: [CurrencyPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section aria-labelledby="orders-heading" class="space-y-4">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <h1 id="orders-heading" class="text-xl font-semibold">Orders ({{ filteredOrders().length }})</h1>
        <select
          aria-label="Filter by status"
          [value]="selectedStatus()"
          (change)="onStatusChange($event)"
          class="rounded-md border px-3 py-1.5"
        >
          <option value="all">All</option>
          <option value="draft">Draft</option>
          <option value="paid">Paid</option>
          <option value="shipped">Shipped</option>
        </select>
      </header>

      @if (ordersResource.isLoading()) {
        <div role="status" aria-live="polite" class="h-32 animate-pulse rounded-lg bg-slate-100"></div>
      } @else if (ordersResource.error(); as err) {
        <div role="alert" class="rounded-md border border-red-300 bg-red-50 p-4 text-red-900">
          Failed to load orders.
          <button type="button" (click)="ordersResource.reload()" class="ml-3 underline">Retry</button>
        </div>
      } @else {
        <ul class="divide-y rounded-lg border">
          @for (order of filteredOrders(); track order.id) {
            <li class="flex items-center justify-between p-3">
              <button type="button" (click)="orderSelected.emit(order.id)" class="font-medium hover:underline">
                {{ order.reference }}
              </button>
              <span class="tabular-nums">{{ order.totalCents / 100 | currency:'USD' }}</span>
            </li>
          } @empty {
            <li class="p-6 text-center text-slate-500">No matching orders.</li>
          }
        </ul>
      }

      <!-- Defer heavy analytics chart until scrolled into viewport (with Incremental Hydration) -->
      @defer (on viewport; hydrate on viewport) {
        <app-order-analytics [customerId]="customerId()" />
      } @placeholder {
        <div class="h-48 rounded-lg border border-dashed"></div>
      }
    </section>
  `,
})
export class OrderListComponent {
  readonly customerId = input.required<string>();
  readonly defaultStatus = input<'all' | 'draft' | 'paid' | 'shipped'>('all');
  readonly orderSelected = output<string>();

  // linkedSignal resets automatically whenever defaultStatus input changes
  readonly selectedStatus = linkedSignal(() => this.defaultStatus());

  // Reactive HTTP resource cancels in-flight requests when customerId changes
  readonly ordersResource = httpResource<OrderSummary[]>(() =>
    `/api/v1/customers/${encodeURIComponent(this.customerId())}/orders`
  );

  readonly filteredOrders = computed(() => {
    const items = this.ordersResource.value() ?? [];
    const status = this.selectedStatus();
    return status === 'all' ? items : items.filter((item) => item.status === status);
  });

  onStatusChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value as 'all' | 'draft' | 'paid' | 'shipped';
    this.selectedStatus.set(value);
  }
}
```

---

## 5. Enterprise State with NgRx SignalStore & Functional Guards

```typescript
// src/app/core/auth/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthStore } from './auth.store';

export const requireAuthGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);
  return auth.isAuthenticated() ? true : router.createUrlTree(['/login']);
};
```

- **State Rule**: Use component-local `signal()`/`computed()` first. Promote shared feature state to **NgRx SignalStore** (`signalStore`, `withState`, `withComputed`, `withMethods`, `rxMethod`). Reserve RxJS strictly for true event streams (WebSockets, debounced typeahead, complex cancellation pipelines) and bridge into templates via `toSignal()`.

---

## 6. Security, Performance & Anti-Patterns

| Anti-Pattern | Root Cause | Remediated Standard |
|---|---|---|
| **Mutating state inside `effect()`** | Synchronizing derived values imperatively | Use `computed()` or `linkedSignal()`; keep `effect()` strictly for DOM/logging side effects |
| **Missing `track` key in `@for`** | Tracking by `$index` on reorderable lists | Always track by stable unique identity (`track item.id`) |
| **Unchecked `DomSanitizer.bypassSecurityTrustHtml`** | Rendering user HTML directly (XSS) | Sanitize via DOMPurify + Angular's built-in sanitization and Trusted Types |
| **Unsubscribed RxJS streams** | Calling `.subscribe()` in components without teardown | Use `takeUntilDestroyed()` (`@angular/core/rxjs-interop`) or `toSignal()` |
| **Importing `zone.js` in polyfills** | Keeping legacy change detection active | Remove `zone.js` from `angular.json` polyfills once `provideZonelessChangeDetection()` is verified |

---

## 7. Verification Checklist

- [ ] `strictTemplates`, `strictInjectionParameters`, and TypeScript `strict: true` enabled in `tsconfig.json`.
- [ ] All components are standalone with `ChangeDetectionStrategy.OnPush` and Zoneless bootstrap verified.
- [ ] Zero raw `.subscribe()` leaks (all subscriptions use `toSignal()` or `takeUntilDestroyed()`).
- [ ] Heavy below-the-fold widgets wrapped in `@defer (on viewport)` with incremental hydration.
- [ ] Unit/component tests (`ng test` / Vitest + `@testing-library/angular`) and Playwright E2E pass with Exit Code `0`.
