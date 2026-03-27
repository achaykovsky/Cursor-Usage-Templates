---
name: manage-request-response-schema-changes
description: Plans safe evolution of request/response JSON and form schemas (required fields, nullability, enums, versioning). Use when changing DTOs, Pydantic models, OpenAPI schemas, or "we need to add/change a field on the API."
---

# Manage Request/Response Schema Changes

## Workflow

1. **Inventory the surface**
   - List affected operations (routes + methods). For each: request body, query, path params, headers; response bodies per status code; error payload shapes.
   - Note whether schemas are **shared** (`components/schemas`, shared DTOs)—one edit may affect many operations.

2. **Prefer additive evolution first**
   - **New fields:** add as **optional** with documented default or null semantics; avoid new required fields on existing bodies without a version bump.
   - **Deprecate before remove:** mark in spec (`deprecated: true`) and docs; keep field present for agreed period; log or metric usage if possible.
   - **Enums:** prefer **open extensibility**—clients handle unknown values; document that new values may appear. Shrinking enums is breaking.

3. **Nullability and types**
   - Changing `string` → `string | null` or adding required fields often breaks generated clients and strict validators—treat as breaking unless all consumers are updated.
   - Integer ↔ string ID changes: breaking for typed clients.

4. **Parallel shapes (when additive is not enough)**
   - Introduce **v2** schema or **nested** object for the new shape; keep v1 stable until retirement (see **api-versioning-guidance**).
   - **Compatibility layers:** optional query `?format=legacy` or dual write only with explicit product agreement—avoid silent dual meaning.

5. **Align implementation and spec**
   - Update validation (Pydantic/Zod/OpenAPI) and **regenerate or hand-edit** spec so **validate-api-contract** stays true.

6. **Verify**
   - Contract tests or snapshot tests for golden requests/responses; **review-openapi-diff** against previous release.

## Notes

- **Error bodies** are part of the contract; changing error codes or JSON error shape affects retries and client branching—classify like response schema changes.
- Cross-link **analyze-api-consumer-impact** before removing fields.
