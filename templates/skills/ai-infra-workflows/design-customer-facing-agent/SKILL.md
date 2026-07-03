---
name: design-customer-facing-agent
description: Designs customer-facing bot specs — intents, conversation flows, persona, tone, and acceptance criteria. Use when planning support bots, chatbots, onboarding assistants, or FAQ agents for end users.
---

# Design Customer-Facing Agent

## Workflow

1. **Define goal** — primary user job (support, sales, onboarding, status).
2. **Channels** — Slack, web widget, API; note auth per [ai-runtime/channels/README.md](../../../ai-runtime/channels/README.md).
3. **Persona** — tone, boundaries, identity disclosure; document in bot manifest `persona`.
4. **Flows** — happy path, error, empty, escalation; map to [human-handoff.md](../../../ai-runtime/guardrails/human-handoff.md) triggers.
5. **Tools** — read vs write; align with `tool-risk-catalog.json`.
6. **Acceptance criteria** — measurable outcomes per intent.

## Output Contract

- Intent table with sample utterances
- Flow diagram or step list
- Manifest draft fields (`id`, `channels`, `persona`, `tools`, `escalation`)
- Non-goals and refusal boundaries

## Notes

- Persona ships as **runtime manifest**, not Cursor `@agent()`.
- Pair with `@agent(BOT_DESIGNER)` for review tone and flows.
