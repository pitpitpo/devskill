# 📊 Distributed Observability: OpenTelemetry, Prometheus & Distributed Tracing

> **Standard Identifier**: `SEC-DEVOPS-OTEL-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: SREs, Platform Architects, Backend Engineers  
> **Classification**: Level 4 Infrastructure Engineering Guide  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *Observability is the ability to infer the internal state of a distributed system from its external outputs. Standardize on the Three Pillars (Metrics, Logs, Traces) unified via the vendor-neutral OpenTelemetry (OTel) specification. Always propagate W3C Trace Context across process and network boundaries.*

Scattered stdout logs without correlation IDs are useless in microservice architectures. When a user request spans 5 distinct services, engineers require end-to-end distributed trace spans with span context, structured JSON logs containing `trace_id`, and actionable Prometheus metrics.

---

## 2. OpenTelemetry Architecture & The Three Pillars

```
       HTTP Request (Contains W3C Header: traceparent: 00-4bf92f35...-00)
            │
            ▼
   ┌─────────────────────────────────────────────────────────┐
   │             OPENTELEMETRY SDK (IN-PROCESS)              │
   ├────────────────────────────┬────────────────────────────┤
   │ 1. Traces (Spans)          │ TracerProvider             │
   │ 2. Metrics (Counters/Gauges│ MeterProvider              │
   │ 3. Structured Logs         │ LoggerProvider             │
   └────────────────────────────┴────────────────────────────┘
                                │ OTLP Protocol (gRPC / HTTP)
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │                 OPENTELEMETRY COLLECTOR                 │
   │           Receives -> Batches -> Exports to:            │
   └────────┬───────────────────┬───────────────────┬────────┘
            │                   │                   │
            ▼                   ▼                   ▼
     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
     │ JAEGER / TEMPO│   │  PROMETHEUS  │    │ LOKI / ES    │
     │ (Traces)     │    │  (Metrics)   │    │ (Logs)       │
     └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. Distributed Context Propagation (W3C Standard)

Every HTTP request and message queue payload passing between services must carry the standard **W3C Trace Context** header:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │  └───────────────┬───────────────┘ └───────┬────────┘ └─ Sampled flag
              │                  │                         │
           Version            Trace ID                  Span ID
```

---

## 4. Production OpenTelemetry Implementation: TypeScript

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-grpc";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";
import { Resource } from "@opentelemetry/resources";
import { SemanticResourceAttributes } from "@opentelemetry/semantic-conventions";

export const otelSdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: process.env.SERVICE_NAME || "order-api",
    [SemanticResourceAttributes.SERVICE_VERSION]: "1.0.0",
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || "production",
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || "http://otel-collector:4317",
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || "http://otel-collector:4317",
    }),
    exportIntervalMillis: 15000,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

otelSdk.start();

process.on("SIGTERM", () => {
  otelSdk.shutdown().finally(() => process.exit(0));
});
```

---

## 5. Metrics Standards: RED & USE Methodologies

### 5.1 The RED Method (Request-Oriented / Services)
- **Rate**: Requests processed per second (`sum(rate(http_requests_total[1m]))`).
- **Errors**: Number of failed requests (`sum(rate(http_requests_total{status=~"5.*"}[1m]))`).
- **Duration**: Latency distributions (P50, P95, P99 via Prometheus histograms).

### 5.2 The USE Method (Resource-Oriented / Infrastructure)
- **Utilization**: Time resource is busy (CPU %, Memory %).
- **Saturation**: Degree to which work is queued (run-queue length, thread pool backlog).
- **Errors**: Hardware and kernel fault counts.

---


---

## 5. Security & Performance Considerations

| Dimension | Risk / Vector | Production Defense |
| :--- | :--- | :--- |
| **PII in Spans & Logs** | Leaking passwords, tokens, or credit cards | Sanitization filters in OTel Collector stripping sensitive attributes |
| **Telemetry Overhead** | Excessive CPU/network consumption from tracing | Configure Head-Based and Tail-Based Sampling (sample 5-10% of 2xx, 100% of 5xx) |
| **High Cardinality Metrics** | Injecting user IDs or UUIDs into Prometheus labels | Memory explosion in Prometheus; strictly restrict metric labels to low-cardinality enums |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **High-Cardinality Label Spikes** | Adding `user_id` as Prometheus label | Prometheus OOM crash due to millions of time-series series | Store high-cardinality identifiers in trace spans, not metrics |
| **Unsampled Full Tracing** | 100% trace sampling on 50,000 req/sec | Collector network saturation, massive storage costs | Implement probabilistic or tail-based sampling rules |
| **Unstructured Logging** | Writing freeform string messages | Inability to query logs by fields; broken log aggregation | Enforce machine-readable JSON logs with trace correlation IDs |

## 6. Verification Checklist & Production Audit

- [ ] All services import and initialize OTel SDK before loading application dependencies.
- [ ] W3C `traceparent` headers are injected and extracted across HTTP calls and message queues.
- [ ] Application logs are formatted as structured JSON with injected `trace_id` and `span_id`.
- [ ] RED metrics are configured with standard Grafana alert rules (p99 latency > 500ms, 5xx error rate > 0.5%).
- [ ] Collector buffers traces and metrics locally to prevent application pauses during monitoring outages.
