---
name: create-flask-api
description: Scaffolds a Flask REST API project with recommended structure, app factory, blueprints, config, and dependencies. Use when the user asks to "create a Flask API," "scaffold Flask," "new Flask project," or "Flask project structure."
---

# Create Flask API

## Workflow

1. **Confirm scope** – Single module vs multi-resource API. Default: multi-resource with blueprints.
2. **Create directory structure** – Use the standard layout in `reference.md`.
3. **Add dependencies** – Flask, Flask-SQLAlchemy (if DB), marshmallow or Pydantic for validation.
4. **Implement app factory** – `create_app()` with config loading.
5. **Add initial routes** – Health check + at least one resource endpoint.
6. **Validate bootstrap** – Ensure app starts and a health route test passes.

## Output Contract

- Project tree consistent with `reference.md`.
- Minimal runnable app factory (`create_app`) and one health blueprint.
- Dependency list aligned with project/package manager conventions.
- One startup test path (health endpoint or smoke test).

## Conventions

- **Versioning**: Use `/api/v1/` prefix. Add new blueprints under `v1` or create `v2` when breaking.
- **Validation**: Use Pydantic or marshmallow at boundaries. Validation error status must follow the project's API contract; if unspecified, use framework default and document it explicitly.
- **Status codes**: 200/201 for success, contract-defined validation status, 404 not found, 500 server error. Never expose stack traces.
- **Secrets**: Load from env. Use `.env.example` with placeholders. No hardcoded keys.
- **Startup safety**: Fail startup if required secrets are missing.
- **Thin handlers**: Delegate business logic to services; keep route handlers as thin glue.

## Notes

- Keep this file concise; detailed tree, file templates, and add-on options live in `reference.md`.
- Only pull sections from `reference.md` needed for the active request.
