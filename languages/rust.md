# 🦀 Rust Production Standard (`rust.md`)

> **Language**: Rust 1.78+ (Edition 2021)  
> **Classification**: Memory-Safe High-Performance Systems  
> **Core Philosophy**: "Zero-Cost Abstractions, Compile-Time Guarantees, No Uncontrolled Panics."

---

## 1. Error Handling (`thiserror` vs `anyhow`)

1. **Libraries / Domain Crates**: Use `thiserror` to define strongly-typed, matchable domain error enums.
2. **Applications / Binaries**: Use `anyhow` for top-level contextual error propagation.

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("Record with key `{0}` not found")]
    NotFound(String),

    #[error("Connection pool exhausted: {0}")]
    PoolExhausted(String),

    #[error(transparent)]
    Unexpected(#[from] anyhow::Error),
}
```

---

## 2. Tokio Async Concurrency

```rust
use tokio::sync::mpsc;
use tracing::{info, error};

#[tokio::main]
async fn main() -> Result<(), anyhow::Ok> {
    let (tx, mut rx) = mpsc::channel::<String>(100);

    // Spawn async background worker
    tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            info!("Received message: {}", msg);
        }
    });

    tx.send("Processing job 101".to_string()).await?;
    Ok(())
}
```

---

## 3. Production Rules for Rust

1. **No `unwrap()` or `expect()` in Production Paths**: Use `?` operator or explicit pattern matching (`match` / `if let`).
2. **Deny Unsafe**: Annotate crates with `#![forbid(unsafe_code)]` unless writing low-level FFI bindings.
3. **Use `clippy` in CI**: Treat all clippy warnings as build-blocking errors (`cargo clippy -- -D warnings`).
