---
name: plan-architecture-evolution
description: Plans architecture-level evolution from current state to target state with compatibility, migration phases, and risk controls. Use when refactoring major subsystems, splitting services, replacing infrastructure, or addressing architecture drift.
---

# Plan Architecture Evolution

## Workflow

1. **Baseline current architecture**
   - Document current modules/services, dependency directions, and critical data paths.
   - Mark known pain points and architectural debt.

2. **Define target architecture**
   - Describe target boundaries, contracts, and operational expectations.
   - Keep target minimal and testable.

3. **Design migration phases**
   - Break migration into reversible increments.
   - Define compatibility strategy between old/new paths (adapter, dual-write/read, versioning, feature flags).

4. **Control risk per phase**
   - For each phase, define success metrics, observability requirements, and rollback triggers.
   - Call out data consistency and idempotency constraints explicitly.

5. **Govern rollout**
   - Assign ownership and decision checkpoints.
   - Define completion criteria and decommission criteria for legacy paths.

## Output Contract

- Current vs target architecture summary
- Phase-by-phase migration plan
- Risk/rollback controls per phase
- Ownership and completion criteria

## Notes

- Do not remove legacy paths until replacement is verified and agreed.
- Pair with `handle-breaking-change` when public contracts are affected.
- Pair with `write-or-update-adr` to persist rationale and superseded decisions.
