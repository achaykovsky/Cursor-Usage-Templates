---
name: monitor-ai-quality
description: Monitors AI bot quality — regression evals, drift, thumbs feedback, escalation rates. Use after launch or when quality regressions are suspected.
---

# Monitor AI Quality

## Workflow

1. **Baseline** — golden questions + expected properties (not always exact match).
2. **Prompt evals** — generation/adversarial suites under `ai-runtime/eval/`; design with `design-prompt-evals` before first baseline.
3. **RAG retrieval** — recall@k, MRR on `ai-runtime/rag/eval/` fixtures.
4. **Online** — thumbs up/down, escalation rate, containment rate.
5. **Regression** — CI eval job on manifest/policy/corpus/prompt changes.
6. **Drift** — alert on rising refusals, latency, or token use.
7. **Review loop** — sample audit logs (redacted) weekly.
8. **Incident** — link degradations to `@agent(INCIDENT)` with trace IDs.

## Output Contract

- Eval set location and pass criteria
- Dashboard metrics list
- Alert thresholds and owners

## Notes

- See [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md); pair with `@agent(AI_OBSERVABILITY)`.
