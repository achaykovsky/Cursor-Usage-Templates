---
name: implement-ai-rate-limiting
description: Implements rate limits, abuse controls, and cost caps for LLM bots. Use when preventing DoS, spam, or runaway token spend on customer-facing agents.
---

# Implement AI Rate Limiting

## Workflow

0. **Discover existing capability** — Run **discover-before-implement** (shared-practices). Check existing gateway rate-limit middleware.

1. **Dimensions** — per user, per IP, per API key, per conversation.
2. **Limits** — requests/minute, tokens/day, concurrent sessions.
3. **Storage** — Redis or similar; fail closed or open per policy.
4. **Responses** — 429 with Retry-After; user-friendly bot message.
5. **Cost caps** — org-level budget alerts; soft stop before hard deny.
6. **Metrics** — counter `rate_limit_blocked` by reason (low cardinality).

## Output Contract

- Limit table with defaults and config keys
- Middleware integration points
- Abuse escalation link to human handoff or blocklist

## Notes

- Addresses OWASP LLM model denial of service; pair with `@agent(AI_PLATFORM)`.
