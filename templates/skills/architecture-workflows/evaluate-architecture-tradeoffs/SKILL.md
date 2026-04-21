---
name: evaluate-architecture-tradeoffs
description: Evaluates architecture options using explicit tradeoffs (scalability, coupling, operability, delivery risk) and recommends a decision with rationale. Use when choosing between system designs, technologies, or topology options.
---

# Evaluate Architecture Tradeoffs

## Workflow

1. **Define decision scope**
   - State the decision and constraints (latency, throughput, team capacity, compliance, cost, delivery timeline).
   - Define non-goals to avoid scope creep.

2. **Enumerate realistic options**
   - List 2-4 viable options only.
   - Include current-state baseline as an option when useful.

3. **Score by architecture criteria**
   - Evaluate each option on: scalability, reliability, security, coupling/cohesion, operational complexity, observability, and migration effort.
   - Call out irreversible choices early.

4. **Analyze failure modes**
   - Identify top failure modes and blast radius per option.
   - Note rollback/recovery feasibility.

5. **Recommend and sequence**
   - Provide a recommendation with explicit tradeoffs accepted.
   - Propose phased rollout with checkpoints and kill-switch/rollback plan.

## Output Contract

- Decision statement
- Option matrix with pros/cons and risks
- Recommended option with rationale
- Rollout sequence and validation checkpoints

## Notes

- Prefer smallest architecture that satisfies constraints (YAGNI).
- Pair with `write-or-update-adr` to record accepted decisions.
