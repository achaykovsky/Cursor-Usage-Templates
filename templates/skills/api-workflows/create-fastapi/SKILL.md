---
name: create-fastapi
description: Scaffolds a FastAPI REST API project with recommended structure, routers, config, and dependencies. Use when the user asks to "create a FastAPI," "scaffold FastAPI," "new FastAPI project," or "FastAPI project structure."
---

# Create FastAPI

## Workflow

1. **Confirm scope** – Single module vs multi-resource API. Default: multi-resource with routers.
2. **Create directory structure** – Use the standard layout in `reference.md`.
3. **Add dependencies** – FastAPI, uvicorn, SQLAlchemy (if DB), python-dotenv.
4. **Implement app** – `main.py` with lifespan, config, and router inclusion.
5. **Add initial routes** – Health check + at least one resource endpoint.
6. **Validate bootstrap** – Ensure app starts, OpenAPI loads, and a basic health test passes.

## Output Contract

- Project tree consistent with `reference.md`.
- Minimal runnable app (`app/main.py`, `run.py`, at least one health route).
- Dependency list pinned to current project conventions.
- One startup test path (health endpoint or smoke test).

## Conventions

- **Versioning**: Use `/api/v1/` prefix. Add new routers under `v1` or create `v2` when breaking.
- **Validation**: Pydantic models for request/response. Validation error status must follow the project's API contract; if unspecified, use framework default and document it explicitly.
- **Status codes**: 200/201 for success, contract-defined validation status, 400 bad request, 404 not found, 500 server error. Never expose stack traces.
- **Secrets**: Load via pydantic-settings from env. Use `.env.example` with placeholders. No hardcoded keys.
- **Thin handlers**: Delegate business logic to services; keep route handlers as thin glue.
- **Dependencies**: Use `Depends()` for shared logic (DB session, auth, pagination).

## Notes

- Keep this file concise; detailed tree, code templates, and optional add-ons live in `reference.md`.
- Only pull sections from `reference.md` that are needed for the user request.
