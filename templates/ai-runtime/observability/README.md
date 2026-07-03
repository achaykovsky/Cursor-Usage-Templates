# AI observability

Traces, audit, and eval artifacts for customer bots.

| Path | Purpose |
|------|---------|
| [span-conventions.md](span-conventions.md) | Span names for LLM, tools, retrieval, embedding |
| [conversation-audit.schema.json](conversation-audit.schema.json) | Append-only audit event shape (IDs only — no full message bodies) |
| [eval-metrics.md](eval-metrics.md) | Offline and online quality metrics |

## Validate

```bash
python templates/ai-runtime/validate_bot_runtime.py audit-event <path.json>
```

**Skill:** [design-ai-observability](../../skills/SKILLS.md). **Agent:** @agent(AI_OBSERVABILITY).

**System design review:** checklist dimensions 5 (observability), 6 (evaluation), 11 (cost), 12 (latency) — [design-review/README.md](../design-review/README.md).
