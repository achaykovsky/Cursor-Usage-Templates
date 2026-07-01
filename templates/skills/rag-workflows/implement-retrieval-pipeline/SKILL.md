---
name: implement-retrieval-pipeline
description: Implements RAG retrieval — query processing, hybrid search, rerank, min score filter, citations, cite-or-abstain. Use when wiring search_knowledge_base or similar retrieve paths.
---

# Implement Retrieval Pipeline

## Workflow

1. **Query** — optional rewrite; cap length; log `retrieval.query` span.
2. **Recall** — vector + optional BM25 per manifest `retrieval.hybrid`; apply metadata filters.
3. **Rerank** — if `retrieval.rerank`; log `retrieval.rerank` span.
4. **Filter** — drop below `min_score`; max chunks to LLM context budget.
5. **Sanitize** — delegate chunk text hardening to `add-prompt-injection-defenses`.
6. **Respond** — return `chunk_id`, `source_id`, snippet; cite-or-abstain when empty.

## Output Contract

- Retrieval API or tool handler signature
- Citation format for bot/LLM consumer
- Tests: empty index, below threshold, hybrid hit, injection in chunk

## Notes

- Audit optional fields: `chunk_ids`, `corpus_version`, `retrieval_score` (conversation-audit.schema.json).
- Pair with `@agent(RAG_ENGINEER)`.
