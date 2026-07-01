# Input Sanitization Guardrails

Apply to all customer-facing bot channels. Complements [ai-safety.mdc](../../rules/ai-safety.mdc).

## Principles

1. **Treat all user text as hostile** — prompt injection, jailbreaks, and encoded payloads are expected.
2. **Schema-bound inputs** — validate message length, encoding, and attachment types at the gateway boundary.
3. **Separate system and user channels** — never concatenate untrusted user content into system instructions without delimiters and length caps.
4. **Tool arguments are inputs** — LLM-proposed tool args must pass Pydantic/JSON Schema validation before execution.

## Gateway checks (before LLM)

| Check | Action |
|-------|--------|
| Max message length | Reject or truncate with user-visible notice |
| Attachment type allowlist | Block executables, scripts, unknown MIME |
| Rate limit per user/session | See `implement-ai-rate-limiting` skill |
| Known injection patterns | Log + optional block per policy mode |

## Context assembly

- Cap total context tokens; drop oldest turns before dropping system policy.
- Strip HTML/scripts from web channel input.
- Hash or omit PII from retrieval (RAG) unless policy explicitly allows.

## Escalation

When input matches abuse or policy violation patterns, route to [human-handoff.md](human-handoff.md) instead of debating with the model.
