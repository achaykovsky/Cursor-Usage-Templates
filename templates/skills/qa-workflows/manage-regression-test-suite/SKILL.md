---
name: manage-regression-test-suite
description: Curates and maintains a high-signal regression suite by selecting critical scenarios, removing flaky/low-value tests, and enforcing stable execution. Use when regression suites become slow, flaky, or low confidence.
---

# Manage Regression Test Suite

## Workflow

1. **Audit current regression suite**
   - Identify coverage by critical user flow and risk area.
   - Measure stability (flake rate), duration, and failure signal quality.

2. **Classify tests**
   - Keep: high-risk, high-signal, deterministic tests.
   - Refactor: useful but flaky or expensive tests.
   - Remove/defer: redundant low-value tests with poor signal.

3. **Optimize execution strategy**
   - Partition smoke vs full regression.
   - Schedule heavier suites appropriately (PR gate vs nightly/pre-release).

4. **Stabilize flaky tests**
   - Replace brittle timing assumptions with observable-state checks.
   - Improve fixtures/test data isolation and external dependency control.

5. **Set governance**
   - Define ownership, review thresholds, and suite health metrics.
   - Track regression escape rate and suite failure noise.

## Output Contract

- Regression suite inventory with keep/refactor/remove decisions
- Execution strategy (smoke/full cadence)
- Flake reduction plan and ownership

## Notes

- Optimize for confidence-per-minute, not raw test count.
- Pair with `add-tests-for-change` and FE testing workflows to close coverage gaps.
