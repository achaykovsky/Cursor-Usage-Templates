---
name: design-ai-observability
description: Designs observability for LLM bots — traces, audit logs, eval pipelines, SLOs. Use when instrumenting customer-facing agents for operations and incident response.
---

# Design AI Observability

## Workflow

1. **Correlation IDs** — `trace_id`, `conversation_id`, `turn_id` (W3C `traceparent`).
2. **Spans** — `llm.completion`, `tool.call`, `policy.block`, `handoff.human`.
3. **Metrics (RED)** — rate, errors, latency per channel; token/cost counters (low-cardinality labels).
4. **Audit** — append-only; use [conversation-audit.schema.json](../../../ai-runtime/observability/conversation-audit.schema.json); no full prompts unless opted in.
5. **Evals** — offline regression (`design-prompt-evals`, `implement-prompt-eval-runner`) + online thumbs/escalation rate.
6. **Eval telemetry** — [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md) for spans and metrics (do not duplicate here).
7. **Dashboards** — link metrics to `monitor-ai-quality` skill.

## Output Contract

- Span name table with required attributes
- Audit field mapping
- SLO proposals (latency, error budget, escalation rate)
- Log redaction rules

## Notes

- Follow `observability.mdc`; pair with `@agent(AI_OBSERVABILITY)`.
