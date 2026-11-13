# 📈 Observability & Telemetry Standards (`observability-telemetry.md`)

> **Classification**: Production Telemetry & Site Reliability Engineering  
> **Standards**: OpenTelemetry (OTel), Prometheus, W3C TraceContext

---

## 1. The Three Pillars of Modern Observability

```
                       ┌─────────────────────────┐
                       │   CORRELATION CONTEXT   │
                       │ Trace ID + Span ID + Env│
                       └────────────┬────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
     ┌───────────┐            ┌───────────┐            ┌───────────┐
     │   LOGS    │            │  METRICS  │            │  TRACES   │
     │Structured │            │Prometheus │            │OpenTelem. │
     │JSON events│            │Rate,Error,│            │End-to-End │
     │with context            │Duration   │            │Spans      │
     └───────────┘            └───────────┘            └───────────┘
```

---

## 2. Distributed Tracing & W3C TraceContext

When Service A calls Service B over HTTP or gRPC, it MUST propagate the `traceparent` header:
```http
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │  └───────────────┬──────────────┘ └───────┬──────┘ └─ Flags
           Version            Trace ID                 Span ID
```

This enables end-to-end flame graphs across distributed systems in Jaeger, Honeycomb, or Datadog.

---

## 3. The RED Method for API Metrics

Monitor all web services and microservices using the **RED** method:
1. **Rate**: Requests received per second (`http_requests_total`).
2. **Errors**: Failed requests per second (`http_requests_errors_total` with status >= 500).
3. **Duration**: Time taken per request in milliseconds (`http_request_duration_seconds_bucket` histogram - p50, p95, p99).

---

## 4. Structured JSON Logging Schema

```json
{
  "@timestamp": "2026-11-13T21:40:00.123Z",
  "level": "ERROR",
  "service": "billing-service",
  "environment": "production",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Payment processing failed due to upstream gateway timeout",
  "error": {
    "type": "GatewayTimeoutError",
    "message": "Stripe API did not respond within 3000ms"
  },
  "context": {
    "customer_id": "cus_99812",
    "order_id": "ord_5521",
    "retry_attempt": 2
  }
}
```
