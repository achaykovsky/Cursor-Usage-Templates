# Customer Output Policy

Governs text and structured responses sent to end users. Complements [ai-customer-facing.mdc](../../rules/ai-customer-facing.mdc) and skill `redact-sensitive-in-output`.

## Required

1. **Identity disclosure** — state that the responder is an AI assistant when asked or on first contact (channel-dependent).
2. **No internal leakage** — no stack traces, internal hostnames, tenant IDs, other users' data, or unreleased product details.
3. **No secrets** — never echo API keys, tokens, connection strings, or full JWTs.
4. **Bounded claims** — no guaranteed outcomes for legal, medical, or financial advice; include appropriate disclaimers.
5. **Structured errors** — user-visible errors are generic; details go to server-side logs only.

## Tone

- Clear, concise, respectful.
- Match brand voice defined in bot manifest `persona.tone`.
- Avoid condescension when escalating or refusing requests.

## Redaction checklist (before send)

- [ ] No PII beyond what the user already provided in-thread
- [ ] No raw tool responses with internal fields
- [ ] No policy engine internals ("blocked by rule X")
- [ ] Links are allowlisted domains when configured

## Refusal pattern

When declining: brief reason, safe alternative if any, offer human handoff when appropriate.
