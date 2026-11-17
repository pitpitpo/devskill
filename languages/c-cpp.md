# ⚡ Modern C23 & C++23/26 Systems Engineering (`languages/c-cpp.md`)

> **Classification**: Systems Programming, Low-Level Memory Safety, High-Performance Systems  
> **Target Standards**: ISO C23 (C2x), ISO C++23, ISO C++26 Draft  
> **Prerequisites**: Clang 18+, GCC 14+, CMake 3.28+, Sanitizers (ASan, TSan, UBSan, MSan), Valgrind  
> **Governing Rules**: **R-001** (Zero TODOs), **R-033** (Strict Static Typing), **R-034** (Zero Raw Pointer Leaks), **R-038** (Zero Magic Values), **R-039** (Const-Correctness)  
> **Last Updated**: 2026-11-17  

---

## 1. Frontmatter & Metadata

| Attribute | Specification |
|---|---|
| **Language Standards** | C23 (`-std=c23`), C++23 (`-std=c++23`), C++26 draft features |
| **Compiler Toolchains** | LLVM Clang 18+, GNU GCC 14+, MSVC 19.38+ |
| **Memory Model** | C++ Memory Model (Acquire-Release, Sequentially Consistent, Relaxed), RAII |
| **Safety Tooling** | AddressSanitizer (ASan), UndefinedBehaviorSanitizer (UBSan), ThreadSanitizer (TSan) |
| **Key Invariant Rules** | Zero manual `malloc`/`free` or raw `new`/`delete` in application code; strict RAII with `std::unique_ptr` and `std::shared_ptr`; bounds-checked spans (`std::span`) |

---

## 2. Core Philosophy / Golden Rule

> **Embrace Resource Acquisition Is Initialization (RAII); Treat Unchecked Raw Pointers as Liabilities, and Enforce Compile-Time Invariants Through Concepts and `constexpr`.**
> 
> *Modern C++ and C23 are fundamentally distinct from legacy 1990s C with classes. Memory safety, lifetime bounds, and exception safety are guaranteed when resource ownership is tied directly to object scope. Manual memory management (`free`/`delete`) produces double-frees, memory leaks, and use-after-free vulnerabilities. In modern systems programming, every resource—memory, file descriptors, mutexes, sockets—must be governed by RAII wrappers.*

---

## 3. Architecture & Memory Management

```
                               MODERN C++23 OBJECT LIFETIME & RAII
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              STACK ALLOCATION (Automatic Scope)                        │
│             `std::unique_ptr<T>`, `std::lock_guard<std::mutex>`, `std::span<T>`        │
│                                                                                        │
│   Construct Scope {                                                                    │
│       Resource Acquired (Socket / Memory / Mutex)                                      │
│       ... Business Execution ...                                                       │
│   } Destruct Scope (Guaranteed unwinding via RAII destructor, even on throw)           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Allocates / Owns
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              HEAP / FREE STORE (Controlled Ownership)                  │
│       • Single Ownership: `std::unique_ptr<T>` (Zero runtime overhead, move-only)      │
│       • Shared Ownership: `std::shared_ptr<T>` + `std::weak_ptr<T>` (Atomic refcount)  │
│       • Cache-Friendly Arrays: `std::vector<T>` with `reserve()`                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Concrete Code Examples

### 4.1 Modern C++23 Safe Ring Buffer with Concepts, Spans & Move Semantics

```cpp
/**
 * @file ring_buffer.hpp
 * @brief Production C++23 Thread-Safe Bounded Ring Buffer.
 * Demonstrates: Concepts (`std::movable`), `std::span` bounds safety,
 * `std::unique_lock`, `std::condition_variable`, and RAII invariants.
 */

#pragma once

#include <concepts>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <optional>
#include <span>
#include <stdexcept>

template <typename T>
concept BufferItem = std::movable<T> && (!std::is_reference_v<T>);

template <BufferItem T>
class BoundedRingBuffer {
public:
    explicit BoundedRingBuffer(size_t capacity)
        : m_capacity(capacity),
          m_head(0),
          m_tail(0),
          m_size(0),
          m_shutdown(false)
    {
        if (capacity == 0) {
            throw std::invalid_argument("Ring buffer capacity must be strictly greater than zero.");
        }
        m_storage.resize(capacity);
    }

    ~BoundedRingBuffer() {
        shutdown();
    }

    // Non-copyable, strictly movable
    BoundedRingBuffer(const BoundedRingBuffer&) = delete;
    BoundedRingBuffer& operator=(const BoundedRingBuffer&) = delete;
    BoundedRingBuffer(BoundedRingBuffer&&) noexcept = default;
    BoundedRingBuffer& operator=(BoundedRingBuffer&&) noexcept = default;

    /**
     * Pushes an item into the ring buffer. Blocks if buffer is full.
     * Returns false if buffer is shut down.
     */
    bool push(T item) {
        std::unique_lock<std::mutex> lock(m_mutex);
        m_not_full.wait(lock, [this]() {
            return m_size < m_capacity || m_shutdown;
        });

        if (m_shutdown) {
            return false;
        }

        m_storage[m_tail] = std::move(item);
        m_tail = (m_tail + 1) % m_capacity;
        ++m_size;

        lock.unlock();
        m_not_empty.notify_one();
        return true;
    }

    /**
     * Pops an item from the ring buffer. Blocks if buffer is empty.
     * Returns std::nullopt if buffer is shut down and empty.
     */
    std::optional<T> pop() {
        std::unique_lock<std::mutex> lock(m_mutex);
        m_not_empty.wait(lock, [this]() {
            return m_size > 0 || m_shutdown;
        });

        if (m_size == 0 && m_shutdown) {
            return std::nullopt;
        }

        T item = std::move(m_storage[m_head]);
        m_head = (m_head + 1) % m_capacity;
        --m_size;

        lock.unlock();
        m_not_full.notify_one();
        return item;
    }

    /**
     * Signals all waiting threads to wake up and terminate.
     */
    void shutdown() {
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            m_shutdown = true;
        }
        m_not_empty.notify_all();
        m_not_full.notify_all();
    }

    [[nodiscard]] size_t size() const noexcept {
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_size;
    }

    [[nodiscard]] bool empty() const noexcept {
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_size == 0;
    }

private:
    const size_t m_capacity;
    std::vector<T> m_storage;
    size_t m_head;
    size_t m_tail;
    size_t m_size;
    bool m_shutdown;
    mutable std::mutex m_mutex;
    std::condition_variable m_not_empty;
    std::condition_variable m_not_full;
};
```

---

### 4.2 Modern C23 Safe Memory Allocation with Static Analysis Attributes

```c
/**
 * @file safe_string_buffer.c
 * @brief Production ISO C23 Safe Resizable Byte Buffer.
 * Demonstrates: C23 `nullptr`, `bool`, `[[nodiscard]]`, bounds-checked copy,
 * and zeroed sanitization before free.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>

typedef struct {
    uint8_t *data;
    size_t size;
    size_t capacity;
} ByteBuffer;

[[nodiscard]]
ByteBuffer* byte_buffer_create(size_t initial_capacity)
{
    if (initial_capacity == 0) {
        initial_capacity = 64;
    }

    ByteBuffer *buf = (ByteBuffer *)malloc(sizeof(ByteBuffer));
    if (buf == nullptr) {
        return nullptr;
    }

    buf->data = (uint8_t *)malloc(initial_capacity);
    if (buf->data == nullptr) {
        free(buf);
        return nullptr;
    }

    buf->size = 0;
    buf->capacity = initial_capacity;
    return buf;
}

[[nodiscard]]
bool byte_buffer_append(ByteBuffer *buf, const uint8_t *src, size_t len)
{
    if (buf == nullptr || src == nullptr || len == 0) {
        return false;
    }

    // Check for integer overflow
    if (buf->size + len < buf->size) {
        return false;
    }

    if (buf->size + len > buf->capacity) {
        size_t new_cap = buf->capacity * 2;
        while (new_cap < buf->size + len) {
            new_cap *= 2;
        }

        uint8_t *new_data = (uint8_t *)realloc(buf->data, new_cap);
        if (new_data == nullptr) {
            return false;
        }
        buf->data = new_data;
        buf->capacity = new_cap;
    }

    memcpy(buf->data + buf->size, src, len);
    buf->size += len;
    return true;
}

void byte_buffer_destroy_secure(ByteBuffer **buf_ptr)
{
    if (buf_ptr == nullptr || *buf_ptr == nullptr) {
        return;
    }

    ByteBuffer *buf = *buf_ptr;
    if (buf->data != nullptr) {
        // Overwrite sensitive buffer with zeroes before deallocating
        memset(buf->data, 0, buf->capacity);
        free(buf->data);
        buf->data = nullptr;
    }

    free(buf);
    *buf_ptr = nullptr;
}
```

---

## 5. Security & Performance Considerations

### 5.1 Memory Sanitizers & Hardened Compilers
Always compile tests and debug builds with Sanitizer flags:
```bash
clang++ -std=c++23 -O2 -g -fsanitize=address,undefined,leak -fno-omit-frame-pointer main.cpp -o main
```
- **AddressSanitizer (ASan)**: Catches out-of-bounds access, use-after-free, double-free, and stack-use-after-return.
- **UndefinedBehaviorSanitizer (UBSan)**: Catches integer overflow, misaligned pointers, null-pointer dereference, and shift-out-of-bounds.
- **ThreadSanitizer (TSan)**: Detects data races between concurrent threads (`-fsanitize=thread`).

### 5.2 Zero-Cost Exception Safety
Adhere to the **Basic Guarantee** (no resource leaks, objects remain valid) and **Strong Guarantee** (commit or rollback, copy-and-swap idiom):
```cpp
// Strong Exception Guarantee via Copy-and-Swap
MyClass& operator=(MyClass other) noexcept {
    swap(*this, other);
    return *this;
}
```

---

## 6. Common Pitfalls & Anti-Patterns

### Anti-Pattern 1: Manual Memory Deallocation (`delete` / `free`)
- **Violation**: Manually allocating with `new T()` and calling `delete ptr` in business branches.
- **Consequence**: An unexpected exception or early return bypasses `delete`, causing heap leaks; double-frees cause remote code execution (RCE).
- **Remediation**: Use `std::make_unique<T>()` or `std::make_shared<T>()`.

### Anti-Pattern 2: Dangling References via String Views
- **Violation**: Returning a `std::string_view` referencing a temporary string created inside a function.
- **Consequence**: The temporary string is destructed at the statement end; the `string_view` holds a dangling pointer.
- **Remediation**: Return `std::string` by value when ownership must be transferred (leveraging Return Value Optimization / RVO).

---

## 7. Verification Checklist

| Criterion | Target Metric | Verification Command / Check |
|---|---|---|
| **1. Compiler Warnings** | Zero warnings with `-Wall -Wextra -Werror` | `clang++ -std=c++23 -Wall -Wextra -Werror -c src/*.cpp` exits code 0 |
| **2. ASan / UBSan Clean** | Zero memory errors | Run test executable compiled with `-fsanitize=address,undefined` |
| **3. Static Analysis** | Clean Clang-Tidy pass | `clang-tidy src/*.cpp -- -std=c++23` passes with 0 violations |
| **4. Valgrind Leak Check** | Definitively lost: 0 bytes | `valgrind --leak-check=full --error-exitcode=1 ./test_bin` |
| **5. RAII Verification** | Zero raw `new` / `delete` | `git grep -EIn "\b(new|delete)\b" src/` returns 0 hits in business code |

---

*See also*: [`sections/systems-kernel/linux-kernel-driver.md`](file:///home/agy/.t3/userdata/attachments/devskill/sections/systems-kernel/linux-kernel-driver.md) for kernel-space C programming, and [`languages/rust.md`](file:///home/agy/.t3/userdata/attachments/devskill/languages/rust.md) for memory-safe systems programming.
