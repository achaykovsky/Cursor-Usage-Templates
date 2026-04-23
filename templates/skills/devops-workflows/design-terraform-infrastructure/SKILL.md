---
name: design-terraform-infrastructure
description: Designs Terraform infrastructure architecture with module boundaries, state strategy, environment layout, and policy controls. Use when planning Terraform for new systems or major infrastructure refactors.
---

# Design Terraform Infrastructure

## Workflow

1. **Define infrastructure scope**
   - Identify required services, environments, and non-functional constraints (security, availability, cost).
   - Capture cloud/account/region boundaries.

2. **Design module architecture**
   - Define root modules and reusable child modules.
   - Keep module interfaces minimal and stable (inputs/outputs).

3. **Define state and environment strategy**
   - Specify remote backend, locking, and state isolation model per environment/account.
   - Define workspace vs directory strategy explicitly.

4. **Design security and policy controls**
   - Define IAM boundaries, secret injection model, and tagging standards.
   - Include policy-as-code checks and drift detection expectations.

5. **Plan change lifecycle**
   - Define plan/review/apply flow and approval gates.
   - Define import/migration strategy for pre-existing resources.

## Output Contract

- Module and environment topology
- State/backend strategy
- Security/policy controls
- Plan/apply governance model

## Notes

- Prefer composition of small modules over a single mega-module.
- Pair with `implement-terraform-modules` for concrete code changes.
