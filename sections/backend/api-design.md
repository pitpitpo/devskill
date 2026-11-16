# 🌐 Production API Design Standards (`api-design.md`)

> **Classification**: Global API Contract & Communication Standard  
> **Applicability**: Public and Private RESTful, GraphQL, and gRPC Services  
> **Last Updated**: 2026-11

---

## 1. Overview — When to Use This Guide

Use this guide when:
- Designing a new REST, GraphQL, or gRPC API from scratch
- Reviewing an existing API for production readiness
- Choosing between API paradigms (REST vs GraphQL vs gRPC)
- Implementing cross-cutting concerns (auth, rate limiting, versioning)
- Generating SDKs or writing OpenAPI specifications
- Establishing team-wide API design conventions

**Core Philosophy**: APIs are contracts. Changing them is expensive, breaking them is unacceptable. Design for the consumer, not the implementation.

---

## 2. Core Concepts & Architecture

### 2.1 API Design Principles

1. **Consumer-First Design** — Design from the caller's perspective, not your database schema
2. **Consistency Over Cleverness** — Follow conventions; surprise is a defect
3. **Evolvability** — Design so you can add without breaking
4. **Least Privilege** — Expose the minimum data needed per endpoint
5. **Idempotency by Default** — Safe retries are a requirement, not a feature

### 2.2 Resource-Oriented Architecture

```
Resource Model (Nouns, not Verbs):

  ✅  GET    /v1/users/{userId}/orders          → List user's orders
  ✅  POST   /v1/orders                          → Create an order
  ✅  PATCH  /v1/orders/{orderId}                → Partially update an order
  ✅  DELETE /v1/orders/{orderId}                → Delete an order

  ❌  POST   /v1/getOrders                       → Verb-based (RPC smell)
  ❌  POST   /v1/deleteOrder                     → Should be DELETE method
  ❌  GET    /v1/users/{userId}/getOrderHistory  → Redundant verb
```

### 2.3 Resource Naming Conventions

| Rule | Example | Anti-Pattern |
|------|---------|--------------|
| Plural nouns for collections | `/users`, `/orders` | `/user`, `/order` |
| Lowercase with hyphens | `/line-items` | `/lineItems`, `/line_items` |
| No trailing slashes | `/users` | `/users/` |
| Nest for true parent-child | `/users/{id}/addresses` | `/user-addresses` |
| Max 2 levels of nesting | `/users/{id}/orders` | `/users/{id}/orders/{oid}/items/{iid}/reviews` |
| Singular for singletons | `/users/{id}/profile` | `/users/{id}/profiles` |
| Actions as sub-resources | `POST /orders/{id}/cancel` | `POST /cancelOrder` |

---

## 3. Unified HTTP Status Code Matrix

| Code | Meaning | When to Use |
|------|---------|-------------|
| **200 OK** | Success with payload | Successful `GET`, `PUT`, or `PATCH` returning resource |
| **201 Created** | Resource created | Successful `POST` returning newly created resource + `Location` header |
| **202 Accepted** | Async processing started | Long-running operations, job submitted |
| **204 No Content** | Action completed without payload | Successful `DELETE` or empty mutation |
| **301 Moved Permanently** | Permanent redirect | Renamed endpoint (update bookmarks) |
| **304 Not Modified** | Conditional GET cache hit | `ETag`/`If-None-Match` validation |
| **400 Bad Request** | Malformed syntax | Malformed JSON or unparseable headers |
| **401 Unauthorized** | Authentication missing/invalid | Missing Bearer token, expired session |
| **403 Forbidden** | Authenticated but unauthorized | User does not have RBAC permission |
| **404 Not Found** | Resource does not exist | Invalid ID or hidden ID for security isolation |
| **405 Method Not Allowed** | Wrong HTTP method | `DELETE` on a read-only resource |
| **409 Conflict** | State collision | Unique constraint violation, concurrent edit |
| **410 Gone** | Resource permanently deleted | Deprecated endpoints after sunset date |
| **413 Payload Too Large** | Body exceeds limit | File upload exceeding max size |
| **415 Unsupported Media Type** | Wrong Content-Type | XML sent to JSON-only endpoint |
| **422 Unprocessable Entity** | Schema validation error | Valid JSON but failed business validation |
| **429 Too Many Requests** | Rate limit exceeded | Throttled by IP or account quota |
| **500 Internal Server Error** | Unhandled crash | System exception (never expose stack trace) |
| **502 Bad Gateway** | Upstream failure | Database or downstream service unreachable |
| **503 Service Unavailable** | Temporarily overloaded | Include `Retry-After` header |
| **504 Gateway Timeout** | Upstream timeout | Downstream took too long |

---

## 4. Standardized Error Envelope (RFC 9457)

All error responses **MUST** conform to the RFC 9457 Problem Details standard:

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "One or more fields failed validation checks.",
  "instance": "/v1/orders/create",
  "traceId": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "invalidParams": [
    {
      "name": "quantity",
      "reason": "Must be greater than zero"
    },
    {
      "name": "email",
      "reason": "Must be a valid email address"
    }
  ]
}
```

### Error Type Registry

Maintain a central error type registry in your OpenAPI spec:

```yaml
# openapi.yaml — components/schemas
ErrorTypes:
  validation-failed:
    uri: "https://api.example.com/errors/validation-failed"
    title: "Validation Failed"
    status: 422
  insufficient-funds:
    uri: "https://api.example.com/errors/insufficient-funds"
    title: "Insufficient Funds"
    status: 422
  rate-limited:
    uri: "https://api.example.com/errors/rate-limited"
    title: "Rate Limit Exceeded"
    status: 429
```

### Implementation Pattern (Node.js / Express)

```typescript
// errors/ApiError.ts
export class ApiError extends Error {
  constructor(
    public readonly type: string,
    public readonly title: string,
    public readonly status: number,
    public readonly detail: string,
    public readonly extensions: Record<string, unknown> = {}
  ) {
    super(detail);
    this.name = 'ApiError';
  }

  toRFC9457(instance: string, traceId: string) {
    return {
      type: `https://api.example.com/errors/${this.type}`,
      title: this.title,
      status: this.status,
      detail: this.detail,
      instance,
      traceId,
      ...this.extensions,
    };
  }
}

// middleware/errorHandler.ts
export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  const traceId = req.headers['x-trace-id'] as string || generateTraceId();

  if (err instanceof ApiError) {
    return res.status(err.status).json(
      err.toRFC9457(req.originalUrl, traceId)
    );
  }

  // Unknown errors — NEVER leak stack traces in production
  logger.error('Unhandled error', { error: err, traceId, path: req.originalUrl });
  return res.status(500).json({
    type: 'https://api.example.com/errors/internal',
    title: 'Internal Server Error',
    status: 500,
    detail: 'An unexpected error occurred. Please contact support.',
    instance: req.originalUrl,
    traceId,
  });
}
```

---

## 5. API Versioning

### 5.1 Versioning Strategies Comparison

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| **URL Path** (recommended) | `/v1/users` | Obvious, easy routing, cacheable | URL pollution, can't version individual fields |
| **Header** | `Accept: application/vnd.api+json;version=1` | Clean URLs | Hidden, harder to test, proxy issues |
| **Query Parameter** | `/users?version=1` | Easy to switch | Not RESTful, cache key complexity |
| **Content Negotiation** | `Accept: application/vnd.myapi.v2+json` | Proper HTTP semantics | Complex, poor tooling support |

### 5.2 Version Lifecycle

```
              ┌─────────────────────────────────────────┐
              │          VERSION LIFECYCLE               │
              │                                         │
   Alpha ──► Beta ──► GA (Stable) ──► Deprecated ──► Sunset
   (internal) (preview)  (production)   (warnings)   (410 Gone)
              │                         │              │
              │                         │  Sunset-Date │
              │                         │  header      │
              │                     12+ months         │
              │                     deprecation        │
              │                     notice             │
              └─────────────────────────────────────────┘
```

### 5.3 Backward Compatibility Rules

**Safe Changes** (non-breaking):
- Adding new optional fields to response bodies
- Adding new endpoints
- Adding new optional query parameters
- Adding new enum values (if clients handle unknown values)
- Adding new HTTP methods to existing resources

**Breaking Changes** (require new version):
- Removing or renaming fields
- Changing field types
- Making optional fields required
- Changing URL structure
- Modifying error response format
- Changing authentication mechanism
- Altering pagination behavior

```typescript
// Deprecation header middleware
function deprecationHeaders(sunsetDate: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    res.setHeader('Deprecation', 'true');
    res.setHeader('Sunset', sunsetDate); // RFC 8594
    res.setHeader('Link', '<https://api.example.com/v2/docs>; rel="successor-version"');
    next();
  };
}

// Usage:
app.use('/v1/', deprecationHeaders('Sat, 01 Mar 2027 00:00:00 GMT'));
```

---

## 6. Pagination

### 6.1 Keyset / Cursor Pagination (Recommended)

Offset-based pagination (`OFFSET 10000 LIMIT 20`) degrades on large datasets (O(N) scan). Keyset pagination uses indexed columns for O(1) time:

```http
GET /v1/transactions?limit=20&cursor=eyJpZCI6MTAyOSwiY3JlYXRlZF9hdCI6MTY5ODc2NX0=
```

#### Response Envelope:

```json
{
  "data": [ ... ],
  "pagination": {
    "limit": 20,
    "hasMore": true,
    "nextCursor": "eyJpZCI6MTA0OSwiY3JlYXRlZF9hdCI6MTY5ODgyMH0=",
    "prevCursor": "eyJpZCI6MTAyOSwiY3JlYXRlZF9hdCI6MTY5ODc2NX0="
  }
}
```

#### Server-Side Implementation:

```python
import base64
import json
from datetime import datetime

def encode_cursor(order_id: int, created_at: datetime) -> str:
    payload = {"id": order_id, "created_at": created_at.isoformat()}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

def decode_cursor(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())

def paginate_orders(cursor: str | None, limit: int = 20):
    query = db.query(Order).order_by(Order.created_at.desc(), Order.id.desc())

    if cursor:
        decoded = decode_cursor(cursor)
        query = query.filter(
            db.or_(
                Order.created_at < decoded["created_at"],
                db.and_(
                    Order.created_at == decoded["created_at"],
                    Order.id < decoded["id"]
                )
            )
        )

    # Fetch limit + 1 to determine hasMore
    results = query.limit(limit + 1).all()
    has_more = len(results) > limit
    items = results[:limit]

    return {
        "data": [serialize(item) for item in items],
        "pagination": {
            "limit": limit,
            "hasMore": has_more,
            "nextCursor": encode_cursor(items[-1].id, items[-1].created_at) if has_more else None,
        }
    }
```

### 6.2 Pagination Strategy Decision Matrix

| Criteria | Cursor/Keyset | Offset/Limit | Page Number |
|----------|---------------|--------------|-------------|
| Large datasets (100K+) | ✅ Best | ❌ Degrades | ❌ Degrades |
| Random page access | ❌ No | ✅ Yes | ✅ Yes |
| Real-time data with inserts | ✅ Stable | ❌ Duplicates/skips | ❌ Duplicates/skips |
| SEO-friendly URLs | ❌ Opaque tokens | ⚠️ OK | ✅ Best |
| Total count needed | ⚠️ Requires extra query | ✅ Natural | ✅ Natural |
| Implementation complexity | Medium | Low | Low |

---

## 7. Filtering, Sorting & Field Selection

### 7.1 Filtering

```http
# Equality
GET /v1/orders?status=shipped

# Multiple values (OR)
GET /v1/orders?status=shipped,delivered

# Range (with operators)
GET /v1/orders?created_at[gte]=2026-01-01&created_at[lt]=2026-02-01
GET /v1/orders?total[gte]=100&total[lte]=500

# Full-text search
GET /v1/products?q=wireless+headphones
```

### 7.2 Sorting

```http
# Single sort
GET /v1/orders?sort=-created_at          # Descending (prefix -)
GET /v1/orders?sort=total                # Ascending (default)

# Multi-sort (comma-separated)
GET /v1/orders?sort=-created_at,total    # Primary: newest first, secondary: lowest total
```

### 7.3 Sparse Field Selection

```http
# Only return specified fields (reduce payload size)
GET /v1/users?fields=id,name,email

# Nested field selection
GET /v1/orders?fields=id,total,customer.name
```

### 7.4 Implementation Pattern (TypeORM)

```typescript
function buildQuery(repo: Repository<Order>, params: QueryParams) {
  const qb = repo.createQueryBuilder('order');

  // Filtering
  if (params.status) {
    const statuses = params.status.split(',');
    qb.andWhere('order.status IN (:...statuses)', { statuses });
  }

  if (params.created_at_gte) {
    qb.andWhere('order.createdAt >= :from', { from: params.created_at_gte });
  }

  if (params.created_at_lt) {
    qb.andWhere('order.createdAt < :to', { to: params.created_at_lt });
  }

  // Sorting — validate against allowlist to prevent SQL injection
  const SORTABLE_FIELDS = new Set(['createdAt', 'total', 'status']);
  if (params.sort) {
    for (const clause of params.sort.split(',')) {
      const desc = clause.startsWith('-');
      const field = desc ? clause.slice(1) : clause;
      const camelField = snakeToCamel(field);
      if (!SORTABLE_FIELDS.has(camelField)) {
        throw new ApiError('invalid-sort', 'Invalid Sort Field', 400,
          `Cannot sort by '${field}'. Allowed: ${[...SORTABLE_FIELDS].join(', ')}`);
      }
      qb.addOrderBy(`order.${camelField}`, desc ? 'DESC' : 'ASC');
    }
  }

  // Field selection
  if (params.fields) {
    const SELECTABLE = new Set(['id', 'total', 'status', 'createdAt']);
    const fields = params.fields.split(',')
      .map(f => snakeToCamel(f.trim()))
      .filter(f => SELECTABLE.has(f))
      .map(f => `order.${f}`);
    qb.select(fields);
  }

  return qb;
}
```

---

## 8. Idempotency Key Architecture & Webhook Security

### 8.1 Stripe / IETF Idempotency Key Standard

Mutating requests (`POST`, `PUT`, `PATCH`) handling financial transactions, order placement, or critical state transitions must support the IETF `Idempotency-Key` header to ensure safe retries without duplicate side effects:

```
Client ────── POST /v1/payments [Idempotency-Key: uuid-v4] ──────► API Gateway
                                                                        │
                                                         Compute SHA-256(Body)
                                                                        │
                                                          Check Redis for key
                                                                        ├── If exists + Fingerprint Mismatch: Return 422 Unprocessable Entity
                                                                        ├── If exists + IN_PROGRESS: Return 409 Conflict
                                                                        ├── If exists + COMPLETED: Return cached status code & body
                                                                        └── If new:
                                                                             1. Atomically acquire lock: SET NX EX 120 (status="IN_PROGRESS")
                                                                             2. Execute payment transaction in DB
                                                                             3. Cache final response in Redis (status="COMPLETED", TTL: 24h)
                                                                             4. Return response to Client
```

#### Production Idempotency Middleware Implementation:

```typescript
// middleware/idempotency.ts
import crypto from "node:crypto";
import type { Request, Response, NextFunction } from "express";
import type { Redis } from "ioredis";

interface IdempotencyRecord {
  status: "IN_PROGRESS" | "COMPLETED";
  requestHash: string;
  statusCode?: number;
  headers?: Record<string, string>;
  body?: unknown;
}

export function idempotencyMiddleware(redis: Redis, ttlSeconds = 86400) {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    if (req.method !== "POST" && req.method !== "PUT" && req.method !== "PATCH") {
      return next();
    }

    const idempotencyKey = req.headers["idempotency-key"];
    if (!idempotencyKey || typeof idempotencyKey !== "string") {
      return next();
    }

    // Compute deterministic SHA-256 hash of the request body
    const rawBody = JSON.stringify(req.body ?? {});
    const requestHash = crypto.createHash("sha256").update(rawBody).digest("hex");
    const cacheKey = `idempotency:${req.baseUrl}${req.path}:${idempotencyKey}`;

    // Atomically acquire lock
    const initialRecord: IdempotencyRecord = {
      status: "IN_PROGRESS",
      requestHash,
    };

    const acquired = await redis.set(
      cacheKey,
      JSON.stringify(initialRecord),
      "EX",
      120, // 2-minute lock for in-flight requests
      "NX"
    );

    if (!acquired) {
      const cached = await redis.get(cacheKey);
      if (!cached) {
        res.status(500).json({
          type: "https://api.example.com/errors/internal-error",
          title: "Idempotency State Error",
          status: 500,
          detail: "Unable to determine idempotency state. Please retry.",
        });
        return;
      }

      const existingRecord: IdempotencyRecord = JSON.parse(cached);

      // Verify payload fingerprint: rejecting key reuse with mismatched payloads
      if (existingRecord.requestHash !== requestHash) {
        res.status(422).json({
          type: "https://api.example.com/errors/idempotency-payload-mismatch",
          title: "Idempotency Key Conflict",
          status: 422,
          detail: "Idempotency key was previously used with a different request payload.",
        });
        return;
      }

      if (existingRecord.status === "IN_PROGRESS") {
        res.status(409).json({
          type: "https://api.example.com/errors/idempotency-conflict",
          title: "Request In Progress",
          status: 409,
          detail: "A request with this idempotency key is currently being processed.",
        });
        return;
      }

      // Return cached completed response
      res.status(existingRecord.statusCode ?? 200).json(existingRecord.body);
      return;
    }

    // Intercept response to cache upon completion
    const originalJson = res.json.bind(res);
    res.json = (body: unknown): Response => {
      // Evict transient 5xx server errors so clients can retry without being locked out
      if (res.statusCode >= 500) {
        redis.del(cacheKey).catch(() => {});
        return originalJson(body);
      }

      const completedRecord: IdempotencyRecord = {
        status: "COMPLETED",
        requestHash,
        statusCode: res.statusCode,
        body,
      };

      // Store cached response asynchronously
      redis.set(cacheKey, JSON.stringify(completedRecord), "EX", ttlSeconds).catch(() => {});

      return originalJson(body);
    };

    next();
  };
}
```

---

### 8.2 Webhook Cryptographic Signature Verification (Stripe Standard)

When exposing webhook endpoints to receive asynchronous events from third-party systems (Stripe, GitHub, Shopify), services **MUST** verify cryptographic HMAC signatures using constant-time comparisons and enforce timestamp replay protection.

#### Header Format:
```http
Stripe-Signature: t=1710500000,v1=5257a869e7eceefe225b394441574701e2c7594f007a93c6966f928809821379
```

#### Verification Protocol:
1. **Extract Timestamp & Signature**: Parse `t=<timestamp>` and `v1=<signature>`.
2. **Replay Window Tolerance**: Reject requests where `|currentTime - timestamp| > 300` (5 minutes) with HTTP 400.
3. **Construct Signed Payload**: Combine `${timestamp}.${rawBody}`.
4. **Compute Expected HMAC-SHA256**: Sign using endpoint shared secret.
5. **Constant-Time Comparison**: Use `crypto.timingSafeEqual` to prevent timing attacks.

```typescript
// middleware/webhook-verifier.ts
import crypto from "node:crypto";
import type { Request, Response, NextFunction } from "express";

export function verifyWebhookSignature(endpointSecret: string, toleranceSeconds = 300) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const signatureHeader = req.headers["stripe-signature"];
    if (!signatureHeader || typeof signatureHeader !== "string") {
      res.status(401).json({
        type: "https://api.example.com/errors/missing-webhook-signature",
        title: "Missing Webhook Signature",
        status: 401,
        detail: "The request is missing the required Stripe-Signature header.",
      });
      return;
    }

    // Parse header: t=12345,v1=abcdef...,v1=dualKeySignature...
    const elements = signatureHeader.split(",");
    const timestampStr = elements.find((e) => e.startsWith("t="))?.slice(2);
    const candidateSignatures = elements
      .filter((e) => e.startsWith("v1="))
      .map((e) => e.slice(3));

    if (!timestampStr || candidateSignatures.length === 0) {
      res.status(400).json({
        type: "https://api.example.com/errors/malformed-webhook-signature",
        title: "Malformed Webhook Signature",
        status: 400,
        detail: "The Stripe-Signature header is missing timestamp or v1 signatures.",
      });
      return;
    }

    const timestamp = Number.parseInt(timestampStr, 10);
    if (Number.isNaN(timestamp)) {
      res.status(400).json({
        type: "https://api.example.com/errors/invalid-signature-timestamp",
        title: "Invalid Webhook Timestamp",
        status: 400,
        detail: "The signature timestamp must be a valid numeric Unix timestamp.",
      });
      return;
    }

    const now = Math.floor(Date.now() / 1000);

    // Enforce 300s replay attack window
    if (Math.abs(now - timestamp) > toleranceSeconds) {
      res.status(400).json({
        type: "https://api.example.com/errors/webhook-timestamp-expired",
        title: "Webhook Timestamp Expired",
        status: 400,
        detail: `Webhook timestamp differs from server time by more than ${toleranceSeconds} seconds.`,
      });
      return;
    }

    // Raw body buffer is strictly required (do not use parsed JSON)
    const rawBody = (req as unknown as { rawBody?: Buffer }).rawBody;
    if (!rawBody) {
      res.status(500).json({
        type: "https://api.example.com/errors/webhook-raw-body-missing",
        title: "Raw Body Missing",
        status: 500,
        detail: "Server failed to preserve raw request body buffer required for HMAC verification.",
      });
      return;
    }

    const signedPayload = `${timestamp}.${rawBody.toString("utf8")}`;
    const expectedSignature = crypto
      .createHmac("sha256", endpointSecret)
      .update(signedPayload)
      .digest("hex");

    const expectedBuffer = Buffer.from(expectedSignature, "hex");

    // Guard against timing attacks; iterate through candidates to support key rotation
    const signatureValid = candidateSignatures.some((candidate) => {
      const candidateBuffer = Buffer.from(candidate, "hex");
      return (
        candidateBuffer.length === expectedBuffer.length &&
        crypto.timingSafeEqual(candidateBuffer, expectedBuffer)
      );
    });

    if (!signatureValid) {
      res.status(401).json({
        type: "https://api.example.com/errors/invalid-webhook-signature",
        title: "Invalid Cryptographic Signature",
        status: 401,
        detail: "No signature in header matched the expected HMAC-SHA256 signature.",
      });
      return;
    }

    next();
  };
}
```

---

## 9. Authentication & Authorization Patterns

### 9.1 Pattern Comparison

| Pattern | Use Case | Token Lifetime | Revocability |
|---------|----------|----------------|--------------|
| **API Keys** | Server-to-server, third-party integrations | Long-lived (rotate quarterly) | Instant (database lookup) |
| **OAuth 2.0 + PKCE** | User-facing apps, third-party auth | Short access (15m), long refresh (7d) | Revoke refresh token |
| **JWT (stateless)** | Microservice-to-microservice | Short (5-15 min) | Cannot revoke (use short TTL + blocklist) |
| **Session Cookies** | Traditional web apps | Server-controlled | Instant (destroy session) |
| **mTLS** | Infrastructure, zero-trust networking | Certificate-based | Revoke via CRL/OCSP |

### 9.2 JWT Best Practices

```typescript
// Token generation
import jwt from 'jsonwebtoken';

function generateTokenPair(user: User) {
  const accessToken = jwt.sign(
    {
      sub: user.id,
      email: user.email,
      roles: user.roles,           // Include minimal claims
      // aud: 'https://api.example.com',  // Audience
      iss: 'https://auth.example.com',    // Issuer
    },
    process.env.JWT_PRIVATE_KEY!,
    {
      algorithm: 'ES256',          // Use ECDSA, NOT HS256 for production
      expiresIn: '15m',           // Short-lived access token
      jwtid: crypto.randomUUID(), // Unique token ID for blocklisting
    }
  );

  const refreshToken = jwt.sign(
    { sub: user.id, type: 'refresh' },
    process.env.JWT_REFRESH_KEY!,
    {
      algorithm: 'ES256',
      expiresIn: '7d',
    }
  );

  return { accessToken, refreshToken };
}
```

### 9.3 API Key Design

```
Format:   sk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
          ├─ prefix (sk = secret key)
          ├─ environment (live / test)
          └─ 32-character random hex string

Storage:  Hash the key (SHA-256) before storing in the database.
          Only show the full key ONCE on creation.

Headers:  Authorization: Bearer sk_live_a1b2c3...
          X-API-Key: sk_live_a1b2c3...  (alternative)
```

```python
import hashlib
import secrets

def generate_api_key(environment: str = "live") -> tuple[str, str]:
    """Returns (display_key, hashed_key_for_storage)."""
    raw = secrets.token_hex(32)
    display_key = f"sk_{environment}_{raw}"
    hashed = hashlib.sha256(display_key.encode()).hexdigest()
    return display_key, hashed

def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    computed = hashlib.sha256(provided_key.encode()).hexdigest()
    return hmac.compare_digest(computed, stored_hash)  # Timing-safe comparison
```

---

## 10. Rate Limiting

### 10.1 Rate Limit Headers (IETF Draft)

```http
HTTP/1.1 200 OK
RateLimit-Limit: 1000
RateLimit-Remaining: 742
RateLimit-Reset: 1698876543
Retry-After: 30          # Only on 429 responses
```

### 10.2 Token Bucket Implementation (Redis)

```lua
-- rate_limit.lua — Atomic Redis script
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])     -- Bucket capacity
local refill_rate = tonumber(ARGV[2])    -- Tokens per second
local now = tonumber(ARGV[3])            -- Current timestamp (ms)
local requested = tonumber(ARGV[4])      -- Tokens to consume (usually 1)

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens based on elapsed time
local elapsed = (now - last_refill) / 1000
local new_tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

if new_tokens >= requested then
  new_tokens = new_tokens - requested
  redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
  redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) + 1)
  return {1, math.floor(new_tokens), 0}  -- allowed, remaining, retry_after
else
  local retry_after = math.ceil((requested - new_tokens) / refill_rate)
  return {0, 0, retry_after}  -- denied, remaining, retry_after
end
```

### 10.3 Rate Limit Tiers

| Tier | Limit | Window | Use Case |
|------|-------|--------|----------|
| Anonymous | 60 req | per minute | Unauthenticated public access |
| Free | 1,000 req | per hour | Free-tier users |
| Pro | 10,000 req | per hour | Paid users |
| Enterprise | 100,000 req | per hour | Enterprise contracts |
| Webhook delivery | 500 req | per second | Internal system-to-system |

---

## 11. OpenAPI 3.1 Specification

### 11.1 Specification Structure

```yaml
openapi: "3.1.0"
info:
  title: Orders API
  version: "1.0.0"
  description: |
    Production-grade order management API.
  contact:
    name: Platform Team
    email: platform@example.com
  license:
    name: MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

paths:
  /orders:
    get:
      operationId: listOrders
      summary: List orders with filtering and pagination
      tags: [Orders]
      parameters:
        - $ref: '#/components/parameters/CursorParam'
        - $ref: '#/components/parameters/LimitParam'
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, shipped, delivered, cancelled]
      responses:
        '200':
          description: Paginated list of orders
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'

    post:
      operationId: createOrder
      summary: Create a new order
      tags: [Orders]
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Order created
          headers:
            Location:
              schema:
                type: string
              description: URL of the created resource
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '422':
          $ref: '#/components/responses/ValidationError'

components:
  parameters:
    CursorParam:
      name: cursor
      in: query
      description: Opaque pagination cursor
      schema:
        type: string
    LimitParam:
      name: limit
      in: query
      description: Number of items per page
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20

  schemas:
    Order:
      type: object
      required: [id, status, total, createdAt]
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
          enum: [pending, shipped, delivered, cancelled]
        total:
          type: number
          format: decimal
          description: Order total in cents
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
          default: USD
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    ValidationError:
      description: Validation failed
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    RateLimited:
      description: Rate limit exceeded
      headers:
        Retry-After:
          schema:
            type: integer
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    apiKey:
      type: apiKey
      in: header
      name: X-API-Key

security:
  - bearerAuth: []
  - apiKey: []
```

---

## 12. GraphQL vs REST vs gRPC — Decision Matrix

| Criteria | REST | GraphQL | gRPC |
|----------|------|---------|------|
| **Best for** | Public APIs, CRUD resources | Complex client-driven queries | Internal microservices |
| **Data fetching** | Fixed shape per endpoint | Client specifies exact fields | Protobuf-defined messages |
| **Over-fetching** | Common problem | ✅ Solved by design | ✅ Minimal by schema |
| **Under-fetching** | Multiple round trips | ✅ Single query | Defined per RPC |
| **Caching** | ✅ Native HTTP caching | ❌ Complex (POST-based) | ❌ Custom required |
| **Real-time** | SSE / WebSocket (separate) | ✅ Subscriptions built-in | ✅ Bidirectional streaming |
| **File uploads** | ✅ Multipart native | ⚠️ Workarounds needed | ✅ Streaming support |
| **Browser support** | ✅ Universal | ✅ Universal | ❌ Requires grpc-web proxy |
| **Tooling maturity** | ✅ Excellent | ✅ Good | ⚠️ Growing |
| **Learning curve** | Low | Medium | High |
| **Contract enforcement** | OpenAPI (optional) | ✅ Schema required | ✅ Protobuf required |
| **Performance** | Good | Good (watch N+1) | ✅ Best (binary protocol) |
| **API versioning** | URL-based versioning | Schema evolution | Protobuf field numbering |

### When to Choose What

```
Choose REST when:
  → Building public APIs for third-party developers
  → CRUD operations dominate
  → HTTP caching is critical
  → You need maximum ecosystem compatibility

Choose GraphQL when:
  → Multiple clients need different data shapes (mobile vs web)
  → You have deeply nested, relational data
  → Reducing network round trips is critical
  → You need real-time subscriptions

Choose gRPC when:
  → Internal service-to-service communication
  → Ultra-low latency is required
  → You need bidirectional streaming
  → Strong typing and code generation are priorities
  → Bandwidth optimization matters (binary protocol)
```

---

## 13. HATEOAS (Hypermedia)

For APIs that benefit from discoverability, include navigation links:

```json
{
  "data": {
    "id": "ord_12345",
    "status": "shipped",
    "total": 4999
  },
  "_links": {
    "self": { "href": "/v1/orders/ord_12345" },
    "cancel": { "href": "/v1/orders/ord_12345/cancel", "method": "POST" },
    "customer": { "href": "/v1/customers/cust_789" },
    "items": { "href": "/v1/orders/ord_12345/items" },
    "invoice": { "href": "/v1/orders/ord_12345/invoice", "type": "application/pdf" }
  }
}
```

> **Pragmatic Guidance**: Full HATEOAS is rarely implemented. At minimum, include `self` links and links to related resources. Skip if building internal APIs where clients are tightly coupled.

---

## 14. SDK Generation

### 14.1 Toolchain

| Generator | Languages | Source |
|-----------|-----------|--------|
| **openapi-generator** | 50+ languages | OpenAPI 3.x |
| **Kiota** (Microsoft) | C#, Go, Java, PHP, Python, TS | OpenAPI 3.x |
| **Stainless** | TypeScript, Python, Go, Java | OpenAPI 3.x |
| **buf.build** | Go, TypeScript, Python, Java | Protobuf |
| **graphql-codegen** | TypeScript | GraphQL Schema |

### 14.2 SDK Design Principles

```typescript
// Good SDK design — idiomatic, typed, ergonomic
const client = new OrdersAPI({
  apiKey: process.env.ORDERS_API_KEY,
  baseUrl: 'https://api.example.com/v1',
  timeout: 30_000,
  retries: 3,
});

// Auto-paginating iterator
for await (const order of client.orders.list({ status: 'shipped' })) {
  console.log(order.id, order.total);
}

// Type-safe mutations
const newOrder = await client.orders.create(
  { items: [{ productId: 'prod_123', quantity: 2 }] },
  { idempotencyKey: crypto.randomUUID() }
);
```

---

## 15. Security Considerations

### 15.1 Security Checklist

- [ ] **HTTPS only** — Reject HTTP connections; use HSTS headers
- [ ] **Input validation** — Validate all inputs against strict schemas; reject unknown fields
- [ ] **Output encoding** — Escape all output to prevent XSS in API responses
- [ ] **Rate limiting** — Apply per-IP, per-user, and per-endpoint limits
- [ ] **Authentication on every endpoint** — No accidental public endpoints
- [ ] **Authorization checks** — Verify resource ownership, not just authentication
- [ ] **No sensitive data in URLs** — Tokens, passwords, PII in headers or body only
- [ ] **CORS configuration** — Whitelist specific origins, never `*` in production
- [ ] **Request size limits** — Cap body size (e.g., 1MB default)
- [ ] **SQL injection prevention** — Parameterized queries only; never string concatenation
- [ ] **Mass assignment protection** — Explicit allowlists for writable fields
- [ ] **Timing-safe comparisons** — Use `hmac.compare_digest` for secret comparison
- [ ] **Audit logging** — Log all mutations with actor, timestamp, and resource
- [ ] **No stack traces in responses** — Generic error messages for 5xx errors

### 15.2 CORS Configuration

```typescript
// Secure CORS setup
app.use(cors({
  origin: [
    'https://app.example.com',
    'https://admin.example.com',
  ],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Idempotency-Key', 'X-Request-ID'],
  exposedHeaders: ['RateLimit-Limit', 'RateLimit-Remaining', 'RateLimit-Reset'],
  credentials: true,
  maxAge: 86400, // Preflight cache: 24 hours
}));
```

---

## 16. Performance & Scaling

### 16.1 Response Compression

```typescript
import compression from 'compression';

app.use(compression({
  filter: (req, res) => {
    // Compress JSON and text responses
    return /json|text|javascript|css|xml/.test(res.getHeader('content-type') as string);
  },
  threshold: 1024, // Only compress responses > 1KB
  level: 6,        // Balanced speed vs ratio
}));
```

### 16.2 Conditional Requests (ETags)

```typescript
app.get('/v1/products/:id', async (req, res) => {
  const product = await db.products.findById(req.params.id);
  const etag = generateETag(product); // Hash of content

  res.setHeader('ETag', etag);
  res.setHeader('Cache-Control', 'private, max-age=0, must-revalidate');

  if (req.headers['if-none-match'] === etag) {
    return res.status(304).end(); // Not Modified — save bandwidth
  }

  res.json({ data: product });
});
```

### 16.3 Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| p50 latency | < 100ms | < 200ms |
| p95 latency | < 300ms | < 1s |
| p99 latency | < 1s | < 3s |
| Error rate (5xx) | < 0.1% | < 1% |
| Availability | 99.9% | 99.5% |
| Time to first byte | < 200ms | < 500ms |

---

## 17. Common Mistakes & Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Verb-based URLs** (`/getUser`) | Not RESTful, inconsistent | Use nouns + HTTP methods |
| **Nested resources 3+ deep** | Unreadable, coupled | Flatten: `/items/{id}` with filter `?orderId=x` |
| **Returning 200 for errors** | Clients can't distinguish success/failure | Use proper status codes |
| **Leaking internal IDs** | Sequential IDs expose count + enumeration | Use UUIDs or opaque tokens |
| **No pagination** | Memory explosion, timeout on large datasets | Always paginate collections |
| **Breaking changes without versioning** | Client crashes | Version URL, deprecation headers |
| **Chatty APIs** | N+1 round trips for related data | Use `?include=` or compound documents |
| **Ignoring idempotency** | Duplicate charges, duplicate creates | Require `Idempotency-Key` for mutations |
| **Exposing database schema** | Coupling, security risk | Design response schema independently |
| **Missing request validation** | Injection attacks, corrupt data | Validate with JSON Schema / Zod |
| **No rate limiting** | DDoS vulnerability, abuse | Apply tiered rate limits |
| **Inconsistent naming** | `camelCase` mixed with `snake_case` | Pick one convention, enforce with linter |

---

## 18. API Design Review Checklist

### Pre-Release

- [ ] All endpoints documented in OpenAPI 3.1 spec
- [ ] Error responses follow RFC 9457 format
- [ ] Pagination implemented for all collection endpoints
- [ ] Rate limiting configured and tested
- [ ] Authentication required on all non-public endpoints
- [ ] Authorization checks for resource ownership
- [ ] Idempotency keys supported for mutating endpoints
- [ ] Input validation with clear error messages
- [ ] No sensitive data in URL paths or query strings
- [ ] CORS properly configured
- [ ] Response envelope is consistent across endpoints
- [ ] Versioning strategy documented and implemented
- [ ] Deprecation policy documented

### Post-Release

- [ ] SDK generated and published for target languages
- [ ] API documentation published with examples
- [ ] Monitoring dashboards for latency, error rates, usage
- [ ] Alerting configured for error rate spikes
- [ ] Load testing completed for expected traffic
- [ ] Backward compatibility tests in CI pipeline
- [ ] Changelog maintained for API changes

---

## 19. API Gateway Patterns

```
                     ┌──────────────────────────┐
    Clients ────────►│      API Gateway          │
                     │  (Kong / AWS API GW /     │
                     │   Traefik / Envoy)        │
                     │                           │
                     │  ┌─ Rate Limiting         │
                     │  ├─ Authentication        │
                     │  ├─ Request Validation    │
                     │  ├─ Response Caching      │
                     │  ├─ Request Logging       │
                     │  ├─ Circuit Breaking      │
                     │  ├─ Request Transformation│
                     │  └─ Load Balancing        │
                     │                           │
                     └──────┬─────┬─────┬────────┘
                            │     │     │
                         ┌──▼─┐┌──▼─┐┌──▼─┐
                         │Svc ││Svc ││Svc │
                         │ A  ││ B  ││ C  │
                         └────┘└────┘└────┘
```

### Gateway vs Service-Level Concerns

| Concern | Gateway | Service |
|---------|---------|---------|
| Rate limiting | ✅ Global limits | Per-endpoint fine-tuning |
| Authentication | ✅ Token validation | ✅ Authorization logic |
| TLS termination | ✅ Always | mTLS between services |
| Request logging | ✅ Access logs | Business event logs |
| Input validation | Schema validation | Business rule validation |
| Caching | ✅ Response caching | Application-level caching |
| Circuit breaking | ✅ Downstream protection | Retry logic |

---

## 20. References & Further Reading

| Resource | URL |
|----------|-----|
| RFC 9457 — Problem Details | https://www.rfc-editor.org/rfc/rfc9457 |
| RFC 8594 — Sunset Header | https://www.rfc-editor.org/rfc/rfc8594 |
| Microsoft REST API Guidelines | https://github.com/microsoft/api-guidelines |
| Google API Design Guide | https://cloud.google.com/apis/design |
| Stripe API Reference (gold standard) | https://docs.stripe.com/api |
| OpenAPI 3.1 Specification | https://spec.openapis.org/oas/v3.1.0 |
| JSON:API Specification | https://jsonapi.org/ |
| gRPC Best Practices | https://grpc.io/docs/guides/ |
| GraphQL Best Practices | https://graphql.org/learn/best-practices/ |
| OWASP API Security Top 10 | https://owasp.org/API-Security/ |
