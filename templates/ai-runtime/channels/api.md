# API Channel Adapter

## Auth

- API key in `Authorization: Bearer` or `X-API-Key` — rotate via secret manager.
- Optional OAuth2 client credentials for B2B integrations.

## Contract

- Versioned paths (`/v1/chat/completions` or `/v1/bots/{id}/messages`).
- Request: `conversation_id`, `message`, optional `metadata`.
- Response: `turn_id`, `reply`, `handoff` object when escalated.

## Errors

- 400 validation, 401 auth, 429 rate limit, 503 provider unavailable.
- JSON error body without internal details; include `trace_id` for support.

## Idempotency

- Support `Idempotency-Key` header for message POST retries.
