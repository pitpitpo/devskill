# 🏛️ Architecture Blueprint: Enterprise Modular Monolith

> **Standard Identifier**: `SCAF-MODULAR-MONOLITH-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Principal Architects, Lead Engineers, Tech Directors  
> **Classification**: Level 4 Scaffolding & Architecture Blueprint  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Default to a Modular Monolith before microservices. Enforce strict compile-time domain boundaries, isolated database schemas, and asynchronous internal event buses. Gain all the organizational independence of microservices with none of the operational tax of distributed systems.*

Premature microservice decomposition introduces immense operational friction: distributed transactions, network latency, complex observability pipelines, and brittle deployment orchestrations. A Modular Monolith keeps all code in a single deployable artifact while enforcing strict hexagonal boundary rules between domains.

---

## 2. Modular Monolith Architectural Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 API & INGRESS GATEWAY                  │
                  │                 (FastAPI / NestJS / Go)                │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         ▼                                   ▼                                   ▼
  ┌───────────────┐                   ┌───────────────┐                   ┌───────────────┐
  │ IDENTITY DOMAIN│                   │ BILLING DOMAIN│                   │ CATALOG DOMAIN│
  ├───────────────┤                   ├───────────────┤                   ├───────────────┤
  │ • Public API  │                   │ • Public API  │                   │ • Public API  │
  │ • Domain Core │                   │ • Domain Core │                   │ • Domain Core │
  │ • Postgres DB │                   │ • Postgres DB │                   │ • Postgres DB │
  │   schema:     │                   │   schema:     │                   │   schema:     │
  │   "identity"  │                   │   "billing"   │                   │   "catalog"   │
  └───────┬───────┘                   └───────┬───────┘                   └───────┬───────┘
          │                                   │                                   │
          └───────────────────────────────────┼───────────────────────────────────┘
                                              │ In-Memory Asynchronous Event Bus
                                              ▼
                             ┌─────────────────────────────────┐
                             │       DOMAIN EVENT DISPATCHER   │
                             │     (Transactional Outbox)      │
                             └─────────────────────────────────┘
```

---

## 3. The 4 Non-Negotiable Boundary Rules

1. **Schema Isolation**: Each module owns its dedicated database schema (`identity.*`, `billing.*`). Modules are strictly forbidden from executing SQL `JOIN` statements across schema boundaries.
2. **Public Interface Contracts**: Modules interact exclusively through designated public service interfaces or internal APIs (`IdentityModuleAPI`). Internal entities, models, and repositories are private.
3. **Asynchronous Cross-Domain Events**: When Domain A needs to trigger side effects in Domain B (e.g. `UserRegistered` -> create billing account), it emits an in-memory Domain Event. Never invoke synchronous business mutation methods across domains.
4. **Zero Circular Dependencies**: Dependency flow must be strictly acyclic. If Module A imports Module B, Module B must never import Module A (enforced via ESLint / ArchUnit rules).

---

## 4. Production Implementation: Domain Events & Transactional Outbox

```typescript
// packages/core/events/DomainEventBus.ts
export interface DomainEvent<T = any> {
  id: string;
  eventType: string;
  occurredAt: Date;
  payload: T;
}

export type EventHandler<T> = (event: DomainEvent<T>) => Promise<void>;

export class InMemoryEventBus {
  private handlers = new Map<string, EventHandler<any>[]>();

  subscribe<T>(eventType: string, handler: EventHandler<T>): void {
    const list = this.handlers.get(eventType) || [];
    list.push(handler);
    this.handlers.set(eventType, list);
  }

  async publish<T>(event: DomainEvent<T>): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || [];
    // Dispatch asynchronously without blocking caller
    for (const handler of handlers) {
      handler(event).catch((err) => {
        console.error(`[EventBus] Handler failed for ${event.eventType}:`, err);
      });
    }
  }
}
```

---

## 5. Directory Layout & Scaffolding Standard

```
src/
├── app.ts                  # Application entry point & module wiring
├── modules/
│   ├── identity/           # Identity Bounded Context
│   │   ├── index.ts        # Public API exports (Only what others can import)
│   │   ├── domain/         # Domain Entities, Value Objects, Business Rules
│   │   ├── application/    # Use Cases, Command Handlers
│   │   └── infrastructure/ # Database models (schema: identity), Repositories
│   ├── billing/            # Billing Bounded Context
│   │   ├── index.ts        # Public API exports
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/ # Database models (schema: billing)
│   └── catalog/            # Catalog Bounded Context
└── shared/
    ├── event-bus/          # In-memory domain event dispatcher
    ├── database/           # Base pool connection & migration harness
    └── telemetry/          # OpenTelemetry providers
```

---

## 6. Migration Blueprint: When and How to Extract a Microservice

When a module experiences radically different scaling requirements or requires a separate team deployment lifecycle:
1. Since the module already owns its database schema and communicates via public interfaces/events, extraction is mechanical:
2. Swap the in-memory event bus subscriber for a message broker (RabbitMQ/Kafka).
3. Deploy the module code as an independent container service with its own database connection string.
4. Replace the internal module import in the monolith with an HTTP/gRPC client conforming to the exact same TypeScript interface.

---


---


---

## 5. Security & Performance Considerations

| Category | Focus Area | Production Standard |
| :--- | :--- | :--- |
| **Cross-Module Authorization** | Security Boundary | Modules must enforce independent permission guards; identity tokens must be passed and validated at public module interfaces |
| **In-Memory Event Bus Saturation** | Performance & Backpressure | Bound asynchronous event queues; if event volume exceeds 1,000/s, transition dispatcher to Redis or Kafka broker |
| **Schema Connection Sizing** | Database Isolation | Slices of the connection pool must be calibrated so high-activity modules (e.g. catalog) cannot starve critical modules (billing) |

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Cross-Schema SQL Joins** | Querying another module's database tables | Destroys domain boundaries; impossible to extract into microservice | Communicate exclusively via module APIs or async domain events |
| **Direct Entity Mutation** | Module A calling `db.update(ModuleBEntity)` | Undocumented side effects, broken invariants, high coupling | Modules mutate only their own domain aggregates |
| **Circular Module Dependencies** | Module A imports B; Module B imports A | Spaghetti architecture, build-time cyclic import errors | Enforce unidirectional dependency flow; extract shared types |

## 7. Verification Checklist & Production Audit

- [ ] Linter rules (`eslint-plugin-boundaries` or ArchUnit) fail CI on cross-module internal file imports.
- [ ] Database migrations maintain separate schema namespaces per domain.
- [ ] Cross-domain writes utilize asynchronous domain events rather than direct mutation calls.
- [ ] Circular dependencies between modules are strictly zero.
- [ ] Public API contracts (`index.ts`) expose only scalar DTOs and interface abstractions.
