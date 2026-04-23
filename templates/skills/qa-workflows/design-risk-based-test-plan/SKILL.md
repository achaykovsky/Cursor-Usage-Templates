---
name: design-risk-based-test-plan
description: Designs a risk-based QA test plan that prioritizes high-impact user flows, failure modes, and release risk. Use when defining QA scope for a feature, sprint, or release.
---

# Design Risk-Based Test Plan

## Workflow

1. **Define scope and quality targets**
   - Identify features, affected components, environments, and release timeline.
   - Define quality goals (reliability, correctness, usability, performance, security).

2. **Assess risk**
   - Rank areas by impact x likelihood (critical, high, medium, low).
   - Prioritize user-critical paths, financial/security-sensitive actions, and integration points.

3. **Map test coverage**
   - Define coverage across unit, integration, API, UI/E2E, and non-functional checks.
   - For each high-risk area, define required positive/negative/edge scenarios.

4. **Define environments and data**
   - Specify required test environments, seed data, mocks/stubs, and external dependency strategy.
   - Define constraints (rate limits, 3rd-party sandbox availability, feature flags).

5. **Set entry/exit criteria**
   - Entry: prerequisites before execution.
   - Exit: pass criteria, defect thresholds, and signoff requirements.

## Output Contract

- Risk matrix with priority
- Coverage map by test level
- Environment/data requirements
- Entry/exit criteria and signoff expectations

## Notes

- Keep plan proportional to risk; avoid exhaustive low-value test lists.
- Pair with `execute-qa-test-cycle` for execution tracking.
