# RAG Runtime Templates

Corpus manifests and eval fixtures for knowledge-base bots. Authoring: skill `orchestrate-rag-delivery` and `@agent(RAG_ENGINEER)`.

**Bot integration:** wire `search_knowledge_base` via skill `implement-bot-gateway` (extended) and [tool-risk-catalog.json](../policy/tool-risk-catalog.json).

## Layout

| Path | Purpose |
|------|---------|
| [corpus.manifest.schema.json](corpus.manifest.schema.json) | Corpus id, sources, chunking, embedding, retrieval, freshness |
| [eval/golden-questions.schema.json](eval/golden-questions.schema.json) | Offline retrieval eval fixtures |
| [examples/](examples/) | Sample corpus manifests |

## Validate

```bash
python templates/ai-runtime/validate_bot_runtime.py corpus <path.json>
python templates/ai-runtime/validate_bot_runtime.py golden <path.json>
```

## Delegated workflows

| Concern | Use |
|---------|-----|
| ETL / streaming ingest | `@agent(DATA_ENGINEER)`, `data-pipelines.mdc` |
| Embed batching | `design-batching-strategy` |
| Safety / PII | `ai-pii.mdc`, `evaluate-ai-safety-policy`, `sensitive-data-handling` |
| Retrieval eval metrics | `monitor-ai-quality`, [eval-metrics.md](../observability/eval-metrics.md) |
| Traces | [span-conventions.md](../observability/span-conventions.md) |
