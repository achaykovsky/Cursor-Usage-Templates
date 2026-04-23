---
name: design-cloudformation-stacks
description: Designs CloudFormation stack architecture with nested stacks, parameter strategy, environment isolation, and change control. Use when planning AWS infrastructure with CloudFormation.
---

# Design CloudFormation Stacks

## Workflow

1. **Define AWS scope and constraints**
   - Identify target accounts/regions/environments and compliance/security requirements.
   - Identify shared vs environment-specific resources.

2. **Design stack topology**
   - Define root/nested stacks and cross-stack export/import boundaries.
   - Keep stack responsibilities cohesive and independently changeable.

3. **Define parameter and configuration strategy**
   - Define parameter conventions, defaults, and required overrides.
   - Define secrets handling via secure references (SSM/Secrets Manager), not plaintext.

4. **Plan lifecycle and safety**
   - Define change set review workflow and rollback behavior.
   - Identify resources requiring replacement-risk controls.

5. **Define governance**
   - Define tagging, IAM least privilege, and drift detection expectations.
   - Define promotion model across environments/accounts.

## Output Contract

- Stack topology and boundaries
- Parameter/secret strategy
- Change-set governance and rollback model
- Environment promotion plan

## Notes

- Prefer nested stacks/modules when ownership and blast-radius boundaries differ.
- Pair with `implement-cloudformation-stacks` for template authoring.
