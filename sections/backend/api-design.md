# 🌐 Production API Design Standards (`api-design.md`)

> **Classification**: Global API Contract & Communication Standard  
> **Applicability**: Public and Private RESTful Services

---

## 1. Unified HTTP Status Code Matrix

| Code | Meaning | When to Use |
|---|---|---|
| **200 OK** | Success with payload | Successful `GET`, `PUT`, or `PATCH` returning resource |
| **201 Created** | Resource created | Successful `POST` returning newly created resource + `Location` header |
| **204 No Content**| Action completed without payload | Successful `DELETE` or empty mutation |
| **400 Bad Request**| Malformed syntax | Malformed JSON or unparseable headers |
| **401 Unauthorized**| Authentication missing/invalid | Missing Bearer token, expired session |
| **403 Forbidden** | Authenticated but unauthorized | User does not have RBAC permission to access resource |
| **404 Not Found** | Resource does not exist | Invalid ID or hidden ID for security isolation |
| **409 Conflict** | State collision | Unique constraint violation (e.g. duplicate email) |
| **422 Unprocessable**| Schema validation error | Valid JSON syntax but failed business/type validation |
| **429 Too Many Req**| Rate limit exceeded | Throttled by IP or account quota |
| **500 Server Error**| Unhandled crash | System exception (Never expose stack trace) |

---

## 2. Standardized Error Envelope (RFC 9457)

All error responses MUST conform to the RFC 9457 Problem Details standard:

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
    }
  ]
}
```

---

## 3. Keyset / Cursor Pagination (Over Offset/Limit)

Offset-based pagination (`OFFSET 10000 LIMIT 20`) degrades significantly on large datasets ($O(N)$ scan). Keyset pagination uses indexed columns for constant $O(1)$ time:

```http
GET /v1/transactions?limit=20&cursor=eyJpZCI6MTAyOSwiY3JlYXRlZF9hdCI6MTY5ODc2NX0=
```

### Response Envelope:
```json
{
  "data": [ ... ],
  "pagination": {
    "limit": 20,
    "hasMore": true,
    "nextCursor": "eyJpZCI6MTA0OSwiY3JlYXRlZF9hdCI6MTY5ODgyMH0="
  }
}
```

---

## 4. Idempotency Key Architecture

Mutating requests (`POST /v1/payments`) must accept an `Idempotency-Key` header:

```
Client ────── POST /v1/payments [Idempotency-Key: abc-123] ──────► API Gateway
                                                                       │
                                                         Check Redis for key
                                                                       ├── If exists: Return cached response immediately
                                                                       └── If new:
                                                                            1. Set status="IN_PROGRESS" in Redis (TTL: 120s)
                                                                            2. Execute payment transaction in DB
                                                                            3. Cache final response in Redis (TTL: 24h)
                                                                            4. Return response to Client
```
