# RAG Runtime Templates

Corpus manifests and eval fixtures for knowledge-base bots.

**Authoring:**

- Skill: `orchestrate-rag-delivery`
- Agent: `@agent(RAG_ENGINEER)`

**Bot integration:** wire `search_knowledge_base` via skill `implement-bot-gateway` (extended) and [tool-risk-catalog.json](../policy/tool-risk-catalog.json).

## Layout

| Path | Purpose |
|------|---------|
| [corpus.manifest.schema.json](corpus.manifest.schema.json) | Corpus id, sources, chunking, embedding, retrieval, freshness |
| [eval/golden-questions.schema.json](eval/golden-questions.schema.json) | Offline retrieval eval fixtures |
| [examples/product-docs-corpus.json](examples/product-docs-corpus.json) | Sample corpus manifest |

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
| Prompt-level generation/adversarial evals | [eval/README.md](../eval/README.md) |
| E2E (retrieval + generation) | Compose golden retrieval with prompt eval suites |
| Traces | [span-conventions.md](../observability/span-conventions.md) |
| Pre-launch system review | [design-review/README.md](../design-review/README.md) — dimensions 1, 3 |
