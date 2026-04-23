---
name: design-ci-cd-pipeline
description: Designs CI/CD pipelines with stage boundaries, quality gates, deployment strategy, and rollback controls. Use when defining or redesigning build/test/deploy flow for an application or service.
---

# Design CI/CD Pipeline

## Workflow

1. **Define delivery constraints**
   - Identify runtime, artifact type, environments, release cadence, and compliance constraints.
   - Identify required checks (tests, lint, security scans, approvals).

2. **Design stage model**
   - Split pipeline into clear stages: validate, build, test, package, deploy, verify.
   - Define stage entry/exit criteria and failure behavior.

3. **Define promotion strategy**
   - Choose promotion model (branch-based, environment promotion, or tag-driven).
   - Define deployment strategy (rolling, blue/green, canary) and when to use each.

4. **Add controls**
   - Add quality/security gates, required reviewers, and protected branch expectations.
   - Define rollback triggers and automated/manual rollback path.

5. **Specify observability and ownership**
   - Define pipeline metrics (lead time, failure rate, MTTR) and alerting.
   - Assign ownership for failed stages and release approvals.

## Output Contract

- Pipeline stage diagram/list
- Promotion/deployment strategy
- Quality/security gates
- Rollback and ownership plan

## Notes

- Prefer incremental rollout and fast feedback over monolithic pipelines.
- Pair with `implement-ci-cd-pipeline` for concrete workflow files.
