---
name: implement-terraform-modules
description: Implements Terraform modules and root stacks with safe variable contracts, provider constraints, and predictable plan/apply behavior. Use when writing or refactoring Terraform code.
---

# Implement Terraform Modules

## Workflow

1. **Set module contract**
   - Define required/optional variables with strict types and validation.
   - Define outputs only for values needed by consumers.

2. **Implement resource composition**
   - Prefer explicit dependencies and clear naming/tagging conventions.
   - Avoid hidden coupling via implicit references where possible.

3. **Harden provider/state behavior**
   - Pin provider versions and required Terraform version.
   - Align backend and locking config to environment strategy.

4. **Prepare safe change review**
   - Ensure `terraform fmt` and validation pass.
   - Produce plan output suitable for review and detect destructive changes.

5. **Document operational usage**
   - Document inputs, outputs, and apply order.
   - Document rollback/remediation path for failed applies.

## Output Contract

- Module/root files changed
- Variable/output contract summary
- Plan risk highlights
- Apply/rollback notes

## Notes

- Never assume in-place replacement is safe for stateful resources.
- Pair with `validate-infra-changes-pre-apply` before apply.
