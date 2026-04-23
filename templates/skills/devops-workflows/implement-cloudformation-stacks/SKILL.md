---
name: implement-cloudformation-stacks
description: Implements CloudFormation templates with parameter validation, stack-safe update patterns, and predictable change-set behavior. Use when creating or modifying CloudFormation templates and stack definitions.
---

# Implement CloudFormation Stacks

## Workflow

1. **Define template contracts**
   - Implement parameters with clear types/constraints and safe defaults.
   - Keep outputs intentional and stable for consumers.

2. **Implement resource definitions**
   - Use explicit logical naming conventions and tagging standards.
   - Keep IAM policies least-privilege and scoped.

3. **Prepare update-safe behavior**
   - Identify resources with replacement risk and add safeguards where possible.
   - Prefer changes that minimize downtime and blast radius.

4. **Validate templates and changes**
   - Run template validation and lint checks.
   - Produce change sets for review before execution.

5. **Document deployment operations**
   - Document parameter files/overrides per environment.
   - Document rollback and drift-remediation procedure.

## Output Contract

- Templates changed and stack scope
- Parameter/output contract summary
- Change-set risk notes
- Deploy/rollback instructions

## Notes

- Do not embed secrets in templates; use managed secret references.
- Pair with `validate-infra-changes-pre-apply` before executing change sets.
