---
name: implement-rag-ingest-and-index
description: Implements RAG ingest and index pipeline — document loaders, chunking, embedding batches, vector index writes. Use when building or updating a knowledge base index.
---

# Implement RAG Ingest and Index

## Workflow

0. **Discover existing capability** — Run **discover-before-implement** (shared-practices). Check corpus manifests and existing ingest jobs.

1. **Loaders** — markdown/HTML/PDF/API per corpus manifest `sources`; preserve `source_id` + version.
2. **Clean** — strip scripts; normalize whitespace; no executable payloads in stored chunks.
3. **Chunk** — apply manifest `chunking`; attach metadata for citation.
4. **Embed** — pin `embedding.model` + `dimensions`; batch per `design-batching-strategy`.
5. **Index** — upsert by `chunk_id`; idempotent re-run; namespace = corpus version.
6. **Validate** — `python templates/ai-runtime/validate_bot_runtime.py corpus <manifest.json>`.

## Delegation

| Concern | Delegate |
|---------|----------|
| Airflow/Prefect/CDC pipelines | `@agent(DATA_ENGINEER)`, `data-pipelines.mdc` |
| Batch size / backpressure | `design-batching-strategy` |
| PII before index | `sensitive-data-handling`, `ai-pii.mdc` |
| Corpus migration / reindex | `plan-and-execute-migration` |

## Output Contract

- Ingest job layout and idempotency keys
- Index write path and metadata schema
- Reindex trigger documentation

## Notes

- Follow `rag-pipeline.mdc` when editing `**/rag/**` code.
- Pair with `@agent(RAG_ENGINEER)`.
