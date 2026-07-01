# Human Handoff Guardrails

Mandatory for customer-facing bots. Implement via skill `implement-human-handoff`.

## Triggers (non-exhaustive)

| Category | Examples |
|----------|----------|
| User request | "talk to a human", "agent", "representative" |
| Sentiment | sustained anger, threats, repeated dissatisfaction |
| Policy | legal, medical, safety, harassment, self-harm |
| Auth | repeated failed verification, account takeover suspicion |
| Capability | bot cannot complete task after N turns |
| Tool risk | write/destructive tool would run — require human approval |

## Handoff payload

Include (redacted): `conversation_id`, `channel`, `user_id_hash`, `summary`, `last_user_message`, `policy_trigger`, `priority`.

Never include: full chat history with third-party PII, secrets, raw tool dumps.

## SLA and fallback

- Define target response time per channel in bot manifest `escalation.sla_minutes`.
- If queue unavailable, provide ticket URL, email, or phone — never silent failure.

## Audit

Log `handoff.human` span with outcome (`queued`, `failed`, `declined_by_user`). See [observability/conversation-audit.schema.json](../observability/conversation-audit.schema.json).
