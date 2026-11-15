# 🔌 Production API Microservice Blueprint

> **Template Type**: Standalone Production API Service  
> **Stack Options**: NestJS (TypeScript) | FastAPI (Python) | Go (Chi/Gin) | Spring Boot (Java)  
> **Database**: PostgreSQL 16 + Redis 7  
> **Deployment**: Docker → Kubernetes (or Serverless)

---

## 1. Architecture Overview

```
                    ┌─────────────────────────────┐
                    │      Load Balancer / API     │
                    │      Gateway (Kong/Envoy)    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       SERVICE INSTANCE       │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │   HTTP/gRPC Server     │  │
                    │  │   (Port 8080)          │  │
                    │  └───────────┬────────────┘  │
                    │              │                │
                    │  ┌───────────▼────────────┐  │
                    │  │   Middleware Pipeline   │  │
                    │  │   Auth → RateLimit →    │  │
                    │  │   Logger → Validator    │  │
                    │  └───────────┬────────────┘  │
                    │              │                │
                    │  ┌───────────▼────────────┐  │
                    │  │   Business Logic Layer  │  │
                    │  │   Services / Use Cases  │  │
                    │  └───────────┬────────────┘  │
                    │              │                │
                    │  ┌───────────▼────────────┐  │
                    │  │   Data Access Layer     │  │
                    │  │   Repository Pattern    │  │
                    │  └───────────┬────────────┘  │
                    │              │                │
                    │  ┌───────┐ ┌▼──────┐ ┌─────┐│
                    │  │ PG 16 │ │ Redis │ │ S3  ││
                    │  └───────┘ └───────┘ └─────┘│
                    └─────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   Observability Sidecar      │
                    │   OTEL Collector → Grafana   │
                    └─────────────────────────────┘
```

---

## 2. Project Structure

```
service/
├── src/
│   ├── main.ts                    # Application bootstrap & graceful shutdown
│   ├── config/
│   │   ├── index.ts               # Typed configuration (env validation)
│   │   ├── database.ts            # PostgreSQL connection config
│   │   └── redis.ts               # Redis connection config
│   │
│   ├── modules/
│   │   └── [domain]/              # One module per bounded context
│   │       ├── domain.controller.ts
│   │       ├── domain.service.ts
│   │       ├── domain.repository.ts
│   │       ├── domain.entity.ts
│   │       ├── dto/
│   │       │   ├── create-domain.dto.ts
│   │       │   └── update-domain.dto.ts
│   │       └── domain.module.ts
│   │
│   ├── common/
│   │   ├── middleware/
│   │   │   ├── request-id.middleware.ts
│   │   │   ├── correlation.middleware.ts
│   │   │   └── tenant.middleware.ts
│   │   ├── guards/
│   │   │   ├── auth.guard.ts
│   │   │   └── roles.guard.ts
│   │   ├── interceptors/
│   │   │   ├── logging.interceptor.ts
│   │   │   ├── timeout.interceptor.ts
│   │   │   └── cache.interceptor.ts
│   │   ├── filters/
│   │   │   └── all-exceptions.filter.ts
│   │   ├── pipes/
│   │   │   └── validation.pipe.ts
│   │   └── decorators/
│   │       ├── current-user.decorator.ts
│   │       └── api-paginated.decorator.ts
│   │
│   ├── health/
│   │   ├── health.controller.ts
│   │   └── health.module.ts
│   │
│   └── infrastructure/
│       ├── database/
│       │   ├── migrations/
│       │   └── seeds/
│       ├── cache/
│       ├── queue/
│       └── telemetry/
│           ├── tracing.ts         # OpenTelemetry SDK setup
│           ├── metrics.ts         # Prometheus metrics
│           └── logger.ts          # Structured JSON logging (Pino)
│
├── test/
│   ├── unit/
│   ├── integration/
│   │   └── setup/
│   │       └── testcontainers.ts  # Real PG + Redis for integration tests
│   └── e2e/
│
├── Dockerfile                     # Multi-stage, non-root, distroless
├── docker-compose.yml             # Local dev environment
├── .env.example
├── tsconfig.json
└── package.json
```

---

## 3. Health Check Endpoints

Every production service MUST expose three health endpoints:

```typescript
@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
    private redis: RedisHealthIndicator,
  ) {}

  // Kubernetes liveness probe — is the process alive?
  // If this fails, K8s restarts the container
  @Get('live')
  @HealthCheck()
  liveness() {
    return this.health.check([
      // Only check if the process is responsive
      () => Promise.resolve({ process: { status: 'up' } }),
    ]);
  }

  // Kubernetes readiness probe — can the service handle traffic?
  // If this fails, K8s removes from load balancer
  @Get('ready')
  @HealthCheck()
  readiness() {
    return this.health.check([
      () => this.db.pingCheck('database', { timeout: 1500 }),
      () => this.redis.pingCheck('redis', { timeout: 1000 }),
    ]);
  }

  // Startup probe — has the service finished initialization?
  // Prevents premature liveness checks during slow startups
  @Get('startup')
  @HealthCheck()
  startup() {
    return this.health.check([
      () => this.db.pingCheck('database', { timeout: 5000 }),
      () => this.redis.pingCheck('redis', { timeout: 3000 }),
    ]);
  }
}
```

---

## 4. Graceful Shutdown

```typescript
// main.ts — Production Bootstrap
async function bootstrap() {
  // 1. Initialize OpenTelemetry BEFORE anything else
  const sdk = initTelemetry();

  const app = await NestFactory.create(AppModule, {
    logger: new PinoLogger(),
  });

  // 2. Global middleware pipeline
  app.use(requestId());
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,        // Strip unknown properties
    forbidNonWhitelisted: true,
    transform: true,
    transformOptions: { enableImplicitConversion: false },
  }));
  app.useGlobalFilters(new AllExceptionsFilter());
  app.useGlobalInterceptors(
    new LoggingInterceptor(),
    new TimeoutInterceptor(30_000), // 30s request timeout
  );

  // 3. Enable graceful shutdown hooks
  app.enableShutdownHooks();

  // 4. Graceful shutdown handler
  const signals: NodeJS.Signals[] = ['SIGTERM', 'SIGINT'];
  for (const signal of signals) {
    process.on(signal, async () => {
      console.log(`Received ${signal}, starting graceful shutdown...`);

      // Stop accepting new connections
      const server = app.getHttpServer();
      server.close();

      // Wait for in-flight requests (max 30s)
      const shutdownTimeout = setTimeout(() => {
        console.error('Graceful shutdown timed out, forcing exit');
        process.exit(1);
      }, 30_000);

      try {
        // Drain queues, close DB connections, flush telemetry
        await app.close();
        await sdk.shutdown();
        clearTimeout(shutdownTimeout);
        console.log('Graceful shutdown completed');
        process.exit(0);
      } catch (err) {
        console.error('Error during shutdown:', err);
        process.exit(1);
      }
    });
  }

  await app.listen(process.env.PORT || 8080, '0.0.0.0');
}
```

---

## 5. Structured Logging

```typescript
// Every log line MUST be structured JSON with correlation context
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  serializers: {
    err: pino.stdSerializers.err,
    req: (req) => ({
      method: req.method,
      url: req.url,
      remoteAddress: req.remoteAddress,
    }),
  },
  // DO NOT log in pretty mode in production
  transport: process.env.NODE_ENV === 'development'
    ? { target: 'pino-pretty' }
    : undefined,
});

// Usage in service:
logger.info(
  {
    requestId: ctx.requestId,
    traceId: ctx.traceId,
    userId: ctx.userId,
    tenantId: ctx.tenantId,
    action: 'order.created',
    orderId: order.id,
    duration_ms: elapsed,
  },
  'Order created successfully'
);

// NEVER log:
// - Passwords, tokens, API keys
// - Full request bodies (may contain PII)
// - Credit card numbers, SSNs, health data
```

---

## 6. Error Handling

```typescript
// Centralized exception filter
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status: number;
    let message: string;
    let code: string;

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const res = exception.getResponse();
      message = typeof res === 'string' ? res : (res as any).message;
      code = `HTTP_${status}`;
    } else if (exception instanceof QueryFailedError) {
      // Database constraint violations
      status = 409;
      message = 'Data conflict';
      code = 'DB_CONSTRAINT_VIOLATION';
      // Log the actual error internally but don't expose to client
      logger.error({ err: exception, requestId: request['requestId'] },
        'Database query failed');
    } else {
      // Unknown error — NEVER expose internal details
      status = 500;
      message = 'Internal server error';
      code = 'INTERNAL_ERROR';
      logger.error({ err: exception, requestId: request['requestId'] },
        'Unhandled exception');
    }

    response.status(status).json({
      error: {
        code,
        message,
        requestId: request['requestId'],
        timestamp: new Date().toISOString(),
      },
    });
  }
}
```

---

## 7. Dockerfile (Production)

```dockerfile
# Stage 1: Install dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Stage 2: Build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Production image
FROM gcr.io/distroless/nodejs22-debian12 AS runner

# Non-root user (distroless default: nonroot)
USER nonroot

WORKDIR /app
COPY --from=deps --chown=nonroot:nonroot /app/node_modules ./node_modules
COPY --from=builder --chown=nonroot:nonroot /app/dist ./dist

# Health check port
EXPOSE 8080

# No shell — direct process execution
CMD ["dist/main.js"]
```

---

## 8. Kubernetes Manifests

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
  labels:
    app: my-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0   # Zero-downtime deployments
  selector:
    matchLabels:
      app: my-service
  template:
    metadata:
      labels:
        app: my-service
    spec:
      terminationGracePeriodSeconds: 60
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        fsGroup: 65534
      containers:
        - name: my-service
          image: registry.example.com/my-service:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          env:
            - name: NODE_ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: my-service-secrets
                  key: database-url
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 0
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 30  # Allow up to 2.5 minutes for startup
```

---

## 9. Verification Checklist

- [ ] Health endpoints (`/health/live`, `/health/ready`, `/health/startup`) respond correctly
- [ ] Graceful shutdown drains in-flight requests within 30s
- [ ] Structured JSON logging with requestId and traceId
- [ ] Request validation strips unknown fields (`whitelist: true`)
- [ ] Error responses never expose internal stack traces
- [ ] Container runs as non-root user
- [ ] Connection pool limits configured (PG: max 20, Redis: max 50)
- [ ] Request timeout configured (30s default)
- [ ] Rate limiting active on all public endpoints
- [ ] OpenTelemetry traces propagate across service boundaries
- [ ] Integration tests use Testcontainers (real PG + Redis)
- [ ] Dockerfile uses multi-stage build with distroless base
