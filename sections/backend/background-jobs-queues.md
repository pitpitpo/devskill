# ⚡ Production Background Jobs, Queues & Distributed Workflows

> **Standard Identifier**: `SEC-BACKEND-QUEUES-001`  
> **Status**: Active / Production Standard  
> **Target Audience**: Backend Engineers, Platform Architects, Distributed Systems SREs  
> **Classification**: Level 4 Core Systems Knowledge Base  

---

## 1. Executive Summary & Core Philosophy

> **Golden Rule**: *User-facing HTTP request/response loops must be strictly computational and ephemeral (< 200ms). Any task involving external I/O, heavy computation, file transformations, bulk notifications, or eventual consistency must be dispatched asynchronously to a durable message broker with guaranteed idempotency.*

Decoupling synchronous API gateways from asynchronous worker processes is essential for system resilience, throughput smoothing, and fault tolerance. However, background processing introduces distributed complexities: message duplication, consumer crashes, queue starvation, poisonous messages, and unordered executions.

This standard establishes production-ready asynchronous job patterns, broker selection matrices, dead-letter queue architectures, and concrete implementations for Node.js (BullMQ) and Python (Celery/ARQ).

---

## 2. Message Broker Architecture & Selection Matrix

```
                      ┌───────────────────────────────────────────────┐
                      │              PRODUCER (API GATEWAY)           │
                      └───────────────────────┬───────────────────────┘
                                              │ 1. Push Job (with Idempotency Key)
                                              ▼
                      ┌───────────────────────────────────────────────┐
                      │         MESSAGE BROKER / TASK QUEUE           │
                      │  [Delayed] -> [Active] -> [Retry / Backoff]   │
                      └───────┬───────────────────────────────┬───────┘
                              │ 2. Pull / Stream              │
                              ▼                               │ (Failed > Max Retries)
                      ┌───────────────┐                       ▼
                      │ WORKER POOL   │               ┌───────────────┐
                      │ Process Job   │               │  DEAD LETTER  │
                      │ ACK on Finish │               │  QUEUE (DLQ)  │
                      └───────────────┘               └───────────────┘
```

### Broker Comparison Matrix

| Broker System | Paradigm | Throughput (msg/sec) | Latency | Persistence | Ordering | Best Suited For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Redis (BullMQ / ARQ)** | In-memory with RDB/AOF | 10,000 - 50,000 | Sub-millisecond | Memory backed by disk | Strict FIFO within queue | Application-level job queues, delayed jobs, scheduled crons |
| **RabbitMQ (AMQP)** | Traditional message broker | 20,000 - 100,000 | 1 - 5 ms | Durable queues & exchanges | FIFO per channel | Complex routing (fanout, topic), reliable transactional messaging |
| **Apache Kafka** | Distributed commit log | 1,000,000+ | 5 - 20 ms | High-throughput partitioned disk log | Strict ordering per partition | Event streaming, audit trails, real-time analytics pipelines |
| **AWS SQS** | Fully managed cloud queue | Virtually infinite (Standard) | 10 - 50 ms | Distributed multi-AZ | Standard (At-least-once) or FIFO | Cloud-native serverless, zero-maintenance operational model |

---

## 3. Distributed Queue Reliability Patterns

### 3.1 Idempotency Enforcement (Deduplication)
Because distributed message brokers provide *at-least-once* delivery semantics, consumers will inevitably receive duplicate messages during network partitions or worker heartbleed timeouts.

**The Idempotency Key Pattern**:
1. Every job dispatched contains a deterministic `idempotency_key` (e.g., `hash(tenant_id, action, entity_id, timestamp_window)`).
2. Before processing, the worker checks an atomic distributed lock in Redis:
   ```
   SET lock:job:{idempotency_key} {worker_id} NX EX 600
   ```
3. If the lock is not acquired, the job is already being processed or completed; the worker emits an immediate ACK.
4. On successful completion, record the state in a durable PostgreSQL `processed_jobs` table before releasing the transient Redis lock.

### 3.2 Dead Letter Queues (DLQ) & Exponential Backoff
When a job fails due to transient external downstream outages (e.g., Stripe API 503), retrying immediately exacerbates the outage.

**Production Retry Schedule**:
$$	ext{Delay}(n) = \min(	ext{MaxDelay}, 	ext{InitialDelay} 	imes 	ext{Multiplier}^n) \pm 	ext{Jitter}$$

If failures exceed `max_retries` (typically 5 attempts), the message must not be discarded. It is routed automatically to a **Dead Letter Queue (DLQ)** with full contextual error metadata, stack traces, and input payload for human inspection and automated alerting.

---

## 4. Concrete Production Implementation: BullMQ + TypeScript

```typescript
import { Queue, Worker, Job, QueueEvents } from "bullmq";
import { Redis } from "ioredis";

const connection = new Redis(process.env.REDIS_URL || "redis://localhost:6379", {
  maxRetriesPerRequest: null,
  enableReadyCheck: false,
});

export interface EmailJobData {
  userId: string;
  templateId: string;
  variables: Record<string, any>;
  idempotencyKey: string;
}

// 1. Queue Definition
export const emailQueue = new Queue<EmailJobData>("email-delivery", {
  connection,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: "exponential",
      delay: 2000, // 2s, 4s, 8s, 16s, 32s
    },
    removeOnComplete: { count: 1000 }, // Keep last 1000 completed
    removeOnFail: { count: 5000 },     // Retain failed jobs for DLQ inspection
  },
});

// 2. Worker Definition with Concurrency & Idempotency
export const emailWorker = new Worker<EmailJobData>(
  "email-delivery",
  async (job: Job<EmailJobData>) => {
    const { userId, templateId, variables, idempotencyKey } = job.data;
    const lockKey = `lock:job:${idempotencyKey}`;

    // Acquire idempotency lock
    const acquired = await connection.set(lockKey, job.id!, "PX", 60000, "NX");
    if (!acquired) {
      console.warn(`[Worker] Duplicate job detected: ${idempotencyKey}, skipping.`);
      return { status: "skipped_duplicate" };
    }

    try {
      console.log(`[Worker] Processing email for ${userId} (Attempt ${job.attemptsMade + 1})`);
      
      // Simulate downstream API call with potential failure
      await sendEmailViaProvider(userId, templateId, variables);

      return { status: "sent", timestamp: Date.now() };
    } catch (error: any) {
      console.error(`[Worker] Execution error for job ${job.id}:`, error.message);
      throw error; // Re-throw to trigger BullMQ exponential backoff
    }
  },
  {
    connection,
    concurrency: 20, // Process 20 jobs concurrently per worker instance
    limiter: {
      max: 100,      // Rate limit: max 100 jobs
      duration: 1000 // per 1000ms (prevents downstream API rate limits)
    }
  }
);

async function sendEmailViaProvider(userId: string, template: string, vars: any) {
  // Production integration with SendGrid / Resend
  return true;
}

// 3. Queue Lifecycle Events & DLQ Alerting
const queueEvents = new QueueEvents("email-delivery", { connection });

queueEvents.on("failed", ({ jobId, failedReason }) => {
  console.error(`[ALERT] Job ${jobId} permanently failed: ${failedReason}`);
  // Dispatch PagerDuty / Sentry Alert if attempts exhausted
});
```

---

## 5. Security & Operational Hardening

### 5.1 Worker Graceful Shutdown Protocol
When deploying new container images via Kubernetes, workers must not be terminated abruptly mid-job.

```typescript
async function gracefulShutdown(signal: string) {
  console.log(`Received ${signal}. Draining worker connections...`);
  await emailWorker.close(); // Waits for active jobs to complete or reach timeout
  await connection.quit();
  process.exit(0);
}

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
```

### 5.2 Queue Lag Monitoring & Autoscaling (HPA)
Deploy Prometheus metrics exporters (`bull_exporter` or custom telemetry) tracking:
1. `queue_depth_total`: Number of waiting jobs.
2. `job_duration_seconds`: Processing latency percentile (p95, p99).
3. `queue_lag_seconds`: Age of oldest unhandled message in queue.

Configure Kubernetes **KEDA (Kubernetes Event-driven Autoscaling)** to scale worker pods from 2 to 50 based on active queue lag:
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: email-worker-scaler
spec:
  scaleTargetRef:
    name: email-worker-deployment
  minReplicaCount: 2
  maxReplicaCount: 50
  triggers:
  - type: redis
    metadata:
      address: redis:6379
      listName: bull:email-delivery:wait
      listLength: "50" # Scale 1 pod per 50 queued jobs
```

---

## 6. Common Pitfalls & Anti-Patterns

| Anti-Pattern | Root Cause | Production Consequence | Remediated Standard |
| :--- | :--- | :--- | :--- |
| **Giant Job Payloads** | Passing 20MB file buffer or complete database objects in job arguments | Redis memory exhaustion, network serialization lag | Pass only entity IDs (`userId`, `documentId`); worker fetches data from DB |
| **Missing Idempotency** | Assuming jobs execute exactly once | Duplicate payments charged, duplicate transactional emails sent | Mandatory `idempotency_key` and atomic execution checks |
| **Unbounded Retries** | Infinite retry loop without backoff | Downstream third-party DDoS, cascading API lockouts | Fixed max attempts (3-5) with exponential backoff and DLQ routing |
| **Synchronous Database Commits Inside Loops** | Iterating over 10,000 records inserting one-by-one inside a single job | Worker timeout, blocking worker thread | Batch operations (`INSERT INTO ... VALUES (...)`) or chunk jobs into micro-batches |
| **Hardcoded Concurrency** | Defaulting to 1 worker thread on multi-core VMs | Massive queue lag despite idle server resources | Size worker concurrency to I/O constraints ($10	imes$ to $50	imes$ CPU count for network I/O) |

---

## 7. Verification Checklist & Production Audit

- [ ] All asynchronous jobs accept an explicit `idempotencyKey` and check for duplicate execution.
- [ ] Retry policies use exponential backoff with randomized jitter; max retries capped at 5.
- [ ] Dead Letter Queues (DLQ) are configured with alerts when dead-lettered job counts exceed zero.
- [ ] Worker processes trap `SIGTERM` and `SIGINT` signals to finish inflight tasks before shutdown.
- [ ] Queue depth, active processing latency, and failure rates are exposed via OpenTelemetry/Prometheus metrics.
- [ ] Autoscaling (KEDA or HPA) is configured based on queue depth rather than raw CPU/memory.
- [ ] Job payloads contain only scalar identifiers and lightweight primitives, never large binary blobs.
