---
name: design-multi-agent-routing
description: Designs router bots and specialist delegation — intent routing, fallbacks, context passing. Use when one entry bot dispatches to multiple domain agents.
---

# Design Multi-Agent Routing

## Workflow

1. **Router role** — classify intent; never execute destructive tools without specialist policy.
2. **Specialists** — one manifest per domain; shared `conversation_id`.
3. **Context** — minimal handoff payload between agents; redact cross-user data.
4. **Fallback** — default specialist or human handoff when confidence low.
5. **Cost** — cap router + specialist LLM calls per turn.
6. **Observability** — span per routing decision with `selected_agent` label.

## Output Contract

- Routing table (intent -> specialist | handoff)
- Context schema between agents
- Failure and fallback behavior

## Notes

- Pair with `@agent(AI_PLATFORM)`.
