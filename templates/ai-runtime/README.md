# AI Runtime Templates

**Hub for customer-facing bots and deployed AI agents.** Authoring lives in Cursor (`templates/rules/`, `templates/skills/`, `templates/agents/`); runtime artifacts here ship into application repos.

**Not synced wholesale to `.cursor/`** — copy or scaffold selectively during bot implementation. See [USAGE.md](../USAGE.md) for the four-layer authoring model.

---

## Authoring vs runtime

| Layer | Who | Location | Purpose |
|-------|-----|----------|---------|
| **Authoring** | Engineers in Cursor | `templates/rules/`, `skills/`, `agents/`, `hooks/` | Build and operate bot services safely |
| **Runtime** | End users / customers | `templates/ai-runtime/` | Deployed bots (Slack, web, API) with policy + observability |

**Start building a bot:** paste [plan-ai-infrastructure.md](../prompts/plan-ai-infrastructure.md) or invoke skill `orchestrate-ai-bot-delivery`.

---

## Layout

| Path | Purpose |
|------|---------|
| [bots/](bots/) | Bot manifest schema + examples |
| [policy/](policy/) | Runtime deny/ask/allow policy (mirrors `hooks/policy/`) |
| [guardrails/](guardrails/) | Input, output, and handoff policies |
| [observability/](observability/) | Traces, audit schema, eval metrics |
| [channels/](channels/) | Slack, web widget, API adapter notes |
| [rag/](rag/) | Corpus manifests, golden eval fixtures |

---

## RAG build sequence

```
design-rag-architecture → implement-rag-ingest-and-index → implement-retrieval-pipeline
→ monitor-ai-quality (RAG metrics) → implement-bot-gateway (if bot)
```

Skill: `orchestrate-rag-delivery`. Agent: `RAG_ENGINEER`.

---

## Canonical build sequence

```
design-customer-facing-agent → evaluate-ai-safety-policy → implement-bot-gateway
→ add-prompt-injection-defenses → design-ai-observability → implement-human-handoff
→ monitor-ai-quality
```

Skill: `orchestrate-ai-bot-delivery` routes steps. Agents: `BOT_DESIGNER`, `AI_PLATFORM`, `AI_SAFETY`, `AI_OBSERVABILITY`.

---

## Policy vocabulary

Reuse the same modes as Cursor hooks (`deny`, `ask`, `allow`, `advisory`, `log`). Runtime gateway middleware should load [policy/default.bot.policy.json](policy/default.bot.policy.json) and [policy/tool-risk-catalog.json](policy/tool-risk-catalog.json).

---

## What is NOT here

- Hosted runtime (Lambda, K8s) — scaffold in app repos using these templates
- Live credentials — env vars and secret manager only
- Customer personas as Cursor `@agent()` — use [bots/examples/](bots/examples/) manifests instead
