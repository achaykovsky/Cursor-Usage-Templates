---
name: validate-infra-changes-pre-apply
description: Validates infrastructure changes before apply/deploy by checking plans/change sets, policy/security guardrails, destructive risk, and rollback readiness. Use before Terraform apply or CloudFormation stack update.
---

# Validate Infra Changes Pre-Apply

## Workflow

1. **Collect proposed infrastructure diff**
   - Terraform: plan output and targeted resources.
   - CloudFormation: change set details and replacement actions.

2. **Assess destructive and replacement risk**
   - Flag deletions, forced replacements, and stateful resource changes.
   - Require explicit acknowledgment for high-blast-radius actions.

3. **Check policy and security constraints**
   - Validate IAM scope, network exposure, encryption, and tagging compliance.
   - Ensure secrets are referenced securely and not embedded.

4. **Verify operational readiness**
   - Confirm backups/snapshots where relevant.
   - Confirm rollback path and ownership for apply window.

5. **Gate decision**
   - Emit go/no-go with blocking issues first.
   - Provide exact remediation steps for each blocker.

## Output Contract

- Diff summary (plan/change-set)
- Blocking vs non-blocking findings
- Rollback readiness status
- Go/no-go decision with rationale

## Notes

- Apply `suggest-commands-dont-run-destructive`; recommend commands unless user explicitly requests execution.
- For app-level deploy readiness, pair with `validate-pre-deploy`.
