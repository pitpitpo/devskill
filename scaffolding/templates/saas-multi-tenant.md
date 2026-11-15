# 🏢 SaaS Multi-Tenant Architecture Blueprint

> **Template Type**: Production SaaS Platform  
> **Stack**: Next.js 15 + NestJS/FastAPI + PostgreSQL + Redis + Stripe  
> **Tenant Model**: Schema-per-tenant (hybrid row-level option)  
> **Estimated Setup**: 2-3 weeks for MVP scaffold

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    EDGE / CDN LAYER                              │
│              Cloudflare / Vercel Edge Network                    │
│         (WAF, DDoS Protection, SSL Termination)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   TENANT ROUTER                                  │
│   Subdomain Routing: {tenant}.app.com → Tenant Context          │
│   Custom Domain CNAME: client.com → Tenant Context              │
│   API Key Header: X-Tenant-ID → Validated Against DB            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                 APPLICATION LAYER                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Next.js 15  │  │  API Server  │  │  Background Workers  │  │
│  │  App Router  │  │  NestJS /    │  │  BullMQ / Celery     │  │
│  │  RSC + SSR   │  │  FastAPI     │  │  Email, Billing,     │  │
│  │              │  │              │  │  Reports, Webhooks   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   DATA LAYER                                     │
│                                                                  │
│  ┌───────────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  PostgreSQL   │  │  Redis   │  │  S3/R2   │  │  Stripe   │ │
│  │  Row-Level or │  │  Cache + │  │  Tenant  │  │  Billing  │ │
│  │  Schema-Level │  │  Sessions│  │  Assets  │  │  Engine   │ │
│  │  Isolation    │  │  + Queues│  │          │  │           │ │
│  └───────────────┘  └──────────┘  └──────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Tenant Isolation Strategies

### Strategy Comparison Matrix

| Strategy | Isolation Level | Complexity | Cost per Tenant | Data Migration | Compliance |
|---|---|---|---|---|---|
| **Row-Level Security (RLS)** | Logical | Low | Very Low | Easy | SOC 2 |
| **Schema-per-Tenant** | Medium | Medium | Low | Moderate | SOC 2, HIPAA |
| **Database-per-Tenant** | Physical | High | High | Complex | HIPAA, FedRAMP |
| **Hybrid (RLS + Schema)** | Configurable | Medium | Variable | Moderate | All |

### Recommended: Row-Level Security with PostgreSQL

```sql
-- Enable RLS on all tenant tables
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Policy: tenants can only see their own data
CREATE POLICY tenant_isolation ON invoices
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Force RLS even for table owners
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;

-- Set tenant context at the beginning of each request
-- (in your middleware / connection hook)
SET LOCAL app.current_tenant_id = 'tenant-uuid-here';
```

### Middleware: Tenant Resolution

```typescript
// NestJS Tenant Middleware
@Injectable()
export class TenantMiddleware implements NestMiddleware {
  constructor(
    private readonly tenantService: TenantService,
    private readonly dataSource: DataSource,
  ) {}

  async use(req: Request, res: Response, next: NextFunction) {
    // 1. Resolve tenant from subdomain
    const hostname = req.hostname; // acme.app.com
    const subdomain = hostname.split('.')[0];

    // 2. Lookup tenant (cached in Redis with 5min TTL)
    const tenant = await this.tenantService.resolveBySubdomain(subdomain);
    if (!tenant) {
      throw new NotFoundException('Tenant not found');
    }

    // 3. Check tenant status (active, suspended, trial_expired)
    if (tenant.status !== TenantStatus.ACTIVE) {
      throw new ForbiddenException(`Tenant is ${tenant.status}`);
    }

    // 4. Set tenant context on request
    req['tenant'] = tenant;

    // 5. Set PostgreSQL RLS context
    const queryRunner = this.dataSource.createQueryRunner();
    await queryRunner.query(
      `SET LOCAL app.current_tenant_id = $1`,
      [tenant.id]
    );

    next();
  }
}
```

```python
# FastAPI Tenant Dependency
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Extract and validate tenant from subdomain or API key."""
    # Subdomain resolution
    host = request.headers.get("host", "")
    subdomain = host.split(".")[0]

    # Check Redis cache first
    cached = await redis.get(f"tenant:{subdomain}")
    if cached:
        return Tenant.model_validate_json(cached)

    # Database lookup
    tenant = await db.execute(
        select(Tenant).where(Tenant.subdomain == subdomain)
    )
    tenant = tenant.scalar_one_or_none()

    if not tenant or tenant.status != "active":
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Cache for 5 minutes
    await redis.setex(f"tenant:{subdomain}", 300, tenant.model_dump_json())

    # Set RLS context
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant.id}'"))

    return tenant
```

---

## 3. Database Schema Design

```sql
-- Core tenant table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(63) NOT NULL UNIQUE,
    custom_domain VARCHAR(255) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'trial'
        CHECK (status IN ('trial', 'active', 'suspended', 'cancelled')),
    plan VARCHAR(50) NOT NULL DEFAULT 'free'
        CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255),
    settings JSONB NOT NULL DEFAULT '{}',
    max_users INT NOT NULL DEFAULT 5,
    max_storage_bytes BIGINT NOT NULL DEFAULT 1073741824, -- 1 GB
    trial_ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- All tenant-scoped tables include tenant_id with RLS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_users ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Audit log (append-only, immutable)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant_created ON audit_logs(tenant_id, created_at DESC);
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
```

---

## 4. Billing Integration (Stripe)

### Subscription Lifecycle

```
Trial Start → Trial Warning (3 days left) → Trial Expired
     │                                           │
     ▼                                           ▼
  Checkout → Active Subscription → Invoice Paid  Grace Period (7 days)
                    │                                │
                    ├── Upgrade/Downgrade             ▼
                    ├── Payment Failed → Retry     Suspended
                    └── Cancel → End of Period        │
                                    │                 ▼
                                    ▼              Cancelled (Data retained 30 days)
                              Cancelled                │
                                                       ▼
                                                  Data Purged
```

### Webhook Handler

```typescript
@Controller('webhooks')
export class StripeWebhookController {
  constructor(
    private readonly billingService: BillingService,
    private readonly tenantService: TenantService,
  ) {}

  @Post('stripe')
  async handleStripeWebhook(
    @Req() req: RawBodyRequest<Request>,
    @Headers('stripe-signature') signature: string,
  ) {
    // 1. Verify webhook signature (CRITICAL: prevents forgery)
    const event = this.billingService.constructEvent(
      req.rawBody,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET,
    );

    // 2. Idempotency check (store processed event IDs)
    if (await this.billingService.isEventProcessed(event.id)) {
      return { received: true };
    }

    // 3. Handle event
    switch (event.type) {
      case 'checkout.session.completed':
        await this.billingService.activateSubscription(event.data.object);
        break;

      case 'invoice.payment_succeeded':
        await this.billingService.recordPayment(event.data.object);
        break;

      case 'invoice.payment_failed':
        await this.billingService.handleFailedPayment(event.data.object);
        // Send dunning email, retry logic
        break;

      case 'customer.subscription.updated':
        await this.billingService.syncSubscription(event.data.object);
        break;

      case 'customer.subscription.deleted':
        await this.tenantService.suspendTenant(event.data.object.metadata.tenant_id);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    // 4. Mark event as processed
    await this.billingService.markEventProcessed(event.id);

    return { received: true };
  }
}
```

### Plan Enforcement Middleware

```typescript
@Injectable()
export class PlanLimitGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requiredPlan = this.reflector.get<string[]>('plans', context.getHandler());
    if (!requiredPlan) return true;

    const request = context.switchToHttp().getRequest();
    const tenant: Tenant = request.tenant;

    // Check plan hierarchy: enterprise > pro > starter > free
    const planHierarchy = ['free', 'starter', 'pro', 'enterprise'];
    const tenantPlanIndex = planHierarchy.indexOf(tenant.plan);
    const requiredPlanIndex = Math.min(
      ...requiredPlan.map(p => planHierarchy.indexOf(p))
    );

    if (tenantPlanIndex < requiredPlanIndex) {
      throw new ForbiddenException(
        `This feature requires the ${requiredPlan[0]} plan or higher`
      );
    }

    return true;
  }
}

// Usage
@Get('analytics/export')
@SetMetadata('plans', ['pro'])
async exportAnalytics(@Req() req: Request) {
  // Only accessible to Pro and Enterprise plans
}
```

---

## 5. Onboarding Flow

### Tenant Provisioning Checklist

```typescript
async provisionTenant(dto: CreateTenantDto): Promise<Tenant> {
  return this.dataSource.transaction(async (manager) => {
    // 1. Create tenant record
    const tenant = manager.create(Tenant, {
      name: dto.organizationName,
      subdomain: dto.subdomain,
      plan: 'trial',
      trial_ends_at: addDays(new Date(), 14),
    });
    await manager.save(tenant);

    // 2. Create owner user
    const owner = manager.create(User, {
      tenant_id: tenant.id,
      email: dto.email,
      password_hash: await argon2.hash(dto.password),
      role: 'owner',
    });
    await manager.save(owner);

    // 3. Create Stripe customer
    const stripeCustomer = await this.stripe.customers.create({
      email: dto.email,
      name: dto.organizationName,
      metadata: { tenant_id: tenant.id },
    });
    tenant.stripe_customer_id = stripeCustomer.id;
    await manager.save(tenant);

    // 4. Seed default data (async via queue)
    await this.queue.add('seed-tenant', {
      tenantId: tenant.id,
      template: dto.template || 'default',
    });

    // 5. Send welcome email (async via queue)
    await this.queue.add('send-email', {
      template: 'welcome',
      to: dto.email,
      data: { tenantName: dto.organizationName },
    });

    return tenant;
  });
}
```

---

## 6. Directory Structure

```
saas-platform/
├── apps/
│   ├── web/                          # Next.js 15 App Router
│   │   ├── app/
│   │   │   ├── (auth)/               # Public auth pages
│   │   │   │   ├── login/
│   │   │   │   ├── signup/
│   │   │   │   └── verify-email/
│   │   │   ├── (dashboard)/          # Tenant-scoped authenticated pages
│   │   │   │   ├── layout.tsx        # Tenant context provider
│   │   │   │   ├── overview/
│   │   │   │   ├── settings/
│   │   │   │   │   ├── general/
│   │   │   │   │   ├── billing/
│   │   │   │   │   ├── team/
│   │   │   │   │   └── api-keys/
│   │   │   │   └── [resource]/
│   │   │   ├── (marketing)/          # Public landing pages
│   │   │   │   ├── pricing/
│   │   │   │   └── docs/
│   │   │   └── api/                  # Route Handlers (webhooks, auth callbacks)
│   │   └── middleware.ts             # Tenant resolution, auth checks
│   │
│   └── api/                          # NestJS / FastAPI backend
│       ├── src/
│       │   ├── modules/
│       │   │   ├── tenant/           # Tenant CRUD, provisioning
│       │   │   ├── auth/             # Authentication, session, RBAC
│       │   │   ├── billing/          # Stripe integration, plans
│       │   │   ├── user/             # User management, invitations
│       │   │   └── [domain]/         # Your business domain modules
│       │   ├── common/
│       │   │   ├── guards/           # TenantGuard, RolesGuard, PlanLimitGuard
│       │   │   ├── interceptors/     # TenantContext, Logging, Audit
│       │   │   ├── decorators/       # @CurrentTenant, @RequirePlan
│       │   │   └── middleware/       # TenantMiddleware
│       │   └── infrastructure/
│       │       ├── database/         # Migrations, seeds, RLS policies
│       │       ├── cache/            # Redis tenant-scoped cache
│       │       ├── queue/            # BullMQ job processors
│       │       └── email/            # Transactional email templates
│       └── test/
│
├── packages/
│   ├── shared-types/                 # Shared TypeScript types
│   ├── ui/                           # Shared component library
│   └── config/                       # Shared configs (ESLint, TS, Tailwind)
│
├── infrastructure/
│   ├── terraform/                    # IaC for cloud resources
│   ├── docker/                       # Docker Compose for local dev
│   └── k8s/                          # Kubernetes manifests
│
└── docs/
    ├── api/                          # Auto-generated API docs
    └── architecture/                 # ADRs and diagrams
```

---

## 7. Security Considerations

1. **Tenant Data Isolation**: RLS policies on EVERY tenant-scoped table. No exceptions.
2. **Cross-Tenant Data Leaks**: Integration tests MUST verify that Tenant A cannot access Tenant B data.
3. **Subdomain Validation**: Sanitize subdomains (`^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`), block reserved words (`www`, `api`, `admin`, `app`, `mail`).
4. **Rate Limiting**: Per-tenant rate limits based on plan tier.
5. **Audit Logging**: Every mutation logged with tenant_id, user_id, IP, and timestamp.
6. **Data Deletion**: GDPR right-to-erasure: tenant deletion must cascade to ALL tenant data including S3 objects, Redis keys, and audit logs.

---

## 8. Verification Checklist

- [ ] RLS policies enabled on ALL tenant-scoped tables
- [ ] Cross-tenant access integration tests pass
- [ ] Stripe webhook signature verification active
- [ ] Subdomain validation rejects reserved words and invalid characters
- [ ] Trial expiration cron job scheduled and tested
- [ ] Failed payment dunning emails configured
- [ ] Tenant provisioning is idempotent (retry-safe)
- [ ] Custom domain SSL certificate provisioning automated
- [ ] Audit log captures all security-relevant events
- [ ] Data export (GDPR) endpoint functional
- [ ] Tenant deletion cascades completely (DB, S3, Redis, queues)
