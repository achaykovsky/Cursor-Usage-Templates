---
name: investigate-performance-issue
description: Defines metrics or baseline, locates the bottleneck (profiling, logs, code review), proposes and validates a fix; avoids changes that trade correctness for speed without explicit agreement. Use when the user reports "this is slow," "optimize X," or a performance regression.
---

# Investigate Performance Issue

## Workflow

1. **Define metrics or baseline**
   - What is slow? (e.g. request latency, throughput, memory, CPU.) Get a measurable baseline (current value and how it was measured).
   - If the user reports "regression," identify when it started (commit range, deploy) and what changed.

2. **Locate the bottleneck**
   - Use profiling, logs, or code review as appropriate: hot paths, N+1 queries, large allocations, blocking I/O, or inefficient algorithms.
   - Narrow to the smallest unit that explains the slowness (e.g. single query, loop, or call).

3. **Propose a fix**
   - Suggest a concrete change: optimize the hot path, add indexing, cache, batch work, or reduce allocations. Prefer changes that preserve correctness and readability.
   - Do not trade correctness for speed without the user's agreement (e.g. no removing validations or changing semantics as an "optimization").

4. **Validate**
   - After applying the fix: re-run the same metric or test. Confirm improvement and that behavior is unchanged (run tests). If the fix is speculative, suggest how to measure before/after.

## Notes

- Prefer measuring over guessing. If profiling is not possible, state assumptions and suggest adding metrics or a profile run.
- Document the root cause and fix briefly so future changes do not regress it.
