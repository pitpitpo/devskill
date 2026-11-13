# 🐍 Python Production Standard (`python.md`)

> **Language**: Python 3.11 / 3.12+  
> **Tooling**: `uv` / `poetry`, `ruff`, `mypy --strict`  
> **Core Philosophy**: "Strict Type Annotations, Hermetic Environments, Fast Tooling, Async Safety."

---

## 1. Type Hinting & Dataclasses

Always annotate function signatures, parameters, and return types completely:

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
import uuid

@dataclass(frozen=True, slots=True)
class CustomerAccount:
    account_id: uuid.UUID
    email: str
    balance_cents: int
    created_at: datetime = field(default_factory=datetime.utcnow)

    def deposit(self, amount_cents: int) -> Self:
        if amount_cents <= 0:
            raise ValueError("Deposit amount must be positive")
        return CustomerAccount(
            account_id=self.account_id,
            email=self.email,
            balance_cents=self.balance_cents + amount_cents,
            created_at=self.created_at,
        )
```

---

## 2. Ultra-Fast Linting & Formatting with Ruff (`pyproject.toml`)

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
    "TCH", # flake8-type-checking
]
ignore = []

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 3. Explicit Error Handling with Domain Exceptions

```python
class DomainError(Exception):
    """Base exception for all domain business errors."""
    pass

class InsufficientFundsError(DomainError):
    def __init__(self, account_id: uuid.UUID, required_cents: int, available_cents: int):
        self.account_id = account_id
        self.required_cents = required_cents
        self.available_cents = available_cents
        super().__init__(
            f"Account {account_id} has insufficient funds. Required: {required_cents}, Available: {available_cents}"
        )
```

---

## 4. Anti-Patterns to Eliminate

1. ❌ **Mutable Default Arguments**: Never use `def fn(items: list = []):`. Use `def fn(items: list[str] | None = None):`.
2. ❌ **Wildcard Imports**: Never use `from module import *`.
3. ❌ **Bare `except:`**: Always catch specific exceptions (`except (ValueError, KeyError) as e:`).
