---
name: implement-human-handoff
description: Implements human escalation for bots — queues, tickets, Slack threads, handoff payloads. Use when customers must reach a human from an AI assistant.
---

# Implement Human Handoff

## Workflow

1. **Triggers** — implement [human-handoff.md](../../../ai-runtime/guardrails/human-handoff.md) table in gateway.
2. **Payload** — redacted summary, `conversation_id`, priority, policy trigger.
3. **Channel** — Zendesk, Jira, Slack channel, email — per bot manifest `escalation`.
4. **User UX** — clear message while waiting; fallback if queue down.
5. **Audit** — `handoff.human` span with outcome.
6. **Tests** — trigger phrases, policy blocks, queue failure paths.

## Output Contract

- Handoff API or webhook integration spec
- Trigger configuration (manifest or policy)
- User-visible copy for wait/fallback states

## Notes

- Pair with `@agent(BOT_DESIGNER)` for copy; `@agent(AI_PLATFORM)` for integration.
