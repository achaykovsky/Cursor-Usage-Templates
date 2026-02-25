---
name: fix-bug-systematically
description: Reproduces, isolates, hypothesizes, fixes, and verifies bugs with tests and regression check. Use when the user reports a bug, says "this is broken," or is in a debugging session.
---

# Fix Bug Systematically

## Workflow

1. **Reproduce**
   - From the user's description or error: identify steps, inputs, and environment.
   - If possible, run the code or tests to reproduce the failure. Document exact steps and outcome.

2. **Isolate**
   - Narrow to the smallest unit (single function, single call path, single input) that still fails.
   - Use logs, breakpoints, or minimal repro (e.g. small script or single test) to confirm.

3. **Hypothesize**
   - State the likely cause (e.g. wrong condition, missing null check, off-by-one).
   - Identify the fix location and intended behavior change.

4. **Fix**
   - Apply a minimal change that addresses the root cause. Avoid unrelated edits.
   - Prefer clear, readable fixes over clever ones.

5. **Add or run tests**
   - Add a test that would have caught this bug (or extend an existing test).
   - Run the relevant test suite and ensure the new or updated test passes.

6. **Verify no regression**
   - Run the full test suite (or the scope the user cares about). If something else fails, treat it as pre-existing or fix it explicitly; do not hide regressions.

## Notes

- If reproduction is impossible (e.g. no access to env), say so and suggest what the user should run or capture (logs, stack trace, minimal repro).
- When the root cause is unclear, suggest targeted logging or assertions to confirm the hypothesis before changing behavior.
