---
name: validate-pre-deploy
description: Runs a pre-deploy checklist: tests, migrations, config, secrets, feature flags; reports gaps and suggests fixes. Use when the user says "ready to deploy," "pre-flight check," or "can we ship this."
---

# Validate Pre-Deploy

## Workflow

1. **Run tests**
   - Run the full test suite (unit and integration). Report pass/fail and any flaky or skipped tests. If something fails, list failures and suggest fixing before deploy.
   - If the project has smoke or deploy-validation tests, run them and report.

2. **Migrations and schema**
   - Are there pending migrations or schema changes that must run before or during deploy? List them and the order. Ensure they are backward compatible or that the deploy plan runs them correctly (e.g. before new code).
   - Flag any destructive migration (e.g. drop column) and confirm the user has a backup or rollback plan.

3. **Config and secrets**
   - Are required env vars or config documented and present in the target environment? Flag missing or placeholder values. Ensure no dev-only or test secrets are used in production config.
   - If the project uses feature flags, note any that must be toggled for this release.

4. **Dependencies and build**
   - Lockfile or dependency list in sync with manifest? Build succeeds and produces expected artifacts? No known high-severity vulnerabilities in runtime deps (refer to assess-and-update-dependencies if needed).

5. **Summarize**
   - Pass/fail per area. List blocking issues first, then recommendations. If all pass, state that the pre-deploy checklist is satisfied and remind about post-deploy verification (e.g. health check, smoke test).

## Notes

- Apply **suggest-commands-dont-run-destructive** (shared-practices): only validate and report; suggest fixes and let the user run deploy.
- If the project has a formal checklist or runbook, align with it and note any missing items.
