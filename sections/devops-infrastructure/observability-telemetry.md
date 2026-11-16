# 📊 Distributed Observability, OpenTelemetry & SRE Alerting (`observability-telemetry.md`)

> **Standard Identifier**: `SEC-DEVOPS-OTEL-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: SREs, Platform Architects, Backend Engineers, DevOps Leads  
> **Classification**: Level 4 Infrastructure & Telemetry Engineering Guide  
> **Tech Stack**: OpenTelemetry 1.25+, Prometheus 2.50+, Grafana 11+, Jaeger/Tempo, Loki  
> **Prerequisites**: Distributed Systems, W3C Trace Context, Google SRE Error Budget Theory  

---

## 1. Title, Metadata & Scope

In modern distributed microservice and serverless architectures, monolithic logs and uncoordinated metrics are insufficient to diagnose latency degradations, cascading failures, or silent data corruptions. When a user checkout transaction traverses an API Gateway, an Authentication Service, an Inventory Pod, and an asynchronous Payment Queue, diagnosing a 504 Gateway Timeout without distributed correlation requires guessing.

This standard establishes the non-negotiable operational architecture for distributed observability. It defines:
1. **The OpenTelemetry (OTel) Standard**: In-process SDK instrumentation for Traces, Metrics, and Logs.
2. **Context Propagation**: Ubiquitous propagation of W3C `traceparent` headers across HTTP and message brokers.
3. **The Four Golden Signals**: Google SRE measurement standards (Latency, Traffic, Errors, Saturation).
4. **Multi-Window Multi-Burn-Rate Alerting**: Mathematical SLO/SLI alerting preventing alert fatigue while catching outages.
5. **PII Redaction & Cardinality Defense**: Strict limits on metric label cardinality and automated scrubbing of sensitive data.

---

## 2. Core Philosophy & Golden Rules

> **"Infer System Health from External Outputs; Correlate Every Log and Metric to a Distributed Trace ID; Alert on User-Impacting Symptoms Rather than Ephemeral Component Spikes."**

### The Five Invariants of Distributed Observability

1. **Unified Correlation (The Trace ID Invariant)**: Every log line, trace span, and error event emitted during request execution MUST include the identical W3C `trace_id` and `span_id`. Uncorrelated logs are treated as operational defects.
2. **Zero Unbounded Cardinality**: Never use unique identifiers (`user_id`, `email`, `order_id`, `uuid`, or raw URL paths containing IDs) as Prometheus metric label keys. High cardinality causes time-series database memory exhaustion and crashes Prometheus.
3. **Mandatory W3C Context Propagation**: Every outbound HTTP request (`fetch`, `axios`, `http.Client`) and message queue publish (Kafka, RabbitMQ, SQS) MUST inject the W3C `traceparent` header.
4. **Symptom-Based Multi-Burn Alerting**: Alerts paging human engineers MUST be based on Service Level Objective (SLO) error budget burn rates. Never alert directly on transient CPU spikes or individual 500 errors.
5. **Zero PII in Telemetry**: Application logs and trace span attributes MUST pass through an automated redaction filter that strips authorization tokens, passwords, credit card numbers, and government IDs prior to network export.

---

## 3. Architecture & Distributed Telemetry Foundations

### 3.1 The OpenTelemetry Architecture Pipeline

```
     User Request (Inbound HTTP)
              │
              ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ IN-PROCESS APPLICATION RUNTIME (Node.js / Go / Python / Java)          │
   │                                                                        │
   │  ┌──────────────────────────────────────────────────────────────────┐  │
   │  │ OpenTelemetry SDK                                                │  │
   │  │ ├── TracerProvider   ──► Captures Spans & DB queries             │  │
   │  │ ├── MeterProvider    ──► Captures RED & Saturation metrics        │  │
   │  │ └── LoggerProvider   ──► Injects trace_id into JSON log records  │  │
   │  └─────────────────────────────────┬────────────────────────────────┘  │
   └────────────────────────────────────┼───────────────────────────────────┘
                                        │ OTLP Protocol (gRPC / Port 4317)
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ OPENTELEMETRY COLLECTOR (Agent / Gateway Pod)                          │
   │                                                                        │
   │  Receivers ──► Processors (Memory Limiter, Batch, PII Scrub) ──► Exporters
   └───────┬────────────────────────────┬────────────────────────────┬──────┘
           │                            │                            │
           ▼                            ▼                            ▼
    ┌──────────────┐             ┌──────────────┐             ┌──────────────┐
    │ GRAFANA TEMPO│             │  PROMETHEUS  │             │ GRAFANA LOKI │
    │   (Traces)   │             │  (Metrics)   │             │    (Logs)    │
    └──────────────┘             └──────────────┘             └──────────────┘
```

---

### 3.2 Google SRE 4 Golden Signals vs RED vs USE

| Telemetry Framework | Target Resource | Dimensions Measured | Standard Metric Names |
|---|---|---|---|
| **Google SRE 4 Golden Signals** | User-Facing Services & Platforms | 1. **Latency** (Time to serve)<br>2. **Traffic** (Demand rate)<br>3. **Errors** (Rate of failed requests)<br>4. **Saturation** (Resource fraction used) | `http_request_duration_seconds`<br>`http_requests_total`<br>`http_requests_failed_total`<br>`process_cpu_seconds_total` |
| **RED Method** | Request-Driven Microservices | 1. **Rate** (req/sec)<br>2. **Errors** (failed req/sec)<br>3. **Duration** (latency histogram) | Best practice for REST/gRPC endpoints |
| **USE Method** | Infrastructure & Hardware Components | 1. **Utilization** (avg time resource was busy)<br>2. **Saturation** (queue backlog/degree of overload)<br>3. **Errors** (device error count) | Best practice for CPUs, Disks, Memory, and Network interfaces |

---

### 3.3 Google SRE Multi-Window Multi-Burn-Rate Alerting Mathematics

Alerting on a single error rate window leads to a severe trade-off between **detection speed** and **reset latency**. Google SRE Chapter 5 specifies **Multi-Window Multi-Burn-Rate Alerts** against a 30-day error budget (e.g. 99.9% availability SLO $\rightarrow$ 0.1% budget):

```
                               SLO ERROR BUDGET BURN RATES
                               
  ┌──────────────┬────────────┬─────────────┬─────────────────┬───────────────────┐
  │ Severity     │ Budget Burn│ Time to 100%│ Long Window     │ Short Window      │
  │              │ Rate       │ Exhaustion  │ (Metric Trigger)│ (Reset Guard)     │
  ├──────────────┼────────────┼─────────────┼─────────────────┼───────────────────┤
  │ **P1 (Page)**│ **14.4x**  │ **2 Days**  │ **1 Hour**      │ **5 Minutes**     │
  │ **P2 (Page)**│ **6.0x**   │ **5 Days**  │ **6 Hours**     │ **30 Minutes**    │
  │ **P3 (Ticket)**│ **1.0x** │ **30 Days** │ **3 Days (72h)**│ **6 Hours**       │
  └──────────────┴────────────┴─────────────┴─────────────────┴───────────────────┘
```

#### Alert Rule Formula (PromQL for P1 14.4x Burn):
```promql
# Alert triggers ONLY if BOTH the 1h window AND the 5m window exceed 14.4x burn rate
(
  sum(rate(http_requests_total{status=~"5.*"}[1h]))
  /
  sum(rate(http_requests_total[1h]))
) > (14.4 * (1 - 0.999))
and
(
  sum(rate(http_requests_total{status=~"5.*"}[5m]))
  /
  sum(rate(http_requests_total[5m]))
) > (14.4 * (1 - 0.999))
```

---

## 4. Concrete Production Implementations

### 4.1 Production OpenTelemetry SDK Initialization (TypeScript / Node.js)

```typescript
// telemetry/otel-init.ts
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-grpc";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";
import { Resource } from "@opentelemetry/resources";
import { SemanticResourceAttributes } from "@opentelemetry/semantic-conventions";

const collectorEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://otel-collector:4317";

export const otelSdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: process.env.SERVICE_NAME ?? "orders-service",
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.SERVICE_VERSION ?? "1.0.0",
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV ?? "production",
  }),
  traceExporter: new OTLPTraceExporter({
    url: collectorEndpoint,
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: collectorEndpoint,
    }),
    exportIntervalMillis: 15000, // Export every 15 seconds
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      // Disable noisy file system spans
      "@opentelemetry/instrumentation-fs": { enabled: false },
      "@opentelemetry/instrumentation-http": {
        ignoreIncomingRequestHook: (req) => {
          // Skip health probes from spamming traces
          return req.url === "/healthz" || req.url === "/readyz";
        },
      },
    }),
  ],
});

// Start SDK before importing any application modules
otelSdk.start();

// Handle graceful process shutdown
const shutdown = async () => {
  try {
    await otelSdk.shutdown();
    process.exit(0);
  } catch (err) {
    console.error("Error shutting down OpenTelemetry SDK:", err);
    process.exit(1);
  }
};

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
```

---

### 4.2 Structured JSON Logger with Trace Correlation & PII Redaction

```typescript
// telemetry/logger.ts
import { trace, context } from "@opentelemetry/api";

type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

interface LogPayload {
  timestamp: string;
  level: LogLevel;
  service: string;
  message: string;
  trace_id?: string;
  span_id?: string;
  context?: Record<string, unknown>;
}

// Rules to scrub sensitive data before outputting to stdout
const PII_RULES = [
  { pattern: /("?(?:password|token|secret|apiKey|authorization)"?\s*[:=]\s*)"[^"]+"/gi, replacement: '$1"[REDACTED]"' },
  { pattern: /("?(?:cardNumber|creditCard)"?\s*[:=]\s*)"\d{13,19}"/gi, replacement: '$1"[REDACTED]"' },
  { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b/g, replacement: '"[REDACTED_EMAIL]"' },
];

function sanitizeLogMessage(input: string): string {
  let sanitized = input;
  for (const rule of PII_RULES) {
    sanitized = sanitized.replace(rule.pattern, rule.replacement);
  }
  return sanitized;
}

export function log(level: LogLevel, message: string, meta?: Record<string, unknown>): void {
  // Extract active distributed tracing context
  const activeSpan = trace.getSpan(context.active());
  const spanContext = activeSpan?.spanContext();

  const payload: LogPayload = {
    timestamp: new Date().toISOString(),
    level,
    service: process.env.SERVICE_NAME ?? "orders-service",
    message,
    trace_id: spanContext?.traceId,
    span_id: spanContext?.spanId,
    context: meta,
  };

  const serialized = JSON.stringify(payload);
  const cleanLog = sanitizeLogMessage(serialized);

  if (level === "ERROR") {
    process.stderr.write(`${cleanLog}\n`);
  } else {
    process.stdout.write(`${cleanLog}\n`);
  }
}

export const logger = {
  debug: (msg: string, meta?: Record<string, unknown>) => log("DEBUG", msg, meta),
  info: (msg: string, meta?: Record<string, unknown>) => log("INFO", msg, meta),
  warn: (msg: string, meta?: Record<string, unknown>) => log("WARN", msg, meta),
  error: (msg: string, meta?: Record<string, unknown>) => log("ERROR", msg, meta),
};
```

---

### 4.3 Production OpenTelemetry Collector Configuration (`otel-collector.yaml`)

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  # Protect collector against OOM crashes under sudden traffic spikes
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 20

  # Batch telemetries to reduce network overhead
  batch:
    send_batch_size: 1024
    timeout: 5s

  # Redact authorization and PII attributes from trace spans
  attributes:
    actions:
      - key: http.request.header.authorization
        action: delete
      - key: db.statement
        pattern: "(?i)(password|secret|credit_card)"
        action: hash

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: app

  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, attributes, batch]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

---

## 5. Security & Performance Considerations

| Dimension | Risk / Vector | Production Defense |
|---|---|---|
| **High-Cardinality Explosion** | Adding `user_id` or `uuid` to metric labels | Crashes Prometheus timeseries index; restrict labels strictly to bounded enums |
| **Telemetry Network Overhead** | 100% trace sampling saturating network links | Use head-based probabilistic sampling (5-10% of 2xx, 100% of 5xx errors) |
| **Sensitive Data Exposure** | Leaking customer PII or auth headers in traces | Filter attributes via OTel Collector `attributes` processor before remote export |
| **Unbounded In-Memory Buffers** | Application crash during collector network partition | Configure bounded memory limits on in-process batch exporters (`maxQueueSize: 2048`) |

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Manifestation | Production Consequence | Remediated Standard |
|---|---|---|---|
| **Raw Unstructured Logs** | Emitting `console.log("user error: " + err)` | Logs cannot be filtered, parsed, or correlated with trace spans | Emit strictly structured JSON with `trace_id` and ISO 8601 timestamps |
| **Swallowed Context in Goroutines** | Spawning background tasks with `context.Background()` | Loses parent trace context; traces appear split and orphaned | Pass existing `ctx` into background workers or explicitly propagate span context |
| **Alerting on Raw CPU Usage** | Paging on-call when CPU exceeds 90% for 30s | High alert fatigue; CPU spikes often reflect healthy batch processing | Alert on user-facing latency and SLO error budget burn rates |
| **100% Trace Sampling at Scale** | Tracing every request at 50,000 req/sec | Enormous cloud storage bills and collector CPU exhaustion | Implement tail-based sampling or probabilistic head-based sampling |
| **Missing Health Probe Filter** | Generating 10 million spans per day for `/healthz` | Clutters Jaeger/Tempo with useless liveness checks | Exclude `/healthz` and `/readyz` in HTTP instrumentation config |

---

## 7. Verification Checklist & Production Audit

Before publishing services or alerting pipelines to production:

- [ ] **OpenTelemetry SDK Loaded First**: OTel SDK is imported and initialized before any database or HTTP libraries.
- [ ] **W3C Header Propagation**: Outbound HTTP requests and messaging payloads inject standard `traceparent` headers.
- [ ] **Structured Logs with Trace ID**: All logs emit machine-readable JSON containing `trace_id` and `span_id`.
- [ ] **Cardinality Checked**: Metric labels are bounded enums; zero `user_id`, `email`, or dynamic UUIDs in label keys.
- [ ] **Multi-Window Multi-Burn Alerts**: Alert rules implement Google SRE Chapter 5 multi-window burn rate formulas.
- [ ] **PII Scrubbing Active**: Automated sanitizer verifies zero plaintext secrets, tokens, or emails in emitted logs.
- [ ] **Probes Filtered**: `/healthz` and `/readyz` endpoints are excluded from distributed trace capture.
