# 🏛️ Enterprise Modular Monolith Blueprint (`enterprise-modular-monolith.md`)

> **Architecture**: Modular Monolith (Clean / Hexagonal Architecture)  
> **Use Case**: Core enterprise platforms, complex SaaS, high-cohesion systems

---

## 1. Domain Boundary Rules

1. Each module (e.g. `billing`, `identity`, `inventory`) is a self-contained bounded context.
2. **Never cross database table boundaries directly**:
   - Module A may NOT query Module B's database tables directly.
   - Module A must call Module B's public domain service interface or subscribe to an in-process domain event.
3. In-process communication uses domain event dispatchers (`MediatR` in C#, `EventEmitter2` in Node, `pydispatcher` in Python).

```
src/
├── modules/
│   ├── identity/
│   │   ├── domain/           # Entities, value objects, domain logic
│   │   ├── application/      # Use cases, DTOs, service contracts
│   │   ├── infrastructure/   # Repositories, DB models, external clients
│   │   └── api/              # Controllers / HTTP routers
│   ├── billing/
│   └── catalog/
├── shared/                   # Shared kernel (Result type, EventBus, Money)
└── main.ts                   # Unified application bootstrap
```
