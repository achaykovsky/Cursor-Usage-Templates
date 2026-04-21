---
name: evolve-design-system-without-breaking-ui
description: Evolves frontend design-system tokens and component variants with compatibility guidance and migration safety. Use when adding or changing design tokens, shared component APIs, or visual standards across multiple frontend surfaces.
---

# Evolve Design System Without Breaking UI

## Workflow

1. **Classify change type**
   - Token change, component API change, variant change, or behavior/state change.
   - Mark whether change is additive, soft-breaking (visual drift), or hard-breaking (API contract change).

2. **Assess impact surface**
   - Identify affected components, pages, and likely high-risk usage patterns.
   - Flag areas where visual regressions are likely (spacing, typography, contrast, focus states).

3. **Define compatibility strategy**
   - Prefer additive extension first (new token/variant) over destructive replacement.
   - If deprecating, define transition window and clear replacement mapping.

4. **Specify migration path**
   - Provide before/after usage guidance with deterministic mapping.
   - Include fallback behavior for consumers not yet migrated.

5. **Guard consistency and accessibility**
   - Ensure token choices preserve contrast and interaction clarity.
   - Keep component API entropy low; remove ambiguous or overlapping variants.

## Output Contract

- Change classification (additive/soft-breaking/hard-breaking)
- Affected surface summary
- Migration mapping and deprecation guidance
- Accessibility consistency checks

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
