---
name: create-fastapi
description: Scaffolds a FastAPI REST API project with recommended structure, routers, config, and dependencies. Use when the user asks to "create a FastAPI," "scaffold FastAPI," "new FastAPI project," or "FastAPI project structure."
---

# Create FastAPI

## Workflow

1. **Confirm scope** – Single module vs multi-resource API. Default: multi-resource with routers.
2. **Create directory structure** – Use the layout below.
3. **Add dependencies** – FastAPI, uvicorn, SQLAlchemy (if DB), python-dotenv.
4. **Implement app** – `main.py` with lifespan, config, and router inclusion.
5. **Add initial routes** – Health check + at least one resource endpoint.

---

## Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, router inclusion
│   ├── config.py            # Pydantic Settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # Shared dependencies (get_db, etc.)
│   │   └── v1/
│   │       ├── __init__.py  # Include routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py
│   │           └── items.py
│   ├── models/              # SQLAlchemy models (optional)
│   │   ├── __init__.py
│   │   └── item.py
│   └── schemas/             # Pydantic request/response models
│       ├── __init__.py
│       └── item.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (client)
│   └── api/
│       └── test_health.py
├── pyproject.toml
├── .env.example
└── run.py                   # uvicorn entry point
```

---

## File Templates

### `app/main.py`

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB, caches, etc.
    yield
    # Shutdown: cleanup


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api/v1")
```

### `app/config.py`

```python
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PROJECT_NAME: str = "My API"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### `app/api/v1/__init__.py`

```python
from fastapi import APIRouter

from app.api.v1.endpoints import health, items

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
```

### `app/api/v1/endpoints/health.py`

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health():
    return {"status": "ok"}
```

### `app/api/v1/endpoints/items.py`

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_items():
    return []


@router.get("/{item_id}")
def get_item(item_id: int):
    return {"id": item_id, "name": "example"}
```

### `run.py`

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

### `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
```

---

## Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest", "httpx"]
```

---

## Conventions

- **Versioning**: Use `/api/v1/` prefix. Add new routers under `v1` or create `v2` when breaking.
- **Validation**: Pydantic models for request/response. FastAPI validates automatically; return 422 for validation errors.
- **Status codes**: 200/201 for success, 400 bad request, 404 not found, 422 validation error, 500 server error. Never expose stack traces.
- **Secrets**: Load via pydantic-settings from env. Use `.env.example` with placeholders. No hardcoded keys.
- **Thin handlers**: Delegate business logic to services; keep route handlers as thin glue.
- **Dependencies**: Use `Depends()` for shared logic (DB session, auth, pagination).

---

## Optional Additions

| Need | Add |
|------|-----|
| DB | SQLAlchemy 2.0 async, `app/api/deps.py` with `get_db` |
| Auth | python-jose, passlib, `Depends(get_current_user)` |
| Migrations | Alembic |
| CORS | `CORSMiddleware` in main.py |
| OpenAPI | Built-in; customize via FastAPI(openapi_*) |
