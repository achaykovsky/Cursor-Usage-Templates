---
name: handle-breaking-change
description: Identifies callers or consumers of a changed interface; proposes a compatibility path (deprecation, adapter, versioning) and updates or documents callers. Use when the user says "this is a breaking change," "we're changing the API," or removes/changes a public contract.
---

# Handle Breaking Change

## Workflow

1. **Define the change**
   - What interface is changing? (API contract, function signature, config key, file format, or behavior.) What is being removed or changed?
   - List the old and new contract (e.g. old vs new request/response, or old vs new config shape).

2. **Find consumers**
   - Search the repo and, if relevant, docs or other repos for call sites, imports, or references to the old interface. List internal and external consumers.
   - For each consumer: what must change for the new contract? (e.g. new parameter, different response field.)

3. **Propose compatibility path**
   - **Deprecation:** Keep old behavior behind a flag or for N releases; log deprecation warning; document removal date. Update callers to use new interface before removal.
   - **Adapter:** Provide a thin layer that accepts old input and calls new implementation, or translates new output to old shape. Use when callers cannot change quickly.
   - **Versioning:** Expose both old and new (e.g. v1 and v2 endpoints). Route existing callers to v1 until they migrate; new usage uses v2.
   - Choose based on project norms and how many consumers can be updated.

4. **Update or document callers**
   - For each internal caller: update to the new interface (or to the adapter). Add tests. For external consumers: document the change and migration steps (e.g. changelog, migration guide).
   - If removing the old path: remove code and any deprecation shims only after callers are updated and the user confirms.

## Notes

- Do not remove or break existing callers without a clear path and user agreement. Prefer deprecation over hard break when possible.
- Summarize who is affected and what they need to do (one-line per consumer type if many).
