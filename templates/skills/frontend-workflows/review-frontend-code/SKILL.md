---
name: review-frontend-code
description: Performs frontend-focused code review for correctness, accessibility, performance, state handling, and regression risk. Use when the user asks to review frontend changes, React/TS diffs, UI regressions, or FE PR quality.
---

# Review Frontend Code

## Workflow

1. **Scope the frontend diff**
   - Collect changed FE files and classify by type: UI components, hooks/state, styling, tests, routing.
   - Identify user-facing flows and states affected (loading/empty/error/success).

2. **Review correctness and state behavior**
   - Validate render and event logic for stale state, closure bugs, race conditions, and side-effect leaks.
   - Check boundary handling: null/undefined data, empty collections, async failures, retries.

3. **Review accessibility and UX safety**
   - Verify semantic controls, keyboard reachability, focus behavior, and accessible labeling.
   - Confirm error and status messaging remains perceivable and does not rely on color alone.

4. **Review performance and maintainability**
   - Flag unnecessary re-renders, unstable callback/prop patterns, expensive render-time work, and avoidable bundle growth.
   - Assess component responsibilities, duplication, and API clarity for long-term maintainability.

5. **Review tests and release risk**
   - Check whether critical behavior changes are covered with behavior-level tests.
   - Highlight missing assertions for failure paths and state transitions.

## Output Contract

- Findings grouped by severity (`CRITICAL`, `WARNING`, `GOOD`)
- Each finding includes impact and concrete remediation
- Explicit callout of missing tests or residual risk before merge

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
