---
name: plan-and-execute-migration
description: For data, schema, config, or code migrations: assesses scope, defines ordered steps, rollback strategy, and verification; executes in phases with checkpoints. Use when the user says "migrate X to Y," "we need to move off Z," or "schema migration."
---

# Plan and Execute Migration

## Workflow

1. **Assess scope**
   - What is being migrated? (Data, schema, config format, or code/dependency.) Identify source and target; list all consumers and touchpoints.
   - Estimate impact: downtime, data volume, and risk. Note backward compatibility requirements (e.g. dual-read during migration).

2. **Define steps and order**
   - Break into phases: e.g. add new schema/code alongside old, migrate data in batches, switch traffic, remove old. Each phase should be verifiable and, if possible, reversible.
   - Order steps so dependencies are respected (e.g. schema before data, code before config switch).

3. **Rollback and verification**
   - For each phase: what is the rollback (revert deploy, re-run script, restore backup)? How do we verify success (counts, checksums, smoke test)?
   - Suggest checkpoints: after each phase, run verification before proceeding.

4. **Execute in phases**
   - Execute (or provide exact commands/scripts) for one phase at a time. Run verification; only proceed if it passes. If the user prefers to run manually, output the plan and commands clearly.
   - Document what was done and any deviations. Note any follow-up (e.g. cleanup of old code in a later release).

## Notes

- Prefer non-destructive or additive steps first (e.g. new columns, new code path) so rollback is simpler.
- Apply **suggest-commands-dont-run-destructive** (shared-practices) for destructive or irreversible steps (e.g. drop table, delete data).
