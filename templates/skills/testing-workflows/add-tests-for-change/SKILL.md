---
name: add-tests-for-change
description: Identifies code paths touched by a change, finds test gaps, adds or updates unit or integration tests, runs the suite, and interprets failures. Use after implementing a feature or fix, or when the user says "add tests" or "test this."
---

# Add Tests for Change

## Workflow

1. **Identify touched code paths**
   - From the diff or change description: list modified or new functions, modules, and entry points (e.g. API routes, CLI commands).
   - Note branches: new conditionals, error paths, edge cases (empty input, null, bounds).

2. **Determine test gaps**
   - Locate existing tests for the same code (same file `test_*`, sibling test module, or integration tests).
   - For each touched path: is there a test that covers the new or changed behavior? Flag missing coverage for success and failure cases.

3. **Add or update tests**
   - Prefer the project's existing test style and framework (e.g. pytest, Jest).
   - Add tests for: happy path, explicit failure/error paths, and important edge cases.
   - Keep tests focused: one behavior per test; descriptive names (test_what_under_what_condition).
   - Avoid testing implementation details; test observable behavior and contracts.

4. **Run the suite**
   - Run the full test suite or the subset that covers the changed area. Use the project's normal command (e.g. `pytest`, `npm test`).
   - If the project uses coverage, run it and ensure new code is covered where appropriate.

5. **Interpret failures**
   - If tests fail: distinguish failures caused by the new tests (fix test or code) from pre-existing failures (report, do not hide).
   - Fix any failures introduced by the change or by the new tests. Re-run until the suite passes.

## Notes

- Prefer the project's patterns: fixtures, parametrization, mocks. Match naming and layout.
- When the framework is unclear, infer from existing test files in the repo.
