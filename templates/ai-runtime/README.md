# AI Runtime Templates

**Hub for customer-facing bots and deployed AI agents.** Authoring lives in Cursor (`templates/rules/`, `templates/skills/`, `templates/agents/`); runtime artifacts here ship into application repos.

**Not synced wholesale to `.cursor/`** — copy or scaffold selectively during bot implementation. See [USAGE.md](../USAGE.md) for the four-layer authoring model.

---

## Authoring vs runtime

| Layer | Who | Location | Purpose |
|-------|-----|----------|---------|
| **Authoring** | Engineers in Cursor | [rules/RULES.md](../rules/RULES.md), [skills/SKILLS.md](../skills/SKILLS.md), [agents/subagents/AGENTS.md](../agents/subagents/AGENTS.md), [hooks/HOOKS_USAGE.md](../hooks/HOOKS_USAGE.md) | Build and operate bot services safely |
| **Runtime** | End users / customers | `templates/ai-runtime/` | Deployed bots (Slack, web, API) with policy + observability |

**Start building a bot:** paste [plan-ai-infrastructure.md](../prompts/plan-ai-infrastructure.md) or invoke skill `orchestrate-ai-bot-delivery`.

**Review an existing or planned LLM system:** paste [plan-llm-system-design-review.md](../prompts/plan-llm-system-design-review.md) or invoke skill `review-llm-system-design` with `@agent(AI_SYSTEM_REVIEWER)`.

---

## Layout

| Path | Purpose |
|------|---------|
| [bots/](bots/README.md) | Bot manifest schema + examples |
| [policy/](policy/README.md) | Runtime deny/ask/allow policy (mirrors `hooks/policy/`) |
| [guardrails/](guardrails/README.md) | Input, output, and handoff policies |
| [observability/](observability/README.md) | Traces, audit schema, eval metrics |
| [channels/](channels/README.md) | Slack, web widget, API adapter notes |
| [rag/README.md](rag/README.md) | Corpus manifests, golden eval fixtures |
| [eval/README.md](eval/README.md) | Prompt eval suites, assertion schema, smoke fixtures |
| [design-review/](design-review/README.md) | LLM system design review checklist (12 dimensions) |

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
design-customer-facing-agent → evaluate-ai-safety-policy → design-prompt-evals
→ implement-bot-gateway → add-prompt-injection-defenses → design-ai-observability
→ implement-prompt-eval-runner → implement-human-handoff → monitor-ai-quality
```

Skill: `orchestrate-ai-bot-delivery` routes steps. Agents: `BOT_DESIGNER`, `AI_PLATFORM`, `AI_SAFETY`, `AI_OBSERVABILITY`.

---

## System design review

Retrospective review of design docs **and** implementation — not code/PR review.

```
review-llm-system-design + @agent(AI_SYSTEM_REVIEWER) → design-review/system-review-checklist.md
```

**Dimensions:** hallucination risks, context explosion, retrieval quality, prompt coupling, observability, evaluation, confidence calculation, deterministic business logic, tenant isolation, future tool calling, cost, latency.

**Prompt:** [plan-llm-system-design-review.md](../prompts/plan-llm-system-design-review.md)

---

## Policy vocabulary

Reuse the same modes as Cursor hooks (`deny`, `ask`, `allow`, `advisory`, `log`). Runtime gateway middleware should load [policy/default.bot.policy.json](policy/default.bot.policy.json) and [policy/tool-risk-catalog.json](policy/tool-risk-catalog.json).

---

## Security & guardrails checklist

| Control | Artifact |
|---------|----------|
| Input sanitization | [guardrails/input-sanitization.md](guardrails/input-sanitization.md), rule [ai-safety.mdc](../rules/ai-safety.mdc) |
| Tool allowlist / risk tiers | [policy/tool-risk-catalog.json](policy/tool-risk-catalog.json), [policy/default.bot.policy.json](policy/default.bot.policy.json) |
| Output policy | [guardrails/output-policy.md](guardrails/output-policy.md), rule [ai-customer-facing.mdc](../rules/ai-customer-facing.mdc) |
| Human handoff triggers | [guardrails/human-handoff.md](guardrails/human-handoff.md), skill [implement-human-handoff](../skills/ai-infra-workflows/implement-human-handoff/SKILL.md) |
| Rate limits / abuse | skill [implement-ai-rate-limiting](../skills/ai-infra-workflows/implement-ai-rate-limiting/SKILL.md) |
| Audit separation | [observability/conversation-audit.schema.json](observability/conversation-audit.schema.json), skill [design-ai-observability](../skills/ai-infra-workflows/design-ai-observability/SKILL.md) |

---

## Validate locally

```bash
python templates/ai-runtime/validate_bot_runtime.py manifest <path.json>
python templates/ai-runtime/validate_bot_runtime.py policy <path.json>
python templates/ai-runtime/validate_bot_runtime.py audit-event <path.json>
python templates/ai-runtime/validate_bot_runtime.py corpus <path.json>
python templates/ai-runtime/validate_bot_runtime.py golden <path.json>
python templates/ai-runtime/validate_bot_runtime.py prompt-eval <path.json>
python templates/ai-runtime/validate_bot_runtime.py eval-baseline <path.json>
python templates/ai-runtime/validate_bot_runtime.py judge-calibration <path.json>
```

See also [rag/README.md](rag/README.md), [policy/README.md](policy/README.md), and [design-review/README.md](design-review/README.md) (pre-launch system review).

---

## What is NOT here

- Hosted runtime (Lambda, K8s) — scaffold in app repos using these templates
- Live credentials — env vars and secret manager only
- Customer personas as Cursor `@agent()` — use [bots/examples/](bots/examples/) manifests instead
