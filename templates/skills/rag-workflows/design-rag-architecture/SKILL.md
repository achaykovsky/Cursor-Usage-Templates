---
name: design-rag-architecture
description: Designs RAG corpus architecture — sources, chunking strategy, embedding model lock, hybrid retrieval, index backend. Use when planning a knowledge base or choosing vector store topology.
---

# Design RAG Architecture

## Workflow

1. **Sources** — types, versions, refresh SLA; output `sources[]` for corpus manifest.
2. **Chunking** — fixed vs structure-aware; max tokens, overlap; citation metadata requirements.
3. **Embedding** — model + dimensions (pinned); re-embed plan on model change.
4. **Index** — backend choice; namespace per corpus version; metadata filters (tenant, doc_type).
5. **Retrieval** — hybrid default for keyword-heavy domains; rerank yes/no; min_score threshold.
6. **Tradeoffs** — delegate system-wide patterns to `evaluate-architecture-tradeoffs` / `@agent(ARCHITECT)`.

## Output Contract

- Draft [corpus.manifest.schema.json](../../../ai-runtime/rag/corpus.manifest.schema.json) JSON
- Chunk metadata fields: `source_id`, `doc_version`, `chunk_id`, `heading_path`, `pii_class`
- Non-goals and freshness/reindex triggers

## Notes

- Pair with `@agent(RAG_ENGINEER)`.
- Bulk ETL architecture -> `@agent(DATA_ENGINEER)`.
