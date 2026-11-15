# ☕ Modern Java 21+ Production Standard (`java.md`)

> **Language**: Java 21 LTS (with Java 23+ preview notes)  
> **Build Tools**: Gradle 8.x (Kotlin DSL) / Maven 3.9+  
> **Frameworks**: Spring Boot 3.3+, Quarkus 3.x, Micronaut 4.x  
> **Core Philosophy**: "Immutable Records, Exhaustive Pattern Matching, Virtual Threads for Throughput, Never Return Null."

---

## 1. Java 21 LTS — Non-Negotiable Language Features

Every new project targeting Java 21+ MUST leverage these finalized features. Legacy patterns (POJOs with getters/setters, manual thread management) MUST NOT be introduced in new code.

### 1.1 Records — Immutable Data Carriers

Records replace boilerplate DTOs, value objects, and data transfer classes. They are `final`, have implicit `equals()`, `hashCode()`, and `toString()`, and enforce immutability.

```java
// ✅ GOOD — Immutable record with compact canonical constructor validation
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount must be non-negative: " + amount);
        }
        Objects.requireNonNull(currency, "Currency must not be null");
        amount = amount.setScale(2, RoundingMode.HALF_UP);
    }

    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new CurrencyMismatchException(this.currency, other.currency);
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
}

// ❌ BAD — Mutable POJO with getters/setters for a value object
public class Money {
    private BigDecimal amount;
    private Currency currency;
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    // ... 40 more lines of boilerplate
}
```

### 1.2 Sealed Classes — Exhaustive Domain Hierarchies

Sealed classes restrict which classes can extend them, enabling compiler-enforced exhaustiveness in `switch` expressions.

```java
public sealed interface PaymentResult
        permits PaymentResult.Success, PaymentResult.Declined, PaymentResult.GatewayError {

    record Success(String transactionId, Money charged, Instant processedAt) implements PaymentResult {}
    record Declined(String reason, String declineCode) implements PaymentResult {}
    record GatewayError(String gatewayName, int httpStatus, String errorBody) implements PaymentResult {}
}
```

### 1.3 Pattern Matching for `switch` (Finalized in Java 21)

Pattern matching eliminates verbose `instanceof` chains and enables exhaustive switching over sealed hierarchies.

```java
// ✅ GOOD — Exhaustive pattern matching with guarded patterns
public String describeResult(PaymentResult result) {
    return switch (result) {
        case PaymentResult.Success s ->
            "Charged %s (tx: %s)".formatted(s.charged(), s.transactionId());
        case PaymentResult.Declined d when "INSUFFICIENT_FUNDS".equals(d.declineCode()) ->
            "Card declined: insufficient funds";
        case PaymentResult.Declined d ->
            "Card declined: %s (%s)".formatted(d.reason(), d.declineCode());
        case PaymentResult.GatewayError e ->
            "Gateway %s error (HTTP %d)".formatted(e.gatewayName(), e.httpStatus());
        // No default needed — compiler enforces exhaustiveness on sealed types
    };
}

// ❌ BAD — instanceof chains with manual casting
public String describeResult(PaymentResult result) {
    if (result instanceof PaymentResult.Success) {
        PaymentResult.Success s = (PaymentResult.Success) result;
        return "Charged " + s.charged();
    } else if (result instanceof PaymentResult.Declined) {
        // ... fragile, no exhaustiveness check
    }
    return "Unknown";
}
```

### 1.4 Text Blocks

Text blocks MUST be used for multi-line strings (SQL, JSON, HTML templates):

```java
String query = """
        SELECT u.id, u.email, u.created_at
        FROM users u
        JOIN orders o ON o.user_id = u.id
        WHERE o.status = ?
          AND u.active = true
        ORDER BY u.created_at DESC
        LIMIT ?
        """;
```

---

## 2. Virtual Threads & Structured Concurrency (Project Loom)

### 2.1 Virtual Threads — Replacing Thread Pools for I/O

Virtual threads (finalized in Java 21) MUST be used for I/O-bound workloads. They are lightweight, managed by the JVM, and eliminate the need for manually tuned thread pools for blocking I/O.

```java
// ✅ GOOD — Virtual thread executor for I/O-bound HTTP handlers
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<OrderSummary>> futures = orderIds.stream()
        .map(id -> executor.submit(() -> orderService.fetchSummary(id)))
        .toList();

    List<OrderSummary> summaries = new ArrayList<>();
    for (var future : futures) {
        summaries.add(future.get(5, TimeUnit.SECONDS));
    }
}

// ❌ BAD — Fixed thread pool for I/O-bound work (wastes platform threads)
ExecutorService pool = Executors.newFixedThreadPool(200);
```

> **WARNING**: Virtual threads MUST NOT be used for CPU-bound computation (e.g., matrix multiplication, encryption). Use platform threads with `ForkJoinPool` for compute-heavy tasks.

> **WARNING**: Avoid `synchronized` blocks with virtual threads — they pin the carrier thread. Use `ReentrantLock` instead.

```java
// ✅ GOOD — ReentrantLock for virtual-thread-safe synchronization
private final ReentrantLock lock = new ReentrantLock();

public void updateCounter() {
    lock.lock();
    try {
        this.counter++;
    } finally {
        lock.unlock();
    }
}

// ❌ BAD — synchronized pins the virtual thread's carrier
public synchronized void updateCounter() {
    this.counter++;
}
```

### 2.2 Structured Concurrency (Preview — Java 23+)

Structured Concurrency (`StructuredTaskScope`) treats groups of concurrent tasks as a single unit of work with automatic cancellation and error propagation. This is a preview feature — use `--enable-preview` explicitly.

```java
// Java 23+ Preview — Structured Concurrency
import java.util.concurrent.StructuredTaskScope;

public record UserProfile(User user, List<Order> orders) {}

public UserProfile fetchUserProfile(UUID userId) throws Exception {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        Subtask<User> userTask = scope.fork(() -> userService.findById(userId));
        Subtask<List<Order>> ordersTask = scope.fork(() -> orderService.findByUserId(userId));

        scope.join();           // Wait for both subtasks
        scope.throwIfFailed();  // Propagate first failure

        return new UserProfile(userTask.get(), ordersTask.get());
    }
    // If userTask fails, ordersTask is automatically cancelled — no resource leak
}
```

---

## 3. Functional Programming & Streams API

### 3.1 Stream Pipeline Patterns

```java
// ✅ GOOD — Clear, composable stream pipeline with method references
public Map<OrderStatus, List<Order>> groupActiveOrders(List<Order> orders) {
    return orders.stream()
        .filter(order -> order.createdAt().isAfter(Instant.now().minus(Duration.ofDays(90))))
        .filter(order -> order.status() != OrderStatus.CANCELLED)
        .collect(Collectors.groupingBy(Order::status, Collectors.toUnmodifiableList()));
}

// ❌ BAD — Mutable collector, imperative loop hidden inside stream
public Map<OrderStatus, List<Order>> groupActiveOrders(List<Order> orders) {
    Map<OrderStatus, List<Order>> result = new HashMap<>();
    orders.forEach(order -> {
        if (order.status() != OrderStatus.CANCELLED) {
            result.computeIfAbsent(order.status(), k -> new ArrayList<>()).add(order);
        }
    });
    return result; // Mutable map leaks internal state
}
```

### 3.2 Optional — Never Return Null

Methods that MAY not produce a result MUST return `Optional<T>`. Calling `.get()` without `.isPresent()` is banned.

```java
// ✅ GOOD — Optional with functional chaining
public Optional<String> findCustomerEmail(UUID customerId) {
    return customerRepository.findById(customerId)
        .filter(Customer::isActive)
        .map(Customer::email);
}

// Caller site — handle absence explicitly
String email = findCustomerEmail(id)
    .orElseThrow(() -> new CustomerNotFoundException(id));

// ❌ BAD — Returning null, forcing caller to guess
public String findCustomerEmail(UUID customerId) {
    Customer c = customerRepository.findById(customerId);
    return c != null ? c.getEmail() : null;  // Null propagates invisibly
}
```

### 3.3 Immutable Collections

ALWAYS prefer immutable factory methods. Mutable collections MUST NOT leak from public APIs.

```java
// ✅ GOOD — Immutable collections
List<String> roles = List.of("ADMIN", "MEMBER", "VIEWER");
Map<String, Integer> limits = Map.of("free", 100, "pro", 10_000, "enterprise", 1_000_000);
Set<String> blocked = Set.of("DROP", "DELETE", "TRUNCATE");

// ✅ GOOD — Creating an unmodifiable copy of a mutable collection
List<OrderLine> lines = Collections.unmodifiableList(new ArrayList<>(mutableLines));

// ❌ BAD — Exposing mutable internal state
public List<OrderLine> getLines() {
    return this.lines; // Caller can mutate internal list
}
```

---

## 4. Exception Handling

### 4.1 Custom Exception Hierarchies

Applications MUST define domain-specific exception types. Never throw raw `RuntimeException` or catch `Throwable`.

```java
// Base domain exception (unchecked — extends RuntimeException for cleaner call sites)
public abstract sealed class DomainException extends RuntimeException
        permits NotFoundException, ConflictException, ValidationException {

    private final String errorCode;
    private final Instant occurredAt;

    protected DomainException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = Objects.requireNonNull(errorCode);
        this.occurredAt = Instant.now();
    }

    public String errorCode() { return errorCode; }
    public Instant occurredAt() { return occurredAt; }
}

public final class NotFoundException extends DomainException {
    public NotFoundException(String resourceType, Object resourceId) {
        super("NOT_FOUND", "%s with id '%s' not found".formatted(resourceType, resourceId), null);
    }
}

public final class ConflictException extends DomainException {
    public ConflictException(String message) {
        super("CONFLICT", message, null);
    }
}

public final class ValidationException extends DomainException {
    private final List<FieldError> fieldErrors;

    public ValidationException(List<FieldError> fieldErrors) {
        super("VALIDATION_ERROR", "Validation failed for %d field(s)".formatted(fieldErrors.size()), null);
        this.fieldErrors = List.copyOf(fieldErrors);
    }

    public List<FieldError> fieldErrors() { return fieldErrors; }

    public record FieldError(String field, String message) {}
}
```

### 4.2 Anti-Patterns

```java
// ❌ NEVER catch Throwable — it swallows OutOfMemoryError, StackOverflowError
try { process(); } catch (Throwable t) { log.error("oops", t); }

// ❌ NEVER catch and swallow
try { process(); } catch (Exception e) { /* silently ignored */ }

// ❌ NEVER log-and-rethrow at every layer (R-056)
try { process(); } catch (Exception e) { log.error("Failed", e); throw e; }

// ✅ DO wrap with context at boundary, log once at the handling layer
try {
    paymentGateway.charge(card, amount);
} catch (GatewayTimeoutException e) {
    throw new PaymentProcessingException("Payment gateway timeout for order " + orderId, e);
}
```

---

## 5. Project Structure & Build Tooling

### 5.1 Maven Multi-Module (BOM Pattern)

```
myapp/
├── pom.xml                    # Parent BOM — dependency versions defined here
├── myapp-domain/              # Pure domain logic, zero framework deps
│   └── pom.xml
├── myapp-application/         # Use cases, ports (interfaces)
│   └── pom.xml
├── myapp-infrastructure/      # DB adapters, HTTP clients, messaging
│   └── pom.xml
└── myapp-web/                 # Spring Boot / Quarkus entry point
    └── pom.xml
```

### 5.2 Gradle Kotlin DSL (`build.gradle.kts`)

```kotlin
// build.gradle.kts — Root project
plugins {
    java
    id("org.springframework.boot") version "3.3.5" apply false
    id("io.spring.dependency-management") version "1.1.6"
    id("com.diffplug.spotless") version "6.25.0"
    id("net.ltgt.errorprone") version "4.1.0"
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

subprojects {
    apply(plugin = "java")
    apply(plugin = "com.diffplug.spotless")

    repositories {
        mavenCentral()
    }

    dependencies {
        compileOnly("com.google.code.findbugs:jsr305:3.0.2")
        errorprone("com.google.errorprone:error_prone_core:2.33.0")
        testImplementation(platform("org.junit:junit-bom:5.11.3"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("org.assertj:assertj-core:3.26.3")
        testImplementation("org.mockito:mockito-core:5.14.2")
    }

    tasks.test {
        useJUnitPlatform()
        jvmArgs("--enable-preview")
    }

    spotless {
        java {
            palantirJavaFormat("2.47.0")
            removeUnusedImports()
        }
    }
}
```

---

## 6. Dependency Injection — Framework Comparison

| Criteria                 | Spring Boot 3.3+       | Quarkus 3.x              | Micronaut 4.x            |
|--------------------------|------------------------|---------------------------|---------------------------|
| DI Mechanism             | Runtime reflection      | Build-time (ArC / CDI)    | Build-time (AOT)          |
| Startup Time             | ~2-4s (JVM)            | ~0.5-1s (JVM)             | ~0.5-1s (JVM)             |
| Native Image             | Spring AOT + GraalVM   | First-class GraalVM       | First-class GraalVM       |
| Ecosystem Size           | Largest                | Growing rapidly           | Moderate                  |
| Recommended For          | Enterprise, monoliths  | Cloud-native, serverless  | Serverless, microservices |

Constructor injection MUST be the default. Field injection (`@Autowired` on fields) is banned.

```java
// ✅ GOOD — Constructor injection (works with records in Micronaut/Quarkus)
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;

    // Single constructor — Spring auto-wires without @Autowired
    public OrderService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        this.orderRepository = Objects.requireNonNull(orderRepository);
        this.paymentGateway = Objects.requireNonNull(paymentGateway);
    }
}

// ❌ BAD — Field injection hides dependencies, breaks testability
@Service
public class OrderService {
    @Autowired private OrderRepository orderRepository;
    @Autowired private PaymentGateway paymentGateway;
}
```

---

## 7. Testing — JUnit 5, Mockito 5, AssertJ, ArchUnit

### 7.1 Unit Test with AssertJ

```java
@Test
void shouldCalculateTotalWithTax() {
    // Given
    var lineItems = List.of(
        new OrderLine("Widget", new Money(new BigDecimal("10.00"), USD), 3),
        new OrderLine("Gadget", new Money(new BigDecimal("25.50"), USD), 1)
    );
    var calculator = new OrderCalculator(TaxRate.of("0.08"));

    // When
    Money total = calculator.calculateTotal(lineItems);

    // Then
    assertThat(total.amount()).isEqualByComparingTo(new BigDecimal("60.94"));
    assertThat(total.currency()).isEqualTo(USD);
}
```

### 7.2 Mockito 5 — Mock at Boundaries Only

```java
@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {

    @Mock private PaymentGateway gateway;       // External boundary — mock allowed
    @Mock private PaymentRepository repository; // DB boundary — mock allowed

    @InjectMocks private PaymentService service;

    @Test
    void shouldReturnDeclinedWhenGatewayRejects() {
        // Given
        when(gateway.charge(any(), any()))
            .thenReturn(new PaymentResult.Declined("Insufficient funds", "INSUFFICIENT_FUNDS"));

        // When
        PaymentResult result = service.processPayment(orderId, card, amount);

        // Then
        assertThat(result).isInstanceOf(PaymentResult.Declined.class);
        assertThat(((PaymentResult.Declined) result).declineCode()).isEqualTo("INSUFFICIENT_FUNDS");
        verify(repository, never()).save(any());
    }
}
```

### 7.3 ArchUnit — Architecture Tests

```java
@AnalyzeClasses(packages = "com.example.myapp")
class ArchitectureTest {

    @ArchTest
    static final ArchRule domainMustNotDependOnInfrastructure =
        noClasses().that().resideInAPackage("..domain..")
            .should().dependOnClassesThat().resideInAPackage("..infrastructure..");

    @ArchTest
    static final ArchRule servicesMustNotAccessControllers =
        noClasses().that().resideInAPackage("..service..")
            .should().dependOnClassesThat().resideInAPackage("..controller..");

    @ArchTest
    static final ArchRule recordsShouldBeImmutable =
        classes().that().areRecords()
            .should().haveOnlyFinalFields();
}
```

---

## 8. Logging — SLF4J + Logback Structured JSON

MUST use SLF4J as the logging facade. Raw `System.out.println` is banned in production code.

```xml
<!-- logback-spring.xml — Structured JSON for production -->
<configuration>
    <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
            <includeMdcKeyName>traceId</includeMdcKeyName>
            <includeMdcKeyName>spanId</includeMdcKeyName>
            <includeMdcKeyName>userId</includeMdcKeyName>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="JSON"/>
    </root>
</configuration>
```

```java
// ✅ GOOD — Parameterized logging with MDC context
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

public class PaymentService {
    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

    public PaymentResult processPayment(UUID orderId, Card card, Money amount) {
        MDC.put("orderId", orderId.toString());
        try {
            log.info("Processing payment of {} {}", amount.amount(), amount.currency());
            PaymentResult result = gateway.charge(card, amount);
            log.info("Payment result: {}", result.getClass().getSimpleName());
            return result;
        } finally {
            MDC.clear();
        }
    }
}

// ❌ BAD — String concatenation in log (evaluated even if level is disabled)
log.debug("Processing order: " + orderId + " with amount: " + amount);
```

---

## 9. Concurrent Programming — CompletableFuture

For existing codebases not yet on Virtual Threads, `CompletableFuture` composition MUST be used instead of blocking `.get()` calls.

```java
public CompletableFuture<DashboardData> loadDashboard(UUID userId) {
    CompletableFuture<UserProfile> profileFuture = userClient.fetchProfile(userId);
    CompletableFuture<List<Notification>> notificationsFuture = notificationClient.fetchRecent(userId);
    CompletableFuture<AccountBalance> balanceFuture = billingClient.fetchBalance(userId);

    return profileFuture.thenCombine(notificationsFuture, (profile, notifications) ->
        balanceFuture.thenApply(balance ->
            new DashboardData(profile, notifications, balance))
    ).thenCompose(Function.identity())
     .orTimeout(3, TimeUnit.SECONDS)
     .exceptionally(ex -> {
         log.error("Dashboard load failed for user {}", userId, ex);
         return DashboardData.empty();
     });
}
```

---

## 10. Memory Management & JVM Production Flags

### 10.1 GC Selection

| GC          | Use Case                                | Flag                        |
|-------------|------------------------------------------|-----------------------------|
| **ZGC**     | Low-latency services (p99 < 10ms pause) | `-XX:+UseZGC`               |
| **G1GC**    | General-purpose (default since Java 9)  | `-XX:+UseG1GC`              |
| **Shenandoah** | Ultra-low pause (RedHat JDKs)        | `-XX:+UseShenandoahGC`      |

### 10.2 Production JVM Flags

```bash
java \
  -XX:+UseZGC \
  -XX:MaxRAMPercentage=75.0 \
  -XX:InitialRAMPercentage=50.0 \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/var/log/heapdumps/ \
  -XX:+ExitOnOutOfMemoryError \
  -Djava.security.egd=file:/dev/urandom \
  -XX:+UseStringDeduplication \
  -XX:MaxGCPauseMillis=50 \
  -XX:+PrintFlagsFinal \
  --enable-preview \
  -jar myapp.jar
```

> **IMPORTANT**: In containers, ALWAYS use `-XX:MaxRAMPercentage` instead of `-Xmx` to respect cgroup memory limits. Never set `-Xmx` higher than 75% of the container memory limit — leave room for off-heap (Metaspace, thread stacks, NIO buffers).

---

## 11. Code Quality Tooling

### 11.1 Error Prone (Compile-Time Bug Detection)

Error Prone (by Google) catches common bugs at compile time as a `javac` plugin.

```kotlin
// build.gradle.kts
dependencies {
    errorprone("com.google.errorprone:error_prone_core:2.33.0")
    // Optional: additional checks
    errorprone("com.uber.nullaway:NullAway:0.11.3")
}

tasks.withType<JavaCompile>().configureEach {
    options.errorprone {
        error("NullAway")
        option("NullAway:AnnotatedPackages", "com.example")
    }
}
```

### 11.2 SpotBugs & Checkstyle

```kotlin
// build.gradle.kts
plugins {
    id("com.github.spotbugs") version "6.0.24"
    id("checkstyle")
}

spotbugs {
    effort = com.github.spotbugs.snom.Effort.MAX
    reportLevel = com.github.spotbugs.snom.Confidence.MEDIUM
    excludeFilter = file("config/spotbugs-exclude.xml")
}

checkstyle {
    toolVersion = "10.20.1"
    configFile = file("config/checkstyle/checkstyle.xml")
    maxWarnings = 0  // Zero tolerance
}
```

---

## 12. GraalVM Native Image

For serverless / CLI applications, GraalVM native-image compilation SHOULD be considered. Key constraints:

```java
// ✅ GOOD — Reflection-free record (works out of the box with native-image)
public record HealthResponse(String status, Instant checkedAt) {}

// ❌ BAD — Dynamic class loading / reflection (requires manual native-image config)
Class<?> clazz = Class.forName(className);
Object instance = clazz.getDeclaredConstructor().newInstance();
```

**Native image build (Spring Boot 3.x)**:
```bash
# Requires GraalVM 21+ with native-image installed
./gradlew nativeCompile

# Or with Maven
./mvnw -Pnative native:compile
```

**Key limitations to document in ADRs**:
- Reflection, JNI, and dynamic proxies MUST be declared in `reflect-config.json`
- Startup time drops from ~2-4s to ~50-150ms
- Build time increases significantly (~3-8 minutes)
- Runtime memory footprint reduced by 50-80%

---

## 13. Security Considerations

- **Deserialization**: MUST NOT use `ObjectInputStream` for untrusted data (OWASP A08:2021). Use Jackson or Protocol Buffers exclusively. See [`../security.md`](../security.md).
- **SQL Injection**: All database queries MUST use parameterized prepared statements. Never concatenate user input into JPQL/SQL strings.
- **Dependency Scanning**: Run `./gradlew dependencyCheckAnalyze` (OWASP Dependency-Check plugin) on every build. Block merges on CVEs with CVSS ≥ 7.0.
- **Secrets**: Use Spring Cloud Config / HashiCorp Vault / environment variables. Never embed credentials in `application.yml`.

---

## 14. Common Pitfalls & Anti-Patterns

| #  | Anti-Pattern                              | Correct Approach                                              |
|----|-------------------------------------------|---------------------------------------------------------------|
| 1  | Returning `null` from methods             | Return `Optional<T>` or throw a domain exception              |
| 2  | Catching `Throwable` or `Exception` broadly | Catch specific exceptions; let `Error` subclasses propagate |
| 3  | `synchronized` with Virtual Threads       | Use `ReentrantLock` to avoid carrier thread pinning            |
| 4  | Mutable DTOs with setters                 | Use `record` types for all data carriers                       |
| 5  | Field injection (`@Autowired` on fields)  | Constructor injection exclusively                              |
| 6  | `System.out.println` for logging          | SLF4J + Logback with structured JSON                           |
| 7  | String concatenation in log statements    | Parameterized logging: `log.info("User {}", id)`              |
| 8  | Raw thread creation (`new Thread(...)`)   | Virtual threads or `ExecutorService`                           |
| 9  | Unbounded `SELECT *` without `LIMIT`      | Always paginate with keyset/cursor pagination                  |
| 10 | Ignoring `CompletableFuture` exceptions   | Always chain `.exceptionally()` or `.handle()`                 |

---

## 15. Verification Checklist

Before merging any Java PR, verify:

- [ ] Java 21+ toolchain is enforced in `build.gradle.kts` or `pom.xml`
- [ ] All value objects use `record` types with compact canonical constructors
- [ ] Sealed type hierarchies have exhaustive `switch` expressions (no `default` branch)
- [ ] No method returns `null` — `Optional<T>` or domain exception used instead
- [ ] Virtual threads used for I/O-bound executors; no `synchronized` in virtual thread paths
- [ ] `ReentrantLock` replaces `synchronized` where virtual threads are used
- [ ] Custom domain exception hierarchy extends a sealed base exception
- [ ] Constructor injection only — zero `@Autowired` field annotations
- [ ] SLF4J parameterized logging — zero string concatenation in log statements
- [ ] JVM flags include `-XX:+UseZGC -XX:MaxRAMPercentage=75.0 -XX:+ExitOnOutOfMemoryError`
- [ ] Error Prone and/or SpotBugs enabled with zero warnings policy
- [ ] JUnit 5 + AssertJ used; tests follow Given-When-Then structure
- [ ] ArchUnit tests enforce package dependency rules
- [ ] Collections exposed via public API are immutable (`List.of`, `Collections.unmodifiable*`)
- [ ] GraalVM native-image compatibility verified if targeting serverless deployment
- [ ] OWASP Dependency-Check runs in CI with CVSS ≥ 7.0 blocking threshold

---

*Cross-references: [`../RULES.md`](../RULES.md) (R-033 Strict Typing, R-039 Immutability, R-043 Nullability, R-047 Domain Exceptions), [`../security.md`](../security.md), [`../sections/testing-qa/test-pyramid.md`](../sections/testing-qa/test-pyramid.md), [`../sections/devops-infrastructure/docker-containers.md`](../sections/devops-infrastructure/docker-containers.md)*
