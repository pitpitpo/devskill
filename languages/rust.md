# 🦀 Rust Production Standard (`rust.md`)

> **Language**: Rust 1.78+ (Edition 2021)  
> **Classification**: Memory-Safe High-Performance Systems  
> **Core Philosophy**: "Zero-Cost Abstractions, Compile-Time Guarantees, No Uncontrolled Panics."

---

## 1. Overview / When to Use

Rust is the right choice when you need:
- **Memory safety without garbage collection** — embedded systems, OS kernels, databases, game engines.
- **Predictable latency** — real-time systems, trading engines, audio/video pipelines.
- **Fearless concurrency** — data-parallel workloads, async network services.
- **FFI boundaries** — replacing C/C++ hotspots or exposing safe APIs to other languages.
- **WebAssembly targets** — high-performance browser modules.

Rust is likely overkill when:
- Rapid prototyping speed matters more than runtime safety (use Python/Go).
- The team has zero Rust experience and the deadline is < 4 weeks.
- The project is pure CRUD with no performance-sensitive paths (use Go, TypeScript, etc.).

---

## 2. Core Concepts & Architecture

### 2.1 Ownership & Borrowing Deep Dive

Rust's ownership system is the foundation of its safety guarantees. Every value has exactly one owner, and when the owner goes out of scope, the value is dropped.

```rust
// MOVE semantics — ownership transfers, original binding is invalidated
fn main() {
    let s1 = String::from("hello");
    let s2 = s1;           // s1 is MOVED into s2
    // println!("{s1}");   // ❌ Compile error: value used after move

    // CLONE — explicit deep copy when you need both
    let s3 = s2.clone();
    println!("{s2} {s3}"); // ✅ Both valid
}
```

**Borrowing rules** (enforced at compile time):
1. You can have **either** one mutable reference (`&mut T`) **or** any number of immutable references (`&T`) — never both simultaneously.
2. References must always be valid (no dangling pointers).

```rust
fn process(data: &[u8]) -> usize {
    // Immutable borrow — can read, cannot modify
    data.len()
}

fn append(data: &mut Vec<u8>, item: u8) {
    // Mutable borrow — exclusive access
    data.push(item);
}

fn main() {
    let mut buffer = vec![1, 2, 3];

    // Multiple immutable borrows — OK
    let len1 = process(&buffer);
    let len2 = process(&buffer);

    // Mutable borrow — OK because no immutable borrows are active
    append(&mut buffer, 4);

    // ❌ This would fail:
    // let r = &buffer;
    // append(&mut buffer, 5);  // Cannot borrow mutably while `r` is alive
    // println!("{:?}", r);
}
```

**Interior mutability** — when you need mutation behind a shared reference:

```rust
use std::cell::RefCell;
use std::sync::{Arc, Mutex};

// Single-threaded interior mutability
let data = RefCell::new(vec![1, 2, 3]);
data.borrow_mut().push(4); // Runtime borrow check

// Thread-safe interior mutability
let shared = Arc::new(Mutex::new(0));
let clone = Arc::clone(&shared);
std::thread::spawn(move || {
    let mut val = clone.lock().unwrap();
    *val += 1;
});
```

### 2.2 Lifetimes

Lifetimes are Rust's way of ensuring references don't outlive the data they point to. Most lifetimes are inferred; you annotate only when the compiler cannot deduce relationships.

```rust
// Explicit lifetime: the returned reference lives as long as BOTH inputs
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Struct holding a reference — must declare lifetime
struct Config<'a> {
    database_url: &'a str,
    max_connections: u32,
}

impl<'a> Config<'a> {
    fn db_host(&self) -> &str {
        // Lifetime elision: output lifetime = &self lifetime
        self.database_url.split('@').nth(1).unwrap_or("localhost")
    }
}
```

**Lifetime elision rules** (when you can omit annotations):
1. Each input reference gets its own lifetime parameter.
2. If there's exactly one input lifetime, it's assigned to all output lifetimes.
3. If one input is `&self` or `&mut self`, its lifetime is assigned to all output lifetimes.

**Common lifetime gotchas:**

```rust
// ❌ Dangling reference — won't compile
fn bad() -> &str {
    let s = String::from("hello");
    &s // s is dropped here, reference would dangle
}

// ✅ Return owned data instead
fn good() -> String {
    String::from("hello")
}

// 'static lifetime — data lives for the entire program
fn static_str() -> &'static str {
    "I live forever"  // String literals are 'static
}
```

### 2.3 Trait System

Traits are Rust's mechanism for polymorphism — similar to interfaces but with default implementations, associated types, and static dispatch.

```rust
// Define a trait with an associated type and default method
trait Repository {
    type Item;
    type Error;

    fn find_by_id(&self, id: &str) -> Result<Self::Item, Self::Error>;
    fn save(&self, item: &Self::Item) -> Result<(), Self::Error>;

    // Default implementation
    fn exists(&self, id: &str) -> bool {
        self.find_by_id(id).is_ok()
    }
}

// Implement for a concrete type
struct PostgresUserRepo {
    pool: sqlx::PgPool,
}

impl Repository for PostgresUserRepo {
    type Item = User;
    type Error = sqlx::Error;

    fn find_by_id(&self, id: &str) -> Result<User, sqlx::Error> {
        // implementation
        todo!()
    }

    fn save(&self, item: &User) -> Result<(), sqlx::Error> {
        // implementation
        todo!()
    }
}
```

**Trait bounds & dynamic dispatch:**

```rust
// Static dispatch (monomorphization) — zero cost, larger binary
fn process_static(repo: &impl Repository<Item = User>) {
    // Compiler generates a specialized version for each concrete type
}

// Equivalent with where clause (preferred for complex bounds)
fn process_where<R>(repo: &R)
where
    R: Repository<Item = User> + Send + Sync,
{
    // ...
}

// Dynamic dispatch (vtable) — smaller binary, slight runtime cost
fn process_dynamic(repo: &dyn Repository<Item = User, Error = anyhow::Error>) {
    // Single compiled function, dispatches via vtable at runtime
}

// Trait objects in collections
let repos: Vec<Box<dyn Repository<Item = User, Error = anyhow::Error>>> = vec![
    Box::new(postgres_repo),
    Box::new(mock_repo),
];
```

**When to use static vs dynamic dispatch:**

| Factor | Static (`impl Trait` / generics) | Dynamic (`dyn Trait`) |
|---|---|---|
| Performance | Zero-cost, inlined | Vtable indirection (~1-2ns per call) |
| Binary size | Larger (monomorphized copies) | Smaller (single implementation) |
| Heterogeneous collections | ❌ Not possible | ✅ `Vec<Box<dyn Trait>>` |
| Compile times | Slower | Faster |
| Use when | Hot paths, known types | Plugin systems, collections of mixed types |

---

## 3. Error Handling

### 3.1 `thiserror` for Libraries

Use `thiserror` in library crates to define strongly-typed, matchable error enums:

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("Record with key `{0}` not found")]
    NotFound(String),

    #[error("Connection pool exhausted after {timeout_ms}ms")]
    PoolExhausted { timeout_ms: u64 },

    #[error("Constraint violation on table `{table}`: {detail}")]
    ConstraintViolation { table: String, detail: String },

    #[error("Migration failed: {0}")]
    MigrationFailed(String),

    #[error(transparent)]
    Sqlx(#[from] sqlx::Error),

    #[error(transparent)]
    Unexpected(#[from] anyhow::Error),
}
```

### 3.2 `anyhow` for Applications

Use `anyhow` at the application/binary level for ergonomic, contextual error propagation:

```rust
use anyhow::{Context, Result, bail, ensure};

async fn load_config(path: &str) -> Result<AppConfig> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read config file: {path}"))?;

    let config: AppConfig = toml::from_str(&content)
        .context("Failed to parse config as TOML")?;

    ensure!(config.port > 0, "Port must be positive, got {}", config.port);

    if config.database_url.is_empty() {
        bail!("DATABASE_URL must not be empty");
    }

    Ok(config)
}
```

### 3.3 Error Handling Decision Matrix

| Context | Crate | Pattern |
|---|---|---|
| Library / public API | `thiserror` | Typed enum, callers can `match` |
| Binary / application top-level | `anyhow` | Context chains, readable error reports |
| Tests | `anyhow` or plain `Result<(), Box<dyn Error>>` | Simplicity wins |
| FFI boundary | Manual `Result` → C error codes | No panics across FFI ever |
| `no_std` | Custom enums, no heap | `#[derive(Debug)]` only |

### 3.4 The `?` Operator & Conversion Chain

```rust
// The ? operator:
// 1. On Ok(v), unwraps and continues
// 2. On Err(e), converts via From::from(e) and returns early
//
// This means your error type must implement From<SourceError>
// thiserror's #[from] attribute does this automatically

fn pipeline() -> Result<Output, AppError> {
    let raw = read_file()?;           // io::Error → AppError via From
    let parsed = parse_json(&raw)?;   // serde::Error → AppError via From
    let result = validate(parsed)?;   // ValidationError → AppError via From
    Ok(result)
}
```

---

## 4. Async Rust with Tokio

### 4.1 Runtime Setup

```rust
use tokio::sync::mpsc;
use tracing::{info, error, instrument};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing subscriber
    tracing_subscriber::fmt()
        .with_env_filter("info,my_app=debug")
        .json()
        .init();

    let (tx, mut rx) = mpsc::channel::<String>(100);

    // Spawn async background worker
    let worker = tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            info!(message = %msg, "Processing message");
        }
    });

    tx.send("Processing job 101".to_string()).await?;
    drop(tx); // Close the channel so the worker can exit
    worker.await?;

    Ok(())
}
```

### 4.2 Structured Concurrency Patterns

```rust
use tokio::task::JoinSet;
use tokio::time::{timeout, Duration};

// Pattern: Fan-out with JoinSet (preferred over raw spawn)
async fn fetch_all(urls: Vec<String>) -> Vec<Result<String, reqwest::Error>> {
    let mut set = JoinSet::new();

    for url in urls {
        set.spawn(async move {
            reqwest::get(&url).await?.text().await
        });
    }

    let mut results = Vec::new();
    while let Some(res) = set.join_next().await {
        match res {
            Ok(inner) => results.push(inner),
            Err(join_err) => error!("Task panicked: {join_err}"),
        }
    }
    results
}

// Pattern: Timeout wrapper
async fn with_deadline<T, F: std::future::Future<Output = T>>(
    duration: Duration,
    fut: F,
) -> anyhow::Result<T> {
    timeout(duration, fut)
        .await
        .map_err(|_| anyhow::anyhow!("Operation timed out after {duration:?}"))
}

// Pattern: Graceful shutdown
async fn run_server(mut shutdown: tokio::sync::watch::Receiver<bool>) {
    loop {
        tokio::select! {
            _ = shutdown.changed() => {
                info!("Shutdown signal received, draining...");
                break;
            }
            _ = accept_connection() => {
                // handle connection
            }
        }
    }
}
```

### 4.3 Async Anti-Patterns

```rust
// ❌ Holding a MutexGuard across an await point
let mut guard = mutex.lock().await;
some_async_fn().await;  // Guard held across await — can deadlock
drop(guard);

// ✅ Minimize lock scope
{
    let mut guard = mutex.lock().await;
    guard.push(item);
} // Guard dropped before any await
some_async_fn().await;

// ❌ Blocking the async runtime
async fn bad() {
    std::thread::sleep(Duration::from_secs(5)); // Blocks the executor thread!
}

// ✅ Use tokio's async sleep or spawn_blocking
async fn good() {
    tokio::time::sleep(Duration::from_secs(5)).await;
}

async fn cpu_heavy() {
    let result = tokio::task::spawn_blocking(|| {
        // CPU-intensive work goes here
        compute_hash(&large_data)
    }).await.unwrap();
}
```

---

## 5. Cargo Workspace Setup

### 5.1 Workspace Structure

```
my-project/
├── Cargo.toml              # Workspace root
├── Cargo.lock              # Shared lockfile
├── crates/
│   ├── api/                # HTTP server binary
│   │   ├── Cargo.toml
│   │   └── src/
│   │       └── main.rs
│   ├── core/               # Domain logic library
│   │   ├── Cargo.toml
│   │   └── src/
│   │       └── lib.rs
│   ├── db/                 # Database layer
│   │   ├── Cargo.toml
│   │   └── src/
│   │       └── lib.rs
│   └── common/             # Shared types and utilities
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs
└── tests/                  # Integration tests
    └── integration.rs
```

### 5.2 Workspace Root `Cargo.toml`

```toml
[workspace]
resolver = "2"
members = ["crates/*"]

# Share dependency versions across all crates
[workspace.dependencies]
tokio = { version = "1.38", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"
thiserror = "2"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
sqlx = { version = "0.8", features = ["runtime-tokio", "postgres", "migrate"] }
reqwest = { version = "0.12", features = ["json"] }

# Shared lint configuration
[workspace.lints.rust]
unsafe_code = "forbid"
unused_must_use = "deny"

[workspace.lints.clippy]
all = { level = "deny", priority = -1 }
pedantic = { level = "warn", priority = -1 }
unwrap_used = "deny"
expect_used = "warn"
panic = "deny"
```

### 5.3 Crate-Level `Cargo.toml`

```toml
[package]
name = "my-api"
version = "0.1.0"
edition = "2021"

[dependencies]
# Inherit from workspace — single source of truth for versions
tokio.workspace = true
serde.workspace = true
anyhow.workspace = true
tracing.workspace = true
my-core = { path = "../core" }
my-db = { path = "../db" }

[lints]
workspace = true

[dev-dependencies]
tokio = { workspace = true, features = ["test-util"] }
```

---

## 6. Testing

### 6.1 Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_valid_config() {
        let input = r#"{ "port": 8080, "host": "0.0.0.0" }"#;
        let config = Config::parse(input).unwrap();
        assert_eq!(config.port, 8080);
        assert_eq!(config.host, "0.0.0.0");
    }

    #[test]
    fn parse_invalid_port_returns_error() {
        let input = r#"{ "port": -1, "host": "0.0.0.0" }"#;
        let err = Config::parse(input).unwrap_err();
        assert!(err.to_string().contains("port"));
    }

    // Async test with tokio
    #[tokio::test]
    async fn fetches_user_by_id() {
        let repo = InMemoryUserRepo::default();
        repo.save(&User::new("user-1", "Alice")).await.unwrap();

        let user = repo.find_by_id("user-1").await.unwrap();
        assert_eq!(user.name, "Alice");
    }
}
```

### 6.2 Integration Tests with Test Fixtures

```rust
// tests/api_integration.rs
use my_api::app;
use axum::http::StatusCode;
use axum_test::TestServer;

async fn setup() -> TestServer {
    let app = app::create_app().await;
    TestServer::new(app).unwrap()
}

#[tokio::test]
async fn health_check_returns_200() {
    let server = setup().await;
    let response = server.get("/health").await;
    response.assert_status(StatusCode::OK);
}

#[tokio::test]
async fn create_user_returns_201() {
    let server = setup().await;
    let response = server
        .post("/api/users")
        .json(&serde_json::json!({ "name": "Alice", "email": "alice@example.com" }))
        .await;
    response.assert_status(StatusCode::CREATED);
}
```

### 6.3 Property-Based Testing with `proptest`

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn roundtrip_serialization(name in "[a-zA-Z]{1,50}", age in 0u32..200) {
        let user = User { name: name.clone(), age };
        let json = serde_json::to_string(&user).unwrap();
        let decoded: User = serde_json::from_str(&json).unwrap();
        assert_eq!(decoded.name, name);
        assert_eq!(decoded.age, age);
    }
}
```

---

## 7. Serde Patterns

### 7.1 Common Derive Patterns

```rust
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiResponse<T: Serialize> {
    pub data: T,
    pub request_id: String,

    #[serde(with = "chrono::serde::ts_milliseconds")]
    pub timestamp: DateTime<Utc>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub pagination: Option<Pagination>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pagination {
    pub page: u32,
    pub per_page: u32,
    pub total: u64,
}
```

### 7.2 Enum Representations

```rust
// Tagged enum (default) — { "type": "Circle", "radius": 5.0 }
#[derive(Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

// Adjacently tagged — { "type": "Circle", "data": { "radius": 5.0 } }
#[derive(Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum Event {
    UserCreated { user_id: String },
    OrderPlaced { order_id: String, total: f64 },
}

// Untagged — tries each variant in order (use sparingly)
#[derive(Serialize, Deserialize)]
#[serde(untagged)]
pub enum Value {
    Integer(i64),
    Float(f64),
    Text(String),
}
```

### 7.3 Custom Deserialization

```rust
use serde::de;

// Deserialize a string that must be non-empty
fn non_empty_string<'de, D>(deserializer: D) -> Result<String, D::Error>
where
    D: de::Deserializer<'de>,
{
    let s = String::deserialize(deserializer)?;
    if s.is_empty() {
        Err(de::Error::custom("string must not be empty"))
    } else {
        Ok(s)
    }
}

#[derive(Deserialize)]
struct CreateUser {
    #[serde(deserialize_with = "non_empty_string")]
    name: String,
}
```

---

## 8. Unsafe Rust Guidelines

### 8.1 When Unsafe Is Acceptable

- FFI calls to C libraries (unavoidable).
- Performance-critical sections where the compiler cannot prove safety (rare).
- Implementing low-level data structures (e.g., lock-free queues).

### 8.2 Rules for Unsafe Code

```rust
// Rule 1: Minimize the unsafe block — wrap in a safe public API
pub fn get_unchecked(slice: &[u8], index: usize) -> u8 {
    assert!(index < slice.len(), "index out of bounds");
    // SAFETY: We just verified `index < slice.len()` above,
    // so this access is within bounds.
    unsafe { *slice.get_unchecked(index) }
}

// Rule 2: ALWAYS document the safety invariant with a // SAFETY comment
// Rule 3: Use #[deny(unsafe_op_in_unsafe_fn)] to require unsafe blocks inside unsafe fns
#[deny(unsafe_op_in_unsafe_fn)]
unsafe fn raw_pointer_deref(ptr: *const u8) -> u8 {
    // SAFETY: Caller guarantees ptr is non-null, aligned, and points to valid memory.
    unsafe { *ptr }
}

// Rule 4: Test unsafe code with Miri
// cargo +nightly miri test
```

### 8.3 Crate-Level Safety Configuration

```rust
// In lib.rs or main.rs — forbid unsafe in the entire crate
#![forbid(unsafe_code)]

// For crates that MUST use unsafe, audit with:
// cargo install cargo-audit
// cargo audit
// cargo install cargo-geiger
// cargo geiger   # Shows unsafe usage in all dependencies
```

---

## 9. FFI (Foreign Function Interface)

```rust
// Calling C from Rust
extern "C" {
    fn compress(
        dest: *mut u8,
        dest_len: *mut libc::c_ulong,
        source: *const u8,
        source_len: libc::c_ulong,
    ) -> libc::c_int;
}

pub fn safe_compress(data: &[u8]) -> Result<Vec<u8>, CompressionError> {
    let mut dest = vec![0u8; data.len() + 128]; // over-allocate
    let mut dest_len = dest.len() as libc::c_ulong;

    // SAFETY: dest and data are valid slices; dest_len is correctly initialized
    let ret = unsafe {
        compress(
            dest.as_mut_ptr(),
            &mut dest_len,
            data.as_ptr(),
            data.len() as libc::c_ulong,
        )
    };

    if ret != 0 {
        return Err(CompressionError::Failed(ret));
    }

    dest.truncate(dest_len as usize);
    Ok(dest)
}

// Exposing Rust to C
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}

// CRITICAL: Never panic across FFI boundary — catch and convert
#[no_mangle]
pub extern "C" fn rust_process(data: *const u8, len: usize) -> i32 {
    let result = std::panic::catch_unwind(|| {
        let slice = unsafe { std::slice::from_raw_parts(data, len) };
        process_data(slice)
    });
    match result {
        Ok(Ok(_)) => 0,
        Ok(Err(_)) => -1,
        Err(_panic) => -2,  // Panic was caught
    }
}
```

---

## 10. Clippy Lints & CI Configuration

### 10.1 Recommended Clippy Configuration

```toml
# In clippy.toml at workspace root
too-many-arguments-threshold = 6
type-complexity-threshold = 350
cognitive-complexity-threshold = 25
```

### 10.2 CI Pipeline

```yaml
# .github/workflows/rust.yml
name: Rust CI
on: [push, pull_request]

env:
  CARGO_TERM_COLOR: always
  RUSTFLAGS: "-D warnings"

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt

      - name: Format check
        run: cargo fmt --all -- --check

      - name: Clippy
        run: cargo clippy --all-targets --all-features -- -D warnings

      - name: Tests
        run: cargo test --all-features

      - name: Doc tests
        run: cargo test --doc

  # Run Miri for unsafe code verification
  miri:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@nightly
        with:
          components: miri
      - run: cargo +nightly miri test
```

---

## 11. Performance Tuning

### 11.1 Release Profile

```toml
# Cargo.toml
[profile.release]
opt-level = 3
lto = "fat"           # Full link-time optimization
codegen-units = 1     # Single codegen unit for max optimization
panic = "abort"       # Smaller binary, no unwinding overhead
strip = "symbols"     # Strip debug symbols from release

[profile.release-with-debug]
inherits = "release"
debug = true          # Keep debug info for profiling
strip = "none"
```

### 11.2 Common Performance Patterns

```rust
// Avoid unnecessary allocations — use iterators
// ❌ Allocates intermediate Vec
let result: Vec<_> = items.iter().map(|x| x * 2).collect();
let sum: i64 = result.iter().sum();

// ✅ Zero-allocation iterator chain
let sum: i64 = items.iter().map(|x| x * 2).sum();

// Pre-allocate when final size is known
let mut results = Vec::with_capacity(items.len());
for item in &items {
    results.push(transform(item));
}

// Use &str instead of String when you don't need ownership
fn greet(name: &str) -> String {  // Accept &str, not String
    format!("Hello, {name}!")
}

// Use Cow<str> for conditional ownership
use std::borrow::Cow;

fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains('\t') {
        Cow::Owned(input.replace('\t', "    "))
    } else {
        Cow::Borrowed(input) // No allocation needed
    }
}
```

### 11.3 Benchmarking with `criterion`

```rust
// benches/my_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_parser(c: &mut Criterion) {
    let input = include_str!("../fixtures/large_input.json");

    c.bench_function("parse_json", |b| {
        b.iter(|| {
            let _parsed: serde_json::Value =
                serde_json::from_str(black_box(input)).unwrap();
        })
    });
}

criterion_group!(benches, benchmark_parser);
criterion_main!(benches);
```

---

## 12. Macro Basics

### 12.1 Declarative Macros (`macro_rules!`)

```rust
// Simple utility macro
macro_rules! map {
    ($($key:expr => $value:expr),* $(,)?) => {{
        let mut m = std::collections::HashMap::new();
        $(m.insert($key, $value);)*
        m
    }};
}

let config = map! {
    "host" => "localhost",
    "port" => "8080",
};

// Retry macro for flaky operations
macro_rules! retry {
    ($attempts:expr, $body:expr) => {{
        let mut last_err = None;
        for attempt in 1..=$attempts {
            match $body {
                Ok(val) => return Ok(val),
                Err(e) => {
                    tracing::warn!(attempt, error = %e, "Retrying...");
                    last_err = Some(e);
                }
            }
        }
        Err(last_err.unwrap())
    }};
}
```

### 12.2 Derive Macros (Proc Macros)

```rust
// Using derive macros — most common in production Rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct User {
    pub id: String,
    pub email: String,
}

// Common derive macro crates:
// - serde:       Serialize, Deserialize
// - thiserror:   Error
// - strum:       EnumString, Display, EnumIter
// - derive_more: From, Into, Display, Constructor
// - sqlx:        FromRow
// - clap:        Parser, Subcommand
```

---

## 13. Common Mistakes & Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `unwrap()` / `expect()` in prod | Panics crash the process | Use `?` or explicit `match` |
| `clone()` everywhere | Hidden performance cost | Borrow where possible, use `Cow` or `Arc` |
| Spawning unbounded tasks | OOM under load | Use `Semaphore` or `JoinSet` with limits |
| `String` in function params | Forces callers to allocate | Accept `&str` or `impl AsRef<str>` |
| Ignoring `must_use` values | Silently dropped results | Always handle `Result` and `Option` |
| `Arc<Mutex<Vec<_>>>` for everything | Lock contention | Consider `DashMap`, channels, or sharding |
| Blocking in async context | Starves the executor | Use `spawn_blocking` for CPU work |
| Over-using `dyn Trait` | Unnecessary vtable indirection | Use generics unless you need heterogeneous collections |
| Massive `match` arms in one function | Unreadable, untestable | Extract each arm into its own function |
| Not running `cargo clippy` | Misses common bugs | Add `clippy -- -D warnings` to CI |

---

## 14. Production Readiness Checklist

- [ ] `#![forbid(unsafe_code)]` or all unsafe blocks have `// SAFETY` comments
- [ ] No `unwrap()` or `expect()` on production code paths
- [ ] `cargo clippy -- -D warnings` passes with zero warnings
- [ ] `cargo fmt --check` passes
- [ ] All public APIs have doc comments (`///`)
- [ ] Error types use `thiserror` (libraries) or `anyhow` (binaries)
- [ ] Structured logging via `tracing` (not `println!`)
- [ ] Graceful shutdown handles `SIGTERM` / `SIGINT`
- [ ] `Cargo.lock` committed for binaries (not for libraries)
- [ ] Release profile configured with `lto`, `codegen-units = 1`
- [ ] Dependencies audited with `cargo audit`
- [ ] Benchmarks exist for performance-critical paths
- [ ] Integration tests cover happy path + error paths
- [ ] `MSRV` (minimum supported Rust version) documented in `Cargo.toml`

---

## 15. Security Considerations

- **Dependency auditing**: Run `cargo audit` in CI to catch known vulnerabilities.
- **Supply chain**: Use `cargo-vet` or `cargo-crev` to verify third-party crate trustworthiness.
- **Secrets**: Never hardcode secrets. Use environment variables via `std::env::var()` or a secrets manager.
- **Input validation**: Validate and sanitize all external input at API boundaries before passing to internal functions.
- **Constant-time comparison**: Use `subtle::ConstantTimeEq` for comparing secrets/tokens to prevent timing attacks.
- **Integer overflow**: In debug builds Rust panics on overflow; in release it wraps. Use `checked_add()`, `saturating_add()`, or `wrapping_add()` explicitly.
- **Unsafe audit surface**: Run `cargo geiger` to quantify unsafe usage across all dependencies.

---

## 16. References & Further Reading

- [The Rust Programming Language (The Book)](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Asynchronous Programming in Rust](https://rust-lang.github.io/async-book/)
- [The Rustonomicon (Unsafe Rust)](https://doc.rust-lang.org/nomicon/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Tokio Documentation](https://tokio.rs/)
- [Serde Documentation](https://serde.rs/)
- [Clippy Lint List](https://rust-lang.github.io/rust-clippy/master/)
- [Criterion.rs Benchmarking](https://bheisler.github.io/criterion.rs/book/)
