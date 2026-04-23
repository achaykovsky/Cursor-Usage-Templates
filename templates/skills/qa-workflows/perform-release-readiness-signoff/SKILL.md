---
name: perform-release-readiness-signoff
description: Produces QA release readiness signoff based on test execution, open defect risk, rollback preparedness, and operational checks. Use before release cut or production deployment approval.
---

# Perform Release Readiness Signoff

## Workflow

1. **Collect readiness evidence**
   - Gather latest test cycle results, defect status, and pre-deploy validation outcomes.
   - Confirm build/version and deployment scope under review.

2. **Assess release blockers**
   - Identify unresolved CRITICAL/HIGH defects and workaround quality.
   - Evaluate deployment and rollback readiness.

3. **Assess operational and user risk**
   - Confirm monitoring/alerts and post-deploy checks are defined.
   - Confirm known-risk communication and mitigation ownership.

4. **Decide signoff status**
   - Mark: approved, conditionally approved, or not approved.
   - For conditional/no-go, list blocking actions and revalidation criteria.

5. **Publish signoff record**
   - Provide concise release decision summary with traceable evidence references.
   - Include explicit assumptions and residual risk acceptance.

## Output Contract

- Signoff decision and rationale
- Blocking issues and required actions
- Residual risk summary
- Revalidation plan (if not fully approved)

## Notes

- Pair with `validate-pre-deploy` for deployment-level readiness checks.
- Signoff must be evidence-based; avoid implicit approval language.
