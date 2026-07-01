# Cursor Prompt: Plan AI Infrastructure (Customer-Facing Bots)

**Usage:** Paste into Chat/Composer with your **bot/platform one-liner** and optional constraints.

**Reference:** [ai-runtime/README.md](../ai-runtime/README.md) | [USAGE.md](../USAGE.md) | skill `orchestrate-ai-bot-delivery` | CLI: `templates/commands/route-session.ps1`

---

## Inputs (user provides)

```
Goal: <e.g. Slack support bot for billing questions>
Channels: <slack | web | api | multi>
Constraints: <optional — HIPAA, no PII in logs, budget cap, etc.>
```

---

## Instructions for Cursor

Produce **only** the following (no full skill bodies, no hook code):

### 1. Route table (max 8 rows)

| Step | Layer | Choice | Why (one line) |
|------|-------|--------|----------------|
| 1 | skill | orchestrate-ai-bot-delivery or specific skill | … |

Canonical sequence when multi-step:

`design-customer-facing-agent` → `evaluate-ai-safety-policy` → `implement-bot-gateway` → `add-prompt-injection-defenses` → `design-ai-observability` → `implement-human-handoff` → `monitor-ai-quality`

### 2. Runtime artifacts

List files to create under `ai-runtime/` or app repo:

- Bot manifest (`bots/manifest.schema.json` shape)
- Policy JSON (`policy/default.bot.policy.json`)
- Observability (audit schema, span names)
- Channel adapter notes

### 3. Rules note

Scoped rules: `ai-customer-facing`, `ai-safety`, `ai-pii`, `llm-gateway` + always-applied.

### 4. Agents note

Suggest `@agent(BOT_DESIGNER)`, `@agent(AI_PLATFORM)`, `@agent(AI_SAFETY)`, `@agent(AI_OBSERVABILITY)` per step.

### 5. Security and guardrails checklist

- Input sanitization, tool allowlist, output policy, handoff triggers, rate limits, audit separation.

### 6. Do not use

Skills/agents that duplicate the route or belong to unrelated domains (e.g. FE_* for pure API gateway work).

---

## Constraints

- Customer personas are **runtime manifests**, not Cursor `@agent()` entries.
- Runtime bots cannot use Cursor hooks — specify CI + gateway middleware equivalents.
- No secrets in manifests; use env var names only.

---

## Optional: RAG knowledge-base track

When the bot uses `search_knowledge_base` or a standalone RAG pipeline, extend the plan with:

### RAG route table (add rows; max 12 total)

Canonical sequence:

`design-rag-architecture` → `implement-rag-ingest-and-index` → `implement-retrieval-pipeline` → `monitor-ai-quality` → (`implement-bot-gateway` if bot-integrated)

Delegate (do not duplicate): `DATA_ENGINEER` for ETL, `evaluate-ai-safety-policy`, `add-prompt-injection-defenses`, `design-ai-observability`, `sensitive-data-handling`.

### RAG runtime artifacts

Under `ai-runtime/rag/`:

- Corpus manifest (`corpus.manifest.schema.json` shape)
- Golden eval set (`eval/golden-questions.schema.json`)
- Span names for retrieval/embedding (see `observability/span-conventions.md`)

Validate locally: `python templates/ai-runtime/validate_bot_runtime.py corpus|golden <file.json>`

### RAG rules and agents

- Rule: `rag-pipeline` (+ cross-refs in `ai-pii`, `ai-safety`, `data-pipelines`)
- Agent: `@agent(RAG_ENGINEER)` for ingest/index/retrieval work
- Optional stack appendix: `implement-rag-with-langchain-stack` (LangChain/LangGraph/LangSmith — only if team standard)

### RAG hooks (CI / template repo)

- `validate-rag-artifacts` — schema validation on corpus/golden JSON edits
- `scan-logs-in-edit` — corpus PII advisory scan on RAG JSON paths
