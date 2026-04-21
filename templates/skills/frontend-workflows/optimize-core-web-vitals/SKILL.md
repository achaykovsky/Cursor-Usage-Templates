---
name: optimize-core-web-vitals
description: Improves frontend performance by targeting Core Web Vitals with measurement-first analysis and scoped fixes. Use when users report slow frontend behavior, high LCP/INP/CLS, large bundles, render jank, or route-level performance regressions.
---

# Optimize Core Web Vitals

## Workflow

1. **Define baseline and target**
   - Capture current vitals and route/context where regressions occur.
   - Set explicit target metrics for LCP, INP, and CLS before changing code.

2. **Find bottleneck source**
   - Determine whether issue is network/loading path, hydration/render work, or interaction handling.
   - Validate with profiling evidence (bundle stats, runtime traces, devtools profiling).

3. **Apply scoped fixes**
   - Loading path: split/lazy critical boundaries, optimize image/font delivery.
   - Render path: reduce unnecessary re-renders, virtualize heavy lists, simplify expensive computations.
   - Interaction path: defer non-critical work, debounce/throttle where appropriate.

4. **Re-measure and compare**
   - Re-run same measurements after fix.
   - Confirm no behavioral regressions in primary flows.

5. **Document guardrails**
   - Record what changed, impact observed, and guardrails to prevent regression.

## Output Contract

- Baseline vs post-change metrics
- Root cause summary with evidence
- Applied fixes and expected tradeoffs
- Follow-up monitoring recommendations

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
