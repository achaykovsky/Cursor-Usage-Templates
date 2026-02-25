---
name: validate-api-contract
description: Compares implementation (routes, types, status codes) to contract or spec; reports drift and suggests fixes or spec updates. Use when the user mentions "contract," "spec," "OpenAPI," or "does this match the API."
---

# Validate API Contract

## Workflow

1. **Obtain contract and implementation**
   - Locate the spec (OpenAPI file, docs, or written contract). Note endpoints, methods, request/response shapes, and status codes.
   - Locate the implementation: route definitions, handlers, and response types. Map each spec endpoint to code.

2. **Compare and find drift**
   - For each endpoint: path and method match? Request body/query/headers match? Response shape and status codes match?
   - List discrepancies: missing or extra endpoints, wrong types, wrong status codes, or docs that describe something different from the code.

3. **Suggest fixes**
   - For each drift: propose either updating the code to match the spec or updating the spec to match the code. Prefer one source of truth (usually spec); note if the project treats code as source of truth and generates spec from it.
   - Suggest concrete edits: add missing field, change type, or fix status code. If the spec is generated from code, suggest code changes and regeneration.

4. **Summarize**
   - Short report: endpoints checked, number of drifts, and top fixes. If no drift, state that implementation matches contract.

## Notes

- Ignore cosmetic differences (e.g. field order in JSON) unless the project requires strict compatibility.
- If there is no written spec, infer contract from the implementation and suggest documenting it (e.g. OpenAPI) for future validation.
