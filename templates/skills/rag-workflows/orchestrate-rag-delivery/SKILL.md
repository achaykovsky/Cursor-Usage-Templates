---
name: orchestrate-rag-delivery
description: Routes RAG and knowledge-base work across rag-workflows skills with delegation to existing data, safety, and observability workflows. Use when building vector search, document corpora, or KB-backed bots, or when ingest vs retrieve ownership is unclear.
---

# Orchestrate RAG Delivery

## Canonical Sequence

0. Discover existing capability (`discover-before-implement`) — corpus manifests, index, retrieval handlers
1. Corpus and index design (`design-rag-architecture`)
2. Ingest, chunk, embed, index (`implement-rag-ingest-and-index`)
3. Query, rerank, cite (`implement-retrieval-pipeline`)
4. Safety for untrusted corpora (`evaluate-ai-safety-policy`) — when needed
5. Injection hardening (`add-prompt-injection-defenses`)
6. Retrieval eval (`monitor-ai-quality` — RAG section)
7. Bot tool wiring (`implement-bot-gateway` — if `search_knowledge_base` tool)

## Routing Decision Tree

- Corpus layout, store choice, hybrid vs dense -> `design-rag-architecture`
- Loaders, chunking, embeddings, index -> `implement-rag-ingest-and-index`
- top-k, rerank, citations, abstain -> `implement-retrieval-pipeline`
- Airflow/CDC/warehouse-scale ETL -> `@agent(DATA_ENGINEER)` + `data-pipelines.mdc`
- Embed batch sizing / throughput -> `design-batching-strategy`
- PII / poisoning / policy -> `evaluate-ai-safety-policy`, `sensitive-data-handling`
- Traces and dashboards -> `design-ai-observability` (retrieval spans in span-conventions.md)
- Golden set / recall@k -> `monitor-ai-quality`
- KB-backed bot -> `orchestrate-ai-bot-delivery` + `implement-bot-gateway`

## Escalation Boundaries

- **RAG_ENGINEER** for doc-loader through retrieve/cite implementation.
- **DATA_ENGINEER** for streaming/batch ETL pipelines only.
- **AI_SAFETY** for corpus trust and poisoning review.
- **ARCHITECT** for multi-tenant index topology (via `design-rag-architecture`).

## Output Contract

- Routing choice and why
- Sequence used (full or partial)
- Corpus manifest path under `ai-runtime/rag/`
- Delegated skills/agents explicitly listed
