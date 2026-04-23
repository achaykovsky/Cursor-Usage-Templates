---
name: execute-qa-test-cycle
description: Executes a QA test cycle against a defined plan, tracks pass/fail status, logs defects with reproducible evidence, and summarizes quality status. Use when running feature, regression, or release QA.
---

# Execute QA Test Cycle

## Workflow

1. **Prepare execution baseline**
   - Confirm build/version under test, environment readiness, and test data availability.
   - Confirm feature flags/config expected for the cycle.

2. **Run prioritized scenarios**
   - Execute critical and high-risk scenarios first.
   - Track scenario status (pass/fail/blocked/not run) with timestamps.

3. **Capture defects with evidence**
   - Record reproducible steps, expected vs actual behavior, and severity/priority.
   - Attach evidence (logs, screenshots, API traces, failing test output) with sensitive data redacted.

4. **Retest and verify fixes**
   - Re-run failed scenarios after fixes.
   - Confirm no regressions in adjacent high-risk paths.

5. **Report cycle outcome**
   - Summarize pass rate, blockers, open defects by severity, and release impact.
   - Provide go/no-go recommendation with rationale.

## Output Contract

- Scenario execution summary
- Defect list with severity and reproducibility quality
- Retest/regression status
- Go/no-go recommendation

## Notes

- Prefer deterministic evidence over narrative-only bug reports.
- Pair with `triage-and-prioritize-defects` when defect volume is high.
