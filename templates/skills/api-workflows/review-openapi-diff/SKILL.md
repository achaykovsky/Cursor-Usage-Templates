---
name: review-openapi-diff
description: Reviews a diff between two OpenAPI (or similar) specs; highlights breaking vs safe changes and review checklist items. Use when the user says "OpenAPI diff," "spec diff," "what changed in swagger," or compares two API description files.
---

# Review OpenAPI Diff

## Workflow

1. **Get two artifacts**
   - **Old:** prior commit, main branch file, or published `openapi.yaml`/`swagger.json`.
   - **New:** current branch or edited file. Same format (YAML vs JSON) is ideal; normalize if one side is generated.

2. **Run or simulate structured diff**
   - Prefer tooling when available: e.g. **oasdiff**, **openapi-diff**, or CI that fails on breaking changes—summarize tool output (breaking / non-breaking groups).
   - Without tools: diff paths, methods, `operationId`, parameters (name, in, required, schema), requestBody, responses per status code, `components/schemas`, security schemes, and global `servers` / base path.

3. **Review checklist**
   - **Paths/methods:** removed or renamed? HTTP method change?
   - **Parameters:** new required param? type/format change? `enum` shrunk?
   - **Bodies:** required properties added? properties removed? `additionalProperties` flipped from true to false?
   - **Responses:** status codes removed? response schema narrowed? `oneOf`/`discriminator` changes?
   - **Shared components:** breaking rename of `$ref` targets used widely?
   - **Defaults and examples:** docs-only vs behavioral if codegen or tests use examples.

4. **Report**
   - Table or bullet list: **change → classification (breaking / non-breaking / unclear) → consumer note**.
   - Point to **check-api-backward-compatibility** for semantics and **manage-request-response-schema-changes** for schema-level patterns.

## Notes

- Cosmetic reordering of keys or descriptions is usually non-functional; still mention if it obscures real diffs.
- If only one file exists, infer "old" from git history or ask for a baseline ref.
