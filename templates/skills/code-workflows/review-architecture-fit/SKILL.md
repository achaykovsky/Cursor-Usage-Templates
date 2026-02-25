---
name: review-architecture-fit
description: Assesses a change or new module against existing architecture (layers, boundaries, dependencies); flags violations and suggests alignment or refactors. Use when the user asks "does this fit our architecture," "review this design," or before adding a new subsystem.
---

# Review Architecture Fit

## Workflow

1. **Infer current architecture**
   - From the codebase: identify layers (e.g. API, domain, persistence), boundaries, and dependency direction (who depends on whom).
   - Note documented architecture (ADRs, README, docs) and compare to actual structure.

2. **Assess the change**
   - For the proposed or existing change: which layers and modules are touched? Are new dependencies introduced?
   - Check: dependency direction (e.g. domain not depending on API), absence of circular deps, and placement of new code (right layer, right module).

3. **Flag violations**
   - List concrete violations: wrong dependency, blurred boundary, duplicated responsibility, or drift from stated architecture.
   - Cite files or modules; be specific.

4. **Suggest alignment**
   - Propose moves, extractions, or interface changes to restore fit. Prefer minimal changes that satisfy the architecture.
   - If the architecture is unclear or inconsistent, say so and suggest documenting or fixing it first.

## Notes

- Do not impose an architecture the project does not follow; infer from the repo.
- Distinguish "violation" from "style preference"; focus on boundaries and dependencies.
