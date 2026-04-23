---
name: implement-ci-cd-pipeline
description: Implements CI/CD workflows in repository CI systems with deterministic builds, test gates, artifact publishing, and controlled deployments. Use when creating or updating CI/CD pipeline config files.
---

# Implement CI/CD Pipeline

## Workflow

1. **Detect CI platform and project conventions**
   - Identify platform (`.github/workflows`, GitLab CI, Azure Pipelines, etc.).
   - Reuse existing cache, artifact, and secret patterns.

2. **Implement deterministic CI**
   - Pin runtime/tool versions and dependency restore strategy.
   - Add lint/test/build jobs with explicit failure gates.

3. **Implement CD flow**
   - Add environment-aware deployment steps and approvals.
   - Ensure deploy jobs are branch/tag constrained and idempotent.

4. **Harden pipeline security**
   - Use least-privilege tokens, avoid echoing secrets, and mask sensitive values.
   - Validate third-party actions/plugins and pin trusted versions.

5. **Add operational safeguards**
   - Include retry policy for transient failures.
   - Add post-deploy verification/smoke checks and rollback command path.

## Output Contract

- CI/CD files added/updated
- Stage/job summary and gates
- Secrets/permissions expectations
- Verification and rollback steps

## Notes

- Prefer `suggest-commands-dont-run-destructive` for deploy/publish operations.
- Pair with `validate-infra-changes-pre-apply` when deployments include IaC changes.
