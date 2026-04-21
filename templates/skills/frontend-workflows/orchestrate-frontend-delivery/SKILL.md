---
name: orchestrate-frontend-delivery
description: Routes frontend work across FE skills and agents with a consistent delivery sequence, shared state vocabulary, and escalation boundaries. Use when work spans multiple FE domains or when ownership between UX, UI, state, accessibility, testing, and performance is unclear.
---

# Orchestrate Frontend Delivery

## Canonical FE Sequence

1. UX intent and flow constraints (`design-ux-flow-spec`)
2. Design-system contract and compatibility (`evolve-design-system-without-breaking-ui`)
3. UI implementation (`implement-accessible-ui-from-spec`)
4. State/cache orchestration (`architect-frontend-state-and-cache`)
5. Accessibility review (`review-frontend-accessibility`)
6. Regression tests (`add-frontend-tests-for-change`)
7. Core Web Vitals/perf pass (`optimize-core-web-vitals`)

## Shared State Vocabulary

- **Loading**: waiting state before data or action completion.
- **Empty**: valid no-data state with clear next action.
- **Error**: failure state with recoverability guidance.
- **Success**: completion state with stable confirmation.

Every FE workflow should define these states when relevant.

## Routing Decision Tree

- Need user journey, state table, or acceptance criteria -> `design-ux-flow-spec`
- Need tokens/variants/component contract migration -> `evolve-design-system-without-breaking-ui`
- Need component/page markup and responsive behavior -> `implement-accessible-ui-from-spec`
- Need query keys/invalidation/optimistic updates/race handling -> `architect-frontend-state-and-cache`
- Need keyboard/focus/ARIA/WCAG validation -> `review-frontend-accessibility`
- Need RTL/Vitest/Playwright regression coverage -> `add-frontend-tests-for-change`
- Need LCP/INP/CLS diagnosis and optimization -> `optimize-core-web-vitals`

## Escalation Boundaries

- **Use FE agents/skills** for frontend-local concerns.
- **Escalate to generic `TESTER`** for cross-stack, backend, contract, or multi-service test strategy.
- **Escalate to generic `PERFORMANCE`** for backend, database, infra, or end-to-end system bottlenecks.

## Output Contract

- Routing choice and why
- Sequence used (full or partial)
- Open ownership conflicts, if any
