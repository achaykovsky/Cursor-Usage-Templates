---
name: implement-bot-gateway
description: Implements LLM bot gateway — FastAPI or Go service, webhooks, session store, channel adapters. Use when scaffolding or extending customer-facing bot backends.
---

# Implement Bot Gateway

## Workflow

1. **Session model** — `conversation_id`, `user_id_hash`, channel, TTL.
2. **Ingress** — validate signatures (Slack), API keys, OAuth per channel doc.
3. **Pipeline** — sanitize input -> policy check -> LLM -> output policy -> respond.
4. **Tool runtime** — allowlist from manifest; enforce `deny`/`ask`/`allow` from policy JSON.
5. **Resilience** — timeouts, retries with backoff, circuit breaker ([llm-gateway.mdc](../../../rules/llm-gateway.mdc)).
6. **Deploy** — health checks, graceful shutdown, structured errors.

7. **Knowledge base tool (optional)** — when bot manifest includes `search_knowledge_base`:
   - Load corpus config from app `rag/` or linked manifest id.
   - Call retrieval handler built per `implement-retrieval-pipeline`.
   - Return citations to LLM tool channel; enforce read-only risk tier.

## Output Contract

- Service layout (routes, middleware, stores)
- Env var contract (no secrets in repo)
- Integration points for observability spans
- Test plan for webhook verification and session lifecycle

## Notes

- Pair with `@agent(AI_PLATFORM)`.
- Load policy from `templates/ai-runtime/policy/`.
- KB pipeline: `orchestrate-rag-delivery` when adding or changing retrieval.
