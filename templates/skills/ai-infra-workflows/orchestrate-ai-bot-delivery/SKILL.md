---
name: orchestrate-ai-bot-delivery
description: Routes customer-facing bot work across AI infra skills and agents with a consistent delivery sequence, shared vocabulary, and escalation boundaries. Use when building support bots, chatbots, or multi-channel AI agents, or when ownership between conversation design, gateway, safety, and observability is unclear.
---

# Orchestrate AI Bot Delivery

## Canonical Sequence

1. Conversation spec and persona (`design-customer-facing-agent`)
2. Safety and retention policy (`evaluate-ai-safety-policy`)
3. Gateway and session layer (`implement-bot-gateway`)
4. Injection and abuse defenses (`add-prompt-injection-defenses`)
5. Traces, audit, evals (`design-ai-observability`)
6. Human escalation (`implement-human-handoff`)
7. Quality monitoring (`monitor-ai-quality`)

Optional parallel tracks: `design-multi-agent-routing`, `implement-ai-rate-limiting`, `orchestrate-rag-delivery` (when bot needs a knowledge base).

## Routing Decision Tree

- Need intents, flows, tone, acceptance criteria -> `design-customer-facing-agent`
- Need PII/retention/content policy -> `evaluate-ai-safety-policy`
- Need FastAPI/Go gateway, webhooks, sessions -> `implement-bot-gateway`
- Need jailbreak/injection hardening -> `add-prompt-injection-defenses`
- Need LLM traces, audit schema, eval pipeline -> `design-ai-observability`
- Need ticket/Slack/human queue handoff -> `implement-human-handoff`
- Need router + specialist bots -> `design-multi-agent-routing`
- Need quotas, abuse, cost caps -> `implement-ai-rate-limiting`
- Need regression evals, drift, thumbs -> `monitor-ai-quality`
- Need knowledge base / RAG / vector search -> `orchestrate-rag-delivery`

## Escalation Boundaries

- **Use AI infra skills** for bot platform, gateway, safety, observability.
- **Escalate to `SECURITY`** for org-wide threat models beyond bot scope.
- **Escalate to `INCIDENT`** for production bot outages with customer impact.
- **Escalate to `DEVOPS`** for infra/CI not specific to LLM gateway.

## Output Contract

- Routing choice and why
- Sequence used (full or partial)
- Runtime artifacts to create under `ai-runtime/`
- Open ownership conflicts, if any
