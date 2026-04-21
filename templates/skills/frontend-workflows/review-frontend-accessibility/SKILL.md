---
name: review-frontend-accessibility
description: Reviews frontend interfaces for accessibility risks and provides prioritized remediation guidance aligned to WCAG-oriented practices. Use when the user asks for accessibility review, keyboard/screen-reader validation, or compliance-focused frontend checks.
---

# Review Frontend Accessibility

## Workflow

1. **Scope critical user paths**
   - Select the highest-impact flows (auth, checkout, forms, navigation, modal interactions).
   - Include major state variants: loading, empty, error, success.

2. **Evaluate interaction accessibility**
   - Verify keyboard-only operation and logical focus order.
   - Check focus visibility and trap/return behavior for dialogs/overlays.

3. **Evaluate semantic/screen-reader quality**
   - Validate semantic structure and landmark usage.
   - Check control labeling, error messaging associations, and ARIA misuse.

4. **Evaluate perception and clarity**
   - Check contrast-sensitive elements and non-color signaling for status/errors.
   - Ensure dynamic updates are announced or otherwise perceivable.

5. **Prioritize findings**
   - Classify by severity and user impact.
   - Provide concrete fix guidance and expected behavior after remediation.

## Output Contract

- Findings list with severity and affected surface
- Concrete remediation actions
- Residual risks and follow-up checks

## Shared Routing

For cross-skill routing and FE-vs-generic escalation, follow `orchestrate-frontend-delivery`.
