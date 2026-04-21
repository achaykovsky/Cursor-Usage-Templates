---
name: create-flask-api
description: Scaffolds a Flask REST API project with recommended structure, app factory, blueprints, config, and dependencies. Use when the user asks to "create a Flask API," "scaffold Flask," "new Flask project," or "Flask project structure."
---

# Create Flask API

## Workflow

1. **Confirm scope** – Single module vs multi-resource API. Default: multi-resource with blueprints.
2. **Create directory structure** – Use the layout below.
3. **Add dependencies** – Flask, Flask-SQLAlchemy (if DB), marshmallow or Pydantic for validation.
4. **Implement app factory** – `create_app()` with config loading.
5. **Add initial routes** – Health check + at least one resource endpoint.

---

## Project Structure

```
project/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Config classes (Dev, Test, Prod)
│   ├── extensions.py        # Flask extensions (db, ma, etc.)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py   # Register blueprints
│   │   │   └── resources/   # Per-resource blueprints
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       └── items.py
│   ├── models/              # SQLAlchemy models (optional)
│   │   ├── __init__.py
│   │   └── item.py
│   └── schemas/             # Request/response schemas (optional)
│       ├── __init__.py
│       └── item.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (app, client)
│   └── api/
│       └── test_health.py
├── pyproject.toml           # or requirements.txt
├── .env.example
└── run.py                   # Entry point
```

---

## File Templates

### `app/__init__.py` (App factory)

```python
from flask import Flask

from app.config import config_by_name
from app.extensions import db  # optional
from app.api.v1 import register_blueprints


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    db.init_app(app)  # optional
    register_blueprints(app)
    return app
```

### `app/config.py`

```python
import os
from typing import Dict, Type

class BaseConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]  # required; no insecure default
    DEBUG = False
    TESTING = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class TestingConfig(BaseConfig):
    TESTING = True
    # Use in-memory SQLite for tests

class ProductionConfig(BaseConfig):
    pass

config_by_name: Dict[str, Type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
```

### `app/extensions.py`

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

### `app/api/v1/__init__.py` (Blueprint registration)

```python
from flask import Flask

from app.api.v1.resources.health import bp as health_bp

def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api/v1")
```

### `app/api/v1/resources/health.py`

```python
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200
```

### `run.py`

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### `tests/conftest.py`

```python
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app("testing")
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
```

---

## Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "flask>=3.0",
    "flask-sqlalchemy>=3.1",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-flask"]
```

---

## Conventions

- **Versioning**: Use `/api/v1/` prefix. Add new blueprints under `v1` or create `v2` when breaking.
- **Validation**: Use Pydantic or marshmallow at boundaries. Validation error status must follow the project's API contract; if unspecified, use framework default and document it explicitly.
- **Status codes**: 200/201 for success, contract-defined validation status, 404 not found, 500 server error. Never expose stack traces.
- **Secrets**: Load from env. Use `.env.example` with placeholders. No hardcoded keys.
- **Startup safety**: Fail startup if required secrets are missing.
- **Thin handlers**: Delegate business logic to services; keep route handlers as thin glue.

---

## Optional Additions

| Need | Add |
|------|-----|
| Auth | Flask-JWT-Extended or custom middleware |
| OpenAPI | flask-smorest or flasgger |
| Migrations | Flask-Migrate (Alembic) |
| CORS | flask-cors |
