---
name: triage-and-prioritize-defects
description: Triage defects using severity, user impact, reproducibility, and release risk; assigns disposition and remediation priority. Use when many bugs are reported and teams need a clear fix order.
---

# Triage and Prioritize Defects

## Workflow

1. **Normalize defect inputs**
   - Ensure each defect has reproducible steps, expected/actual behavior, and environment/build context.
   - Reject or mark insufficient reports for clarification.

2. **Score defect criticality**
   - Evaluate severity (functional break, data loss, security exposure, UX degradation).
   - Evaluate impact (affected users, frequency, business/release impact).

3. **Set priority and disposition**
   - Assign priority (P0/P1/P2/P3 or project equivalent).
   - Mark disposition: fix now, fix next release, defer, duplicate, or not-a-bug (with justification).

4. **Identify dependency and root-cause clusters**
   - Group related defects by subsystem/root area.
   - Flag cluster-level ownership and likely shared fixes.

5. **Publish triage outcome**
   - Provide ordered fix queue and blockers.
   - Highlight risks if high-severity defects remain open.

## Output Contract

- Defect triage table/list with severity + priority + disposition
- Top risk clusters and ownership
- Recommended fix sequence

## Notes

- Severity reflects user/system impact; priority reflects execution urgency.
- Pair with `execute-qa-test-cycle` for retest closure tracking.
