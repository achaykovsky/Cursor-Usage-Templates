---
name: design-ux-flow-spec
description: Produces implementation-ready frontend UX flow specs with user journeys, state matrices, and edge-case behavior. Use when the user asks to design a flow, define UX behavior, or clarify interaction requirements before coding.
---

# Design UX Flow Spec

## Workflow

1. **Define goal and actor**
   - Identify user type, success outcome, and primary task.
   - Capture key constraints (device, auth state, compliance, performance expectations).

2. **Map the flow**
   - Document step-by-step journey from entry to completion.
   - Include alternate branches: cancellation, retry, timeout, validation failure, and recoverability.

3. **Build state matrix**
   - For each step, define: trigger, system response, UI state, and user-visible message.
   - Include loading/empty/error/success states explicitly.

4. **Specify interaction details**
   - Define form validation timing, disabled rules, navigation behavior, and back/refresh behavior.
   - Define keyboard expectations and focus movement for key interactions.

5. **Write acceptance criteria**
   - Convert behavior into testable bullets (Given/When/Then or equivalent).
   - Mark uncertain requirements that need product clarification.

## Output Contract

- Journey steps (happy + failure paths)
- State matrix per critical step
- Accessibility-relevant interaction notes
- Testable acceptance criteria
- Open questions/assumptions

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
