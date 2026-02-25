---
name: design-feature-from-requirements
description: Turns user stories or requirements into a concrete design: components, data flow, interfaces, and optional implementation order or stubs; aligns with existing patterns. Use when the user says "design this feature," "how should I implement X," or provides a spec or ticket.
---

# Design Feature from Requirements

## Workflow

1. **Clarify requirements**
   - Extract acceptance criteria, inputs, outputs, and constraints from the user story, ticket, or spec.
   - Identify unknowns or ambiguities; ask or state assumptions.

2. **Map to existing system**
   - Locate where the feature fits: which layer, module, or service. Note existing patterns (naming, structure, APIs) to follow.
   - Identify touchpoints: existing APIs, DB, config, or external systems.

3. **Produce design**
   - **Components:** New or modified modules, classes, or functions; responsibilities and boundaries.
   - **Data flow:** Inputs, transformations, persistence, and outputs. Data shapes or key types.
   - **Interfaces:** Public APIs, events, or contracts (signatures, payloads, status codes).
   - **Order:** Suggested implementation order or phases (e.g. contract first, then implementation, then integration).

4. **Optional: stubs or scaffolding**
   - If useful, propose stub implementations or file layout so the user can implement incrementally. Keep stubs consistent with project style.

## Notes

- Prefer minimal design that meets the requirements; avoid over-engineering.
- Call out dependencies on other work or follow-up tasks (e.g. "after auth service exposes X").
