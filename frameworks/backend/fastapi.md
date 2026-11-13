# ⚡ FastAPI Production Guide (`fastapi.md`)

> **Framework**: FastAPI (Python 3.11 / 3.12+)  
> **Classification**: High-Performance Asynchronous Python Backend  
> **Core Philosophy**: "Strict Type Hints, Schema-Driven Validation, Explicit Dependency Injection."

---

## 1. Asynchronous Execution Rules (`async def` vs `def`)

FastAPI handles concurrency differently based on how route functions are defined:

```python
# 1. Non-blocking Async I/O (Async DB driver, httpx async client)
# MUST use 'async def' to run in the event loop without thread overhead
@router.get("/users/{user_id}")
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# 2. Blocking / CPU-bound / Synchronous I/O (Pillow image processing, sync requests)
# MUST use standard 'def' so FastAPI automatically offloads it to the external thread pool
@router.post("/process-image")
def process_image(file: UploadFile):
    # Runs in threadpool; does not block the main asyncio event loop
    image = Image.open(file.file)
    image.thumbnail((200, 200))
    return {"status": "processed"}
```

> **Warning**: Calling synchronous blocking libraries (like `requests.get` or `time.sleep`) inside an `async def` function will freeze the entire event loop for all concurrent users!

---

## 2. Pydantic v2 Validation Schemas

Always separate Request schemas from Response schemas:

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field
import uuid
from datetime import datetime

# Base shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)

# Request DTO (incoming)
class UserCreate(UserBase):
    password: str = Field(min_length=10, max_length=128)

# Response DTO (outgoing, safe projection)
class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    # Enable reading from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)
```

---

## 3. Database Dependency Injection (SQLAlchemy 2.0 Async)

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator

engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/production_db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Test connection viability before handing out
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## 4. Lifespan Events & Production Uvicorn Settings

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connection pools, caches, warm up models
    yield
    # Shutdown: Close database pools, flush telemetry, stop workers
    await engine.dispose()

app = FastAPI(title="Core Production API", lifespan=lifespan)
```

### Production Deployment Command
```bash
# Run with Uvicorn worker class behind Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
```
