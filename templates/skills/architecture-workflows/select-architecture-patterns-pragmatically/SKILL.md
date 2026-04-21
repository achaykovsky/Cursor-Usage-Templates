---
name: select-architecture-patterns-pragmatically
description: Selects architecture patterns only when justified by concrete failure modes or scaling pressure; rejects pattern cargo-culting. Use when deciding service boundaries, layering, repository/service patterns, CQRS, events, or modularization strategy.
---

# Select Architecture Patterns Pragmatically

## Workflow

1. **Identify the concrete problem**
   - Define current pain: coupling, testability, inconsistent boundaries, scaling bottleneck, ownership confusion.
   - Quantify impact where possible.

2. **Map problem to minimal pattern**
   - Choose the least complex pattern that directly addresses the pain.
   - Avoid introducing multiple new patterns in one step.

3. **Set adoption boundaries**
   - Specify where pattern applies and where it does not.
   - Define contracts/interfaces to prevent leakage across layers.

4. **Define enforcement signals**
   - Add review checks: dependency direction, module ownership, API boundary rules.
   - Specify anti-patterns that should be blocked.

5. **Plan incremental adoption**
   - Start with one vertical slice or module.
   - Validate outcome before broader rollout.

## Output Contract

- Problem -> pattern mapping
- Explicit in-scope/out-of-scope boundaries
- Enforcement checks and anti-pattern list
- Incremental adoption plan

## Notes

- Use patterns to reduce risk, not to mirror textbook architecture.
- Pair with `review-architecture-fit` after rollout to detect drift.
