---
name: reproduce-and-document-failure
description: Turns a failure report (error message, stack trace, steps) into a minimal reproduction, documents steps and environment, and optionally suggests assertions or test cases. Use when the user pastes an error, describes "it fails when," or asks to reproduce a bug.
---

# Reproduce and Document Failure

## Workflow

1. **Parse the failure report**
   - Extract: error type and message, stack trace (file, line, function), and any user-described steps (what they ran, with what input, in what order).
   - Note environment clues: OS, runtime or tool versions, relevant env vars if mentioned.

2. **Locate the failing code**
   - From the stack trace or description: find the source file and line(s). Read the surrounding code to understand the call path and preconditions.
   - Identify the immediate cause if possible (e.g. null dereference, failed assertion, wrong branch).

3. **Build a minimal repro**
   - Reduce to the smallest input and code path that still triggers the failure. Strip unrelated code and optional steps.
   - If the repo has tests: add or adapt a test that runs the failing scenario (same inputs/steps). Prefer a single focused test that fails with the same (or equivalent) error.
   - If a standalone script is clearer: produce a short script and exact run command (e.g. "run `python repro.py` with env X").

4. **Document**
   - Write a short repro description: steps to run, expected vs actual behavior, and relevant environment (runtime, OS, versions). Use a consistent format (e.g. Steps / Expected / Actual / Environment).
   - If the user uses an issue tracker, format so it can be pasted into an issue. Apply **redact-sensitive-in-output** (shared-practices).

5. **Optional: suggest assertions or tests**
   - Propose an assertion or test that would have caught this (e.g. "assert not null before use," or a unit test with the failing input). Tie it to the root cause.

## Notes

- If reproduction is not possible (e.g. missing data or environment), say so and list what is needed (exact command, sample input, version, logs).
- When documenting repro or pasting into a ticket: apply **redact-sensitive-in-output** (shared-practices).
