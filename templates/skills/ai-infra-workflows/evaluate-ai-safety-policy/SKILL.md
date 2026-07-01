---
name: evaluate-ai-safety-policy
description: Evaluates AI safety policy for customer bots — content rules, PII in context, retention, tool risk. Use before launch or after material bot changes.
---

# Evaluate AI Safety Policy

## Workflow

1. **Data** — what PII enters context; retention and deletion windows.
2. **Content** — blocked topics; medical/legal/financial disclaimers.
3. **Tools** — map each tool to risk tier in `tool-risk-catalog.json`.
4. **Output** — [output-policy.md](../../../ai-runtime/guardrails/output-policy.md) compliance.
5. **OWASP LLM** — walk `security.mdc` LLM section; document gaps.
6. **ADR** — use `write-or-update-adr` for material policy decisions.

## Output Contract

- Policy matrix (area | rule | enforcement | owner)
- Gaps with severity (CRITICAL / WARNING / GOOD)
- Recommended manifest and policy JSON changes

## Notes

- Pair with `@agent(AI_SAFETY)`; not a substitute for legal review.
