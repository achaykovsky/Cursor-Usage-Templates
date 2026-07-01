---
name: implement-rag-with-langchain-stack
description: Optional LangChain/LangGraph/LangSmith implementation of RAG when the project already uses that stack. Use only when user names LangChain, LangGraph, or LangSmith; otherwise use neutral rag-workflows skills.
---

# Implement RAG with LangChain Stack (Optional)

**Prefer neutral path:** `implement-rag-ingest-and-index` + `implement-retrieval-pipeline` unless the repo already depends on LangChain.

## LangChain (ingest + retrieve)

- Document loaders and text splitters aligned with corpus manifest chunking settings.
- Vector store adapter matching manifest `index.backend`.
- Retriever with score threshold and metadata filters.

## LangGraph (orchestration)

- Graph nodes: retrieve -> grade (optional) -> generate; human approval for reindex if needed.
- Pass `conversation_id` / `trace_id` for observability.

## LangSmith (eval + traces)

- Dataset from `ai-runtime/rag/eval/*.json` golden fixtures.
- Trace `retrieval.query` and `llm.completion` spans; regression on corpus manifest changes.

## Output Contract

- Which neutral skills this replaces or wraps
- Dependency pins and env vars (no secrets in repo)
- Fallback if LangChain components are removed later

## Notes

- Pair with `@agent(RAG_ENGINEER)`.
- Safety and PII rules unchanged: `ai-pii.mdc`, `evaluate-ai-safety-policy`.
