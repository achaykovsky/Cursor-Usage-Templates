---
name: implement-or-extend-api-surface
description: From spec, OpenAPI, or contract: implements or extends endpoints, request/response types, validation, and status codes; aligns with existing patterns. Use when the user adds an API spec, describes a new endpoint, or says "implement this API."
---

# Implement or Extend API Surface

## Workflow

1. **Gather contract**
   - Obtain the spec (OpenAPI, prose, or existing routes). Identify method, path, request body/query/headers, response shape, and status codes.
   - Locate existing API layer in the repo (routers, handlers, controllers) and match naming and structure.

2. **Implement or extend**
   - Add or update the route/handler. Implement request parsing, validation (against types or schema), and response serialization.
   - Use existing patterns: error handling, auth middleware, and status codes (e.g. 400 for validation, 404 for not found, 500 for server error). Do not expose internal errors or stack traces in responses. For logs and docs, apply **redact-sensitive-in-output** (shared-practices).

3. **Align with project**
   - Follow existing conventions: URL style, versioning, and DTOs or response types. Add or update types/interfaces so the API is consistent.
   - If the project has contract tests or OpenAPI generation, ensure the implementation matches (or update the spec if the code is the source of truth).

4. **Verify**
   - Suggest a quick manual check (e.g. curl or test request) or add/run an existing test that hits the new or changed endpoint. Ensure success and error paths are covered.

## Notes

- Prefer validation at the boundary (e.g. Pydantic, Zod). Fail fast with clear error messages.
- Keep handlers thin; delegate business logic to services or domain layer if the project does so.
