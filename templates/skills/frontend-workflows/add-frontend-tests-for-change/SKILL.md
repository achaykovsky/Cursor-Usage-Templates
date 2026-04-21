---
name: add-frontend-tests-for-change
description: Adds or updates frontend tests for changed behavior using RTL/Vitest/Playwright patterns, with deterministic assertions and regression focus. Use after frontend feature work, bug fixes, or when the user asks for FE test coverage.
---

# Add Frontend Tests for Change

## Workflow

1. **Identify changed FE behaviors**
   - List affected interactions, visual states, and data-state transitions.
   - Prioritize user-visible and failure-prone paths first.

2. **Build a test matrix**
   - Unit/component tests (RTL/Vitest) for rendering and interaction logic.
   - Integration/E2E (Playwright) for critical user journeys.
   - Include loading, empty, error, and recovery scenarios.

3. **Write deterministic tests**
   - Use AAA structure and behavior-focused assertions.
   - Prefer role/text/label queries over implementation selectors.
   - Mock external boundaries only where required; avoid over-mocking internals.

4. **Stabilize flaky paths**
   - Replace brittle timing assumptions with explicit waits on observable outcomes.
   - Ensure fixtures and seeded data are repeatable.

5. **Run and triage**
   - Run scoped tests first, then broader suite if needed.
   - Distinguish newly introduced failures from unrelated pre-existing failures.

## Output Contract

- Covered behaviors and remaining gaps
- Test types added/updated (unit/integration/e2e)
- Flake risks and mitigation notes

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
