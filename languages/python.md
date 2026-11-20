# 🐍 Python Production Standard (`python.md`)

> **Standard**: Python 3.13 / 3.14+ (CPython internals, PEP 695 generics, PEP 649 deferred annotations, PEP 750 t-strings, PEP 779 supported free-threading)  
> **Tooling Stack**: `uv` (hermetic fast packaging & resolver), `ruff` (linter & formatter), `mypy --strict` / `pyright` / `ty`  
> **Classification**: Idiomatic Type-Safe Systems, Asynchronous Runtimes, & Enterprise Engineering  
> **Applicability**: Platform Engineers, Backend Core Architects, High-Throughput Service Developers  
> **Prerequisites**: Python Object Model, OS Threading Models, Event Loop Mechanics, Type Variance  

---

## 1. Title, Metadata & Scope

Python is one of the most widely adopted languages in contemporary computing, powering everything from high-throughput distributed microservices and asynchronous API gateways to machine learning pipelines and infrastructure automation. However, in enterprise environments, Python codebases frequently suffer from:
1. **Dynamic Type Drift & Latent Runtime TypeErrors**: Absence of strict static analysis leading to crashes in production execution branches.
2. **Event Loop Starvation & AsyncIO Anti-Patterns**: Blocking system calls, file system I/O, or CPU-bound tasks executed directly inside the cooperative asynchronous event loop.
3. **Global Interpreter Lock (GIL) Contention**: Naive multithreading for compute-heavy workloads, resulting in thread thrashing and negative scaling performance.
4. **Environment Drift & Unreproducible Packaging**: Conflicting dependency trees, slow virtualenv resolution, and inconsistent runtime interpreter baselines.
5. **Permissive Data Ingestion**: Lack of deep runtime boundary validation for incoming payloads and configurations.

This standard provides a rigorous, battle-tested engineering blueprint for building production-grade Python 3.12+ systems. It establishes strict guidelines across static typing (`mypy --strict`), ultra-fast linting and packaging (`uv`, `ruff`), robust runtime schema enforcement (`pydantic` v2), resilient concurrent execution (`asyncio`), and deterministic test scaffolding (`pytest` fixtures).

---

## 2. Core Philosophy & Golden Rules

> **"Type Statically at the Boundaries, Isolate the Event Loop from Blockers, Fail Early with Explicit Models, and Package Hermetically."**

Every Python service engineered under this standard must uphold five architectural imperatives:

1. **Strict Compile-Time Verification (`mypy --strict`)**: Python is dynamic at runtime, but code must be authored as if it were statically typed. Every function, method, parameter, and return value must carry explicit, unambiguous type annotations. The use of `Any` without an isolated `# type: ignore` accompanied by architectural justification is strictly prohibited.
2. **Immutable-First Domain Modeling**: Domain data structures must be immutable by default using frozen dataclasses (`@dataclass(frozen=True, slots=True)`) or Pydantic models (`frozen=True`). Mutable shared state is the leading cause of concurrency race conditions and side-effect leakage.
3. **Total Asynchronous Non-Blocking Discipline**: The `asyncio` event loop is single-threaded and cooperative. No synchronous file I/O, socket operations, or compute-heavy loops are permitted inside an `async def` context without offloading via `asyncio.to_thread` or dedicated multiprocessing executors.
4. **Hermetic, Lockfile-Pinned Tooling**: Dependency resolution must be reproducible to the single bit. Legacy `pip` and manual `requirements.txt` workflows without cryptographic hashes are replaced with `uv` workspace lockfiles (`uv.lock`).
5. **Zero Silent Exception Suppression**: Bare `except:` clauses or catching raw `Exception` without re-raising or wrapping into domain-specific hierarchies is categorized as a Critical Severity defect.

---

## 3. Architecture, Runtimes & Interpreter Internals

Understanding CPython internals is essential for building low-latency, memory-efficient services that operate predictably under load.

### 3.1 CPython Memory Model & GIL Internals

CPython manages memory using two core mechanisms:
1. **Reference Counting**: Every Python object (`PyObject`) maintains an internal counter (`ob_refcnt`). When this count drops to zero, the object's memory is deallocated immediately.
2. **Cyclic Garbage Collector (GC)**: A generational tri-color collector (Generations 0, 1, and 2) periodically runs to detect and collect isolated reference cycles (e.g., Object A references Object B, and Object B references Object A).

```
   ┌────────────────────────────────────────────────────────┐
   │                    CPython Process                     │
   │                                                        │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │             Global Interpreter Lock              │  │
   │  │  (Only 1 native thread executes bytecode at once)│  │
   │  └────────────────────────┬─────────────────────────┘  │
   │                           │                            │
   │         ┌─────────────────┴─────────────────┐          │
   │         ▼                                   ▼          │
   │  ┌───────────────┐                 ┌───────────────┐   │
   │  │   Thread 1    │                 │   Thread 2    │   │
   │  │ (I/O Bound)   │                 │  (CPU Bound)  │   │
   │  │ Releases GIL  │                 │ Holds GIL for │   │
   │  │ during socket │                 │ bytecode eval │   │
   │  │ read / select │                 │ loop counter  │   │
   │  └──────┬────────┘                 └───────────────┘   │
   │         │                                              │
   │         ▼ (OS Kernel wait)                             │
   │    Non-blocking                                        │
   │                                                        │
   └────────────────────────────────────────────────────────┘
```

#### The Global Interpreter Lock (GIL)
- In standard CPython (prior to PEP 703 free-threaded builds), the GIL is a mutual exclusion lock that prevents multiple native OS threads from executing Python bytecodes concurrently.
- **I/O-Bound Tasks**: When a thread initiates network I/O, disk I/O, or enters a C extension (e.g., NumPy vectorized kernels, cryptographic hashing), it explicitly releases the GIL, allowing other threads to run.
- **CPU-Bound Tasks**: Multiple Python threads attempting to compute math or process strings fight for the single GIL, resulting in context-switch overhead (GIL thrashing via OS condition variables) and execution times worse than a single thread.
- **Python 3.13/3.14 Free-Threaded Mode (PEP 703 / PEP 779)**: Python 3.14 promotes the free-threaded build (`python3.14t`, GIL disabled via mimalloc and biased reference counting) from experimental to officially supported. Use `python3.14t` ONLY after verifying every native C/Rust extension in your lockfile declares `Py_MOD_GIL_NOT_USED` (otherwise importing an incompatible extension silently re-enables the GIL). For mixed native ecosystems, `concurrent.interpreters` (PEP 734 subinterpreters) or `ProcessPoolExecutor` remain reliable CPU-parallel primitives.

### 3.2 AsyncIO Architecture: Epoll Event Loops and Cooperative Scheduling

The Python asynchronous execution model is single-threaded and cooperative. The event loop monitors registered file descriptors (network sockets) using OS primitives: `epoll` on Linux, `kqueue` on macOS/BSD.

```
                   AsyncIO Cooperative Task Cycle
                   
   ┌────────────────────────────────────────────────────────┐
   │                   Event Loop Iteration                 │
   │                                                        │
   │  1. Check I/O Events (epoll_wait / kqueue)             │
   │  2. Wake ready Task Callbacks                          │
   │  3. Execute Task Bytecode up to the next `await`       │
   │                                                        │
   │       Task A                      Task B               │
   │    ┌──────────┐                ┌──────────┐            │
   │    │ RUNNING  │                │ READY    │            │
   │    │          │                │          │            │
   │    │ `await`  │ ── Yield ───►  │ RUNNING  │            │
   │    │ socket   │                │          │            │
   │    └────┬─────┘                └────┬─────┘            │
   │         │                           │                  │
   │         ▼                           ▼                  │
   │    Registers socket            Executes pure           │
   │    with epoll                  non-blocking logic      │
   │                                                        │
   └────────────────────────────────────────────────────────┘
```

#### Event Loop Poisoning
If any coroutine executes a synchronous blocking call (such as `time.sleep()`, `requests.get()`, or `open().read()`), the entire event loop ceases execution. No other connections are accepted, health checks fail, timeouts cascade, and latency spikes across the entire service instance.

---

## 4. Concrete Production Code & Patterns

### 4.1 Strict Typing with Modern Python 3.12+ Syntax (PEP 695)

Python 3.12 introduces native generic type parameters via the `type` statement and generic syntax, eliminating verbose `TypeVar` declarations.

```python
# domain/entities.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Generic, NewType, Protocol, Self, TypeVar, override
import uuid

# Domain-specific NewTypes prevent primitive obsession
UserId = NewType("UserId", uuid.UUID)
OrderId = NewType("OrderId", uuid.UUID)


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True, kw_only=True)
class Money:
    """Immutable Value Object enforcing 2-decimal financial precision."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < Decimal("0.00"):
            raise ValueError(f"Monetary amount cannot be negative: {self.amount}")
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(f"Currency must be 3-letter ISO-4217 code: {self.currency}")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} != {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderLine:
    line_id: uuid.UUID = field(default_factory=uuid.uuid4)
    sku: str
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be strictly positive: {self.quantity}")


@dataclass(frozen=True, slots=True, kw_only=True)
class Order:
    order_id: OrderId
    user_id: UserId
    lines: tuple[OrderLine, ...]
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def total_amount(self) -> Money:
        if not self.lines:
            return Money(amount=Decimal("0.00"), currency="USD")
        currency = self.lines[0].unit_price.currency
        total = sum(
            (line.unit_price.amount * line.quantity for line in self.lines),
            start=Decimal("0.00"),
        )
        return Money(amount=total, currency=currency)

    def transition_to(self, new_status: OrderStatus) -> Self:
        """Returns a new immutable instance with mutated lifecycle state."""
        valid_transitions: dict[OrderStatus, set[OrderStatus]] = {
            OrderStatus.PENDING: {OrderStatus.SETTLED, OrderStatus.FAILED, OrderStatus.CANCELLED},
            OrderStatus.SETTLED: set(),
            OrderStatus.FAILED: set(),
            OrderStatus.CANCELLED: set(),
        }
        if new_status not in valid_transitions[self.status]:
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        
        # Replace creates an updated shallow copy with slots optimization
        from dataclasses import replace
        return replace(self, status=new_status)


# PEP 695 Type Alias with Type Parameter Syntax (Python 3.12+)
type Result[T, E: Exception] = tuple[T, None] | tuple[None, E]


# Protocol-based structural typing (eliminates tight inheritance coupling)
class OrderRepository(Protocol):
    async def get_by_id(self, order_id: OrderId) -> Order | None: ...
    async def save(self, order: Order) -> None: ...
    async def stream_pending(self, batch_size: int) -> AsyncIterator[Order]: ...
```

---

### 4.2 Runtime Data Validation with Pydantic v2

Pydantic v2 is rebuilt in Rust (`pydantic-core`), providing 10x–50x throughput improvements over v1. Always use modern v2 APIs: `field_validator`, `model_validator`, `ConfigDict`, and `TypeAdapter`.

```python
# schemas/order.py
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class BaseSchema(BaseModel):
    """Base schema enforcing immutability and strict configuration across all models."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        populate_by_name=True,
        arbitrary_types_allowed=False,
    )


class CreateOrderLineRequest(BaseSchema):
    sku: Annotated[str, Field(min_length=3, max_length=64, pattern=r"^[A-Z0-9_\-]+$")]
    quantity: Annotated[int, Field(gt=0, le=10_000, description="Items ordered")]
    unit_price: Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)]
    currency: Annotated[str, Field(min_length=3, max_length=3, default="USD")]

    @field_validator("currency")
    @classmethod
    def validate_currency_uppercase(cls, v: str) -> str:
        upper = v.upper()
        if upper not in {"USD", "EUR", "GBP", "JPY", "CAD"}:
            raise ValueError(f"Unsupported trading currency: {upper}")
        return upper


class CreateOrderRequest(BaseSchema):
    client_mutation_id: Annotated[uuid.UUID, Field(description="Idempotency key from client")]
    customer_email: EmailStr
    items: Annotated[list[CreateOrderLineRequest], Field(min_length=1, max_length=100)]
    max_total_budget: Annotated[Decimal | None, Field(default=None, gt=Decimal("0.00"))]

    @model_validator(mode="after")
    def verify_total_against_budget(self) -> Self:
        calculated_total = sum(item.unit_price * item.quantity for item in self.items)
        if self.max_total_budget is not None and calculated_total > self.max_total_budget:
            raise ValueError(
                f"Calculated total {calculated_total} exceeds maximum total budget {self.max_total_budget}"
            )
        return self


class OrderResponse(BaseSchema):
    order_id: uuid.UUID
    customer_email: EmailStr
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime
```

---

### 4.3 AsyncIO Event Loop, Structured Concurrency & Worker Supervision

Python 3.11+ introduces `asyncio.TaskGroup`, implementing structured concurrency. If one task fails, all concurrent tasks in the group are automatically cancelled, preventing dangling orphan tasks and resource leaks.

```python
# services/payment_orchestrator.py
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from contextlib import asynccontextmanager
import logging
from typing import Any, Final
import uuid

logger = logging.getLogger(__name__)

MAX_CONCURRENT_NETWORK_CALLS: Final[int] = 50
NETWORK_SEMAPHORE: Final[asyncio.Semaphore] = asyncio.Semaphore(MAX_CONCURRENT_NETWORK_CALLS)


class NetworkGatewayError(Exception):
    """Raised when an external payment gateway encounters a transport or protocol failure."""


class PaymentService:
    def __init__(self, gateway_url: str, request_timeout: float = 5.0) -> None:
        self._gateway_url = gateway_url
        self._request_timeout = request_timeout

    async def charge_single(self, account_id: uuid.UUID, amount_cents: int) -> dict[str, Any]:
        """Executes a bounded, non-blocking HTTP post with semaphore rate-limiting."""
        async with NETWORK_SEMAPHORE:
            # Emulating non-blocking async network I/O
            try:
                async with asyncio.timeout(self._request_timeout):
                    logger.info("Executing gateway charge for %s", account_id)
                    await asyncio.sleep(0.05)  # Cooperative yield
                    return {
                        "status": "APPROVED",
                        "auth_code": uuid.uuid4().hex[:8].upper(),
                        "account_id": str(account_id),
                        "amount_cents": amount_cents,
                    }
            except TimeoutError as err:
                logger.error("Gateway request timed out for account %s", account_id)
                raise NetworkGatewayError(f"Gateway timeout after {self._request_timeout}s") from err
            except Exception as exc:
                logger.exception("Unexpected gateway error during charge")
                raise NetworkGatewayError(f"Failed to communicate with gateway: {exc}") from exc

    async def execute_batch_charges(
        self, charges: list[tuple[uuid.UUID, int]]
    ) -> list[dict[str, Any]]:
        """Structured concurrency batch processing using Python 3.11+ TaskGroup.
        
        Guarantees that unhandled exceptions abort all sibling tasks cleanly.
        """
        results: list[dict[str, Any]] = []

        async def _worker(acc_id: uuid.UUID, amount: int) -> None:
            res = await self.charge_single(acc_id, amount)
            results.append(res)

        try:
            async with asyncio.TaskGroup() as tg:
                for acc_id, amount in charges:
                    tg.create_task(_worker(acc_id, amount))
        except* NetworkGatewayError as eg:
            # Python 3.11+ ExceptionGroup handling
            logger.error("Batch processing failed due to %d gateway errors", len(eg.exceptions))
            for sub_exc in eg.exceptions:
                logger.error("Sub-exception detail: %s", sub_exc)
            raise

        return results


# Graceful Event Loop Signal Handling and Worker Lifecycle
class AsyncDaemonWorker:
    def __init__(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._active_tasks: set[asyncio.Task[None]] = set()

    async def start(self) -> None:
        logger.info("Starting AsyncDaemonWorker...")
        supervisor = asyncio.create_task(self._supervise_loop(), name="worker-supervisor")
        self._active_tasks.add(supervisor)
        supervisor.add_done_callback(self._active_tasks.discard)

    async def _supervise_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                # Wait for work or shutdown signal
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=1.0)
            except TimeoutError:
                # Heartbeat processing
                await self._process_tick()

    async def _process_tick(self) -> None:
        # Non-blocking tick operation
        pass

    async def stop(self) -> None:
        logger.info("Initiating graceful shutdown of AsyncDaemonWorker...")
        self._shutdown_event.set()
        
        # Wait for all background tasks to complete within grace period
        if self._active_tasks:
            logger.info("Awaiting %d active tasks to drain...", len(self._active_tasks))
            done, pending = await asyncio.wait(self._active_tasks, timeout=5.0)
            for t in pending:
                logger.warning("Cancelling uncompleted task: %s", t.get_name())
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        logger.info("AsyncDaemonWorker stopped cleanly.")
```

---

### 4.4 Enterprise Packaging, Dependency Management & Linting

Modern Python eliminates slow setup tools and fragmented configs in favor of `pyproject.toml` standardized under PEP 517, PEP 518, and PEP 621.

#### `pyproject.toml` Production Configuration

```toml
[build-system]
requires = ["hatchling>=1.25.0"]
build-backend = "hatchling.build"

[project]
name = "enterprise-service"
version = "1.0.0"
description = "Industrial-grade high-throughput backend service"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "Apache-2.0" }
authors = [
    { name = "Core Platform Engineering", email = "platform-core@enterprise.internal" }
]
dependencies = [
    "pydantic>=2.9.2",
    "pydantic-settings>=2.5.2",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.31.0",
    "httpx>=0.27.2",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
    "mypy>=1.11.2",
    "ruff>=0.6.9",
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "pytest-mock>=3.14.0",
]

[tool.uv]
managed = true
dev-dependencies = [
    "types-requests>=2.32.0.20240914",
    "types-ujson>=5.10.0.20240515",
]

# ------------------------------------------------------------------------------
# Ruff Configuration (Fastest Linting & Formatting)
# ------------------------------------------------------------------------------
[tool.ruff]
target-version = "py312"
line-length = 100
exclude = [
    ".git",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "__pypackages__",
    "dist",
    "build",
]

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort (import organization)
    "B",     # flake8-bugbear (common bug prevention)
    "C4",    # flake8-comprehensions
    "UP",    # pyupgrade (modernize syntax to 3.12)
    "ARG",   # flake8-unused-arguments
    "SIM",   # flake8-simplify
    "TCH",   # flake8-type-checking (clean type import separation)
    "PTH",   # flake8-use-pathlib
    "ERA",   # eradicate (commented-out code detection)
    "PL",    # Pylint rules
    "TRY",   # tryceratops (exception handling best practices)
    "RUF",   # Ruff-specific rules
]
ignore = [
    "PLR0913", # Too many arguments in function definition (handled by domain design)
    "TRY003",  # Avoid specifying long messages outside the exception class
]

[tool.ruff.lint.isort]
combine-as-imports = true
force-sort-within-sections = true
known-first-party = ["enterprise_service"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "lf"

# ------------------------------------------------------------------------------
# Mypy Strict Mode Configuration
# ------------------------------------------------------------------------------
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
disallow_untyped_defs = true
disallow_untyped_calls = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
strict_optional = true
show_error_codes = true
show_column_numbers = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false

# ------------------------------------------------------------------------------
# Pytest Configuration
# ------------------------------------------------------------------------------
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=enterprise_service",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=xml:coverage.xml",
    "--cov-fail-under=90",
]
markers = [
    "integration: marks tests as integration tests against real databases or external services",
    "unit: fast in-memory unit tests",
]
```

---

### 4.5 Production Testing: Pytest Fixtures, Mocking & Async Scaffolding

Testing concurrent asynchronous Python code requires rigorous lifecycle management, isolated event loops, and strict fixture scoping.

```python
# tests/conftest.py
from collections.abc import AsyncGenerator, Generator
from decimal import Decimal
from typing import Any
import uuid

import pytest
import pytest_asyncio

from domain.entities import Money, Order, OrderId, OrderLine, OrderStatus, UserId
from services.payment_orchestrator import PaymentService


@pytest.fixture(scope="session")
def test_user_id() -> UserId:
    """Session-scoped immutable mock identity."""
    return UserId(uuid.UUID("11111111-1111-4111-8111-111111111111"))


@pytest.fixture
def sample_money() -> Money:
    return Money(amount=Decimal("199.99"), currency="USD")


@pytest.fixture
def mock_order(test_user_id: UserId, sample_money: Money) -> Order:
    return Order(
        order_id=OrderId(uuid.uuid4()),
        user_id=test_user_id,
        lines=(
            OrderLine(
                sku="PROD-SERVER-01",
                quantity=2,
                unit_price=sample_money,
            ),
        ),
        status=OrderStatus.PENDING,
    )


@pytest_asyncio.fixture(scope="function")
async def payment_service() -> AsyncGenerator[PaymentService, None]:
    """Provides a fresh PaymentService per test with clean resource teardown."""
    service = PaymentService(gateway_url="https://mock-gateway.internal", request_timeout=2.0)
    yield service
    # Teardown logic runs after test completes
    logger.debug("Tearing down mock payment service")
```

```python
# tests/test_payment_orchestrator.py
from decimal import Decimal
import uuid

import pytest
import pytest_mock

from domain.entities import Order, OrderStatus
from services.payment_orchestrator import NetworkGatewayError, PaymentService


@pytest.mark.unit
async def test_order_total_calculation(mock_order: Order) -> None:
    # 2 items @ 199.99 = 399.98
    total = mock_order.total_amount
    assert total.amount == Decimal("399.98")
    assert total.currency == "USD"


@pytest.mark.unit
async def test_order_status_valid_transition(mock_order: Order) -> None:
    settled = mock_order.transition_to(OrderStatus.SETTLED)
    assert settled.status == OrderStatus.SETTLED
    assert mock_order.status == OrderStatus.PENDING  # Immutability preserved


@pytest.mark.unit
async def test_order_status_invalid_transition(mock_order: Order) -> None:
    settled = mock_order.transition_to(OrderStatus.SETTLED)
    with pytest.raises(ValueError, match="Invalid transition from SETTLED to CANCELLED"):
        settled.transition_to(OrderStatus.CANCELLED)


@pytest.mark.unit
async def test_batch_charge_execution_success(payment_service: PaymentService) -> None:
    account_ids = [(uuid.uuid4(), 1000), (uuid.uuid4(), 2500)]
    results = await payment_service.execute_batch_charges(account_ids)
    
    assert len(results) == 2
    for r in results:
        assert r["status"] == "APPROVED"
        assert "auth_code" in r


@pytest.mark.unit
async def test_batch_charge_propagates_gateway_error(
    payment_service: PaymentService, mocker: pytest_mock.MockerFixture
) -> None:
    # Force single charge to fail
    mocker.patch.object(
        payment_service,
        "charge_single",
        side_effect=NetworkGatewayError("Gateway transport disconnected"),
    )

    with pytest.raises(ExceptionGroup) as exc_info:
        await payment_service.execute_batch_charges([(uuid.uuid4(), 500)])

    assert exc_info.group_contains(NetworkGatewayError)
```

---

## 5. Security & Performance Considerations

### 5.1 Security Standards: AST Sanitization, Timing Attacks & Secret Handling

1. **Timing Attack Elimination**: When validating API keys, cryptographic tokens, or password signatures, never use the equality operator `==`. Use `secrets.compare_digest()` to ensure constant-time comparison, mitigating timing side-channel attacks.
   ```python
   import secrets

   def verify_api_token(supplied_token: str, expected_token: str) -> bool:
       return secrets.compare_digest(supplied_token.encode("utf-8"), expected_token.encode("utf-8"))
   ```
2. **Safe Deserialization**:
   - Never use `pickle.loads()` on untrusted streams; `pickle` allows arbitrary remote code execution (RCE) via `__reduce__` exploit payloads.
   - For structured deserialization, use `pydantic.TypeAdapter.validate_json()` or standard `json.loads()`.
   - Never use `yaml.load()` without `Loader=yaml.CSafeLoader` or `yaml.safe_load()`.
3. **Subprocess Execution Guardrails**:
   - Prohibit `shell=True` in `subprocess.run()` or `asyncio.create_subprocess_shell()`.
   - Pass arguments strictly as structured lists to prevent command injection:
   ```python
   # ✅ GOOD
   import subprocess
   result = subprocess.run(["git", "rev-parse", "--verify", ref_name], capture_output=True, check=True)

   # ❌ CRITICAL VULNERABILITY: Command Injection
   # subprocess.run(f"git rev-parse --verify {ref_name}", shell=True)
   ```

### 5.2 Performance Tuning & Memory Optimization

1. **`__slots__` for High-Volume Objects**:
   Standard Python classes allocate an internal dynamic dictionary (`__dict__`) per instance to store attributes, consuming ~150 bytes minimum per instance. By using `__slots__` (or `@dataclass(slots=True)`), memory is allocated as a compact fixed-size array in C, cutting heap consumption by up to 60% and speeding up attribute lookup times.
2. **Offloading CPU-Bound Hotspots with ProcessPoolExecutor**:
   ```python
   import asyncio
   from concurrent.futures import ProcessPoolExecutor
   import os

   _CPU_POOL: ProcessPoolExecutor | None = None

   def _init_pool() -> ProcessPoolExecutor:
       global _CPU_POOL
       if _CPU_POOL is None:
           _CPU_POOL = ProcessPoolExecutor(max_workers=os.cpu_count())
       return _CPU_POOL

   def cpu_intensive_hashing(payload: bytes) -> bytes:
       import hashlib
       result = payload
       for _ in range(500_000):
           result = hashlib.sha256(result).digest()
       return result

   async def run_cpu_workload(payload: bytes) -> bytes:
       loop = asyncio.get_running_loop()
       pool = _init_pool()
       # Delegates work to an isolated OS process; the asyncio event loop remains fully responsive
       return await loop.run_in_executor(pool, cpu_intensive_hashing, payload)
   ```

---

## 6. Common Pitfalls & Anti-Patterns

### 6.1 Mutable Default Arguments
```python
# ❌ BAD: Default list is evaluated ONCE at function definition time.
# Subsequent calls share and mutate the same list instance across callers!
def append_item(item: str, registry: list[str] = []) -> list[str]:
    registry.append(item)
    return registry

# ✅ GOOD: Default parameter is None, fresh container allocated in function frame
def append_item(item: str, registry: list[str] | None = None) -> list[str]:
    target = list(registry) if registry is not None else []
    target.append(item)
    return target
```

### 6.2 The Naked `except Exception:` Anti-Pattern
```python
# ❌ BAD: Catches cancellation signals, system exits, and masks fatal logic bugs
try:
    await process_transaction()
except Exception:
    pass  # Silently dropped

# ✅ GOOD: Specific exception catching with explicit context chaining
try:
    await process_transaction()
except DatabaseConnectionError as err:
    logger.error("Transaction failed due to network partition: %s", err)
    raise ServiceUnavailableError("Payment ledger temporarily unreachable") from err
```

### 6.3 Blocking the Cooperative AsyncIO Event Loop
```python
# ❌ BAD: Synchronous time.sleep freezes ALL event loop coroutines for 5 seconds
async def poll_status():
    import time
    time.sleep(5)

# ✅ GOOD: Cooperative sleep yields control back to event loop selector
async def poll_status():
    await asyncio.sleep(5)
```

### 6.4 Unbounded `asyncio.gather()` Memory Explosion
```python
# ❌ BAD: Spawning 100,000 tasks concurrently exhausts network sockets and triggers OOM
async def sync_all(urls: list[str]):
    return await asyncio.gather(*(fetch(u) for u in urls))

# ✅ GOOD: Bounded concurrency using asyncio.Semaphore or chunked queue workers
async def sync_bounded(urls: list[str], concurrency_limit: int = 50):
    sem = asyncio.Semaphore(concurrency_limit)
    async def _safe_fetch(u: str):
        async with sem:
            return await fetch(u)
    return await asyncio.gather(*(_safe_fetch(u) for u in urls))
```

---

## 7. Python 3.13 / 3.14 Production Features (2026 Baseline)

1. **Template Strings (`t`-strings, PEP 750 in Python 3.14)**: Unlike `f`-strings (which eagerly evaluate to raw `str` and cause SQL/HTML/shell injection if misused), `t`-strings evaluate to a structured `string.templatelib.Template` separating static literal segments from interpolated `Interpolation` values. Use `t`-strings with typed sanitizers for HTML rendering, structured logging, and safe query builders—never interpolate untrusted user input into `f`-strings (`R-061`, `R-069`).
2. **Deferred Annotation Evaluation by Default (PEP 649 / PEP 749 in Python 3.14)**: Annotations are evaluated lazily via `__annotate__` functions and inspected safely via `annotationlib.get_annotations()`, eliminating forward-reference string quoting hacks and cyclic import traps without legacy `from __future__ import annotations` pitfalls (keep `from __future__ import annotations` only when supporting Python 3.10–3.13 runtimes).
3. **Supported Free-Threading (`python3.14t`) & Subinterpreters (PEP 734)**:
   - Audit thread-safety before adopting `python3.14t`: prefer immutable dataclasses, explicit `threading.Lock` / `queue.Queue`, and verify `sys._is_gil_enabled() is False` in startup self-checks when free-threading is required.
   - Use `concurrent.interpreters` when isolated per-worker state with lower memory overhead than OS processes is desired.
4. **Hermetic `uv` + `ruff` Toolchain**: Run all CI jobs with `uv sync --frozen --no-dev` (or `--locked` for tests), `ruff check .`, `ruff format --check .`, and strict static type checking (`mypy --strict` or `pyright`).

---

## 8. Verification Checklist

Before shipping Python code to production, execute this automated verification sequence:

- [ ] **Static Type Analysis**: `mypy --strict .` (or `pyright`) passes with 0 errors across all production modules.
- [ ] **Linter & Formatting Conformity**: `ruff check .` and `ruff format --check .` return cleanly with zero deprecation warnings.
- [ ] **Test Coverage Baseline**: `pytest` executes with `--cov-fail-under=90`, all unit and integration tests green.
- [ ] **Event Loop Hygiene**: No synchronous file I/O (`open()`), network calls (`requests.*`), or `time.sleep()` in any `async def` function.
- [ ] **Data Model Validation**: All external payloads (HTTP requests, message broker events) are parsed through Pydantic v2 schemas configured with `extra="forbid"`.
- [ ] **Constant-Time Crypto**: All token and secret verifications utilize `secrets.compare_digest()`.
- [ ] **Subprocess Safety**: No `shell=True` invocations; arguments passed as structured sequence arrays.
- [ ] **Hermetic Dependency Pinning**: `uv.lock` is up-to-date and checked into Git; no unpinned runtime dependencies.
