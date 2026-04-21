---
name: implement-accessible-ui-from-spec
description: Implements frontend UI from UX or design-system specs with semantic HTML, responsive behavior, and accessibility defaults. Use when building or updating React/TypeScript pages/components from requirements, mockups, or state definitions.
---

# Implement Accessible UI from Spec

## Workflow

1. **Parse implementation inputs**
   - Extract required UI states, interactions, constraints, and acceptance criteria from spec/ticket.
   - Identify missing inputs (breakpoints, disabled/error behavior, loading skeletons). If missing, state assumptions.

2. **Map to component structure**
   - Split into composable components with clear prop contracts.
   - Keep domain/state orchestration out of presentational components unless explicitly requested.

3. **Implement semantic, responsive UI**
   - Use semantic elements first; ARIA only when semantics are insufficient.
   - Implement mobile-first layout and explicit behavior at key breakpoints.
   - Cover default, loading, empty, error, and success visual states.

4. **Accessibility pass before finish**
   - Validate keyboard reachability and focus order.
   - Ensure visible focus and meaningful labels for interactive controls.
   - Avoid color-only state signaling.

5. **Implementation sanity checks**
   - Verify props are typed and minimal.
   - Remove dead styles/variants introduced during iteration.

## Output Contract

- List implemented components/pages and their responsibilities.
- List assumptions and unresolved UX/design gaps.
- Note accessibility checks performed and any known limitations.

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
