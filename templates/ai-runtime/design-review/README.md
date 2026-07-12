# LLM system design review

Pre-launch and periodic review of customer-facing LLM systems — **not** code/PR review.

| Doc | Purpose |
|-----|---------|
| [system-review-checklist.md](system-review-checklist.md) | 12-dimension checklist: questions, pass criteria, failure modes |

**Skill:** `review-llm-system-design`

**Agent:** `@agent(AI_SYSTEM_REVIEWER)`

**Prompt:** [plan-llm-system-design-review.md](../../prompts/plan-llm-system-design-review.md)

## When to use

- Before launch or after material architecture changes
- When reviewing design docs, ADRs, `ai-runtime/` artifacts, gateway code, or RAG pipelines together
- When the ask is system design (hallucination, context, retrieval, tenant isolation) — not line-level diff review

## Invocation

```
@agent(AI_SYSTEM_REVIEWER) review @templates/ai-runtime/ against the system design checklist
```

Or paste [plan-llm-system-design-review.md](../../prompts/plan-llm-system-design-review.md) with your system name and scope.

## Remediation

The review produces findings only. Route fixes to existing skills:

- `design-prompt-evals`
- `implement-prompt-eval-runner`
- `implement-retrieval-pipeline`
- `design-ai-observability`
- `evaluate-ai-safety-policy`

See the remediation map in the skill for the full list.

## Related runtime docs

| Area | README | Checklist dimensions |
|------|--------|-------------------|
| Guardrails | [guardrails/README.md](../guardrails/README.md) | 1, 4, 7 |
| Bots / manifests | [bots/README.md](../bots/README.md) | 2, 4 |
| RAG | [rag/README.md](../rag/README.md) | 1, 3 |
| Policy / tools | [policy/README.md](../policy/README.md) | 8, 9, 10 |
| Observability | [observability/README.md](../observability/README.md) | 5, 6, 11, 12 |
| Prompt evals | [eval/README.md](../eval/README.md) | 5 (offline regression, adversarial CI) |
| Channels | [channels/README.md](../channels/README.md) | 11, 12 |

**Hub:** [ai-runtime/README.md](../README.md)
