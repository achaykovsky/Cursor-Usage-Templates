---
name: check-api-backward-compatibility
description: Evaluates whether an API change is backward compatible for existing clients; classifies additive vs breaking changes and suggests mitigations. Use when the user asks "is this breaking," "backward compatible," "safe for clients," or before shipping contract changes.
---

# Check API Backward Compatibility

## Workflow

1. **Establish baseline**
   - Identify the **previous** contract (committed OpenAPI, published SDK types, or last release tag). Identify the **proposed** contract (branch diff, PR, or described change).
   - Clarify **client assumptions**: strict parsers, generated clients, mobile apps that cache shapes, or unknown third parties (assume worst case).

2. **Classify changes**
   - **Usually compatible (when done carefully):** New optional request fields; new response fields (clients ignore unknown JSON keys); new enum values *only if* clients treat unknown values safely; new endpoints; new optional query parameters; widening string formats when validation relaxes; new success or documented error status codes that old clients do not rely on failing.
   - **Often breaking:** Removing or renaming fields; changing types; making optional fields required; narrowing formats; removing enum values; changing default behavior; new required query/header/body fields; changing URL path or HTTP method; splitting or merging resources; pagination cursor format changes.
   - **Gray areas:** Tightening validation (400 where 200 was possible), changing error body shape, ordering guarantees, precision of numbers, date/time formats—treat as breaking if any client could depend on old behavior.

3. **Verify with evidence**
   - Prefer **diff** of machine-readable specs (see **review-openapi-diff**). If only code changed, compare generated or hand-written schemas and route tables.
   - List each delta with a **compat verdict** (safe / risky / breaking) and **why**.

4. **Recommend**
   - If breaking: default path is **versioning** + migration window, or **deprecation** with overlap (see **api-versioning-guidance**, **handle-breaking-change**). If additive-only: still document new fields and optional semantics.

## Notes

- JSON: clients that fail on unknown properties are fragile; call that out if the codebase or partner contracts require "closed" schemas.
- Link to **analyze-api-consumer-impact** when blast radius is unknown.
