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

`design-customer-facing-agent` → `evaluate-ai-safety-policy` → `design-prompt-evals` → `implement-bot-gateway` → `add-prompt-injection-defenses` → `design-ai-observability` → `implement-prompt-eval-runner` → `implement-human-handoff` → `monitor-ai-quality`

### 2. Runtime artifacts

List files to create under `ai-runtime/` or app repo:

- Bot manifest (`bots/manifest.schema.json` shape)
- Policy JSON (`policy/default.bot.policy.json`)
- Observability (audit schema, span names)
- Channel adapter notes

### 3. Rules note

Scoped rules (plus always-applied):

- `ai-customer-facing`
- `ai-safety`
- `ai-pii`
- `llm-gateway`
- `prompt-evals` (when prompt eval track applies)

### 4. Agents note

Suggest per step:

- `@agent(BOT_DESIGNER)`
- `@agent(AI_PLATFORM)`
- `@agent(AI_SAFETY)`
- `@agent(AI_OBSERVABILITY)`

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

Delegate (do not duplicate):

- `@agent(DATA_ENGINEER)` — ETL
- `evaluate-ai-safety-policy`
- `add-prompt-injection-defenses`
- `design-ai-observability`
- `sensitive-data-handling`

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

---

## Optional: Prompt eval track

When the bot has versioned system prompts or requires regression gates on prompt/policy changes:

### Eval route table (add rows; max 12 total)

Canonical sequence:

`design-prompt-evals` → `add-prompt-injection-defenses` (export adversarial cases) → `implement-prompt-eval-runner` → (`calibrate-llm-judge-eval` if using LLM judge) → `monitor-ai-quality`

### Eval runtime artifacts

Under `ai-runtime/eval/`:

- Generation smoke suite (`generation/*.json`)
- Adversarial suite (`adversarial/*.json`) — from red-team export
- Baselines (`baselines/*-baseline.json`)
- Calibration fixtures (`calibration/*.json`) when using LLM judge
- Canned responses for offline CI (`fixtures/*-responses.json`)

Validate locally:

```bash
python templates/ai-runtime/validate_bot_runtime.py prompt-eval <suite.json>
python templates/ai-runtime/validate_bot_runtime.py eval-baseline <baseline.json>
python templates/ai-runtime/validate_bot_runtime.py judge-calibration <calibration.json>
python templates/ai-runtime/eval/prompt_eval_runner.py grade --suite <suite.json> --responses <responses.json> --baseline <baseline.json>
python templates/ai-runtime/eval/llm_judge_calibration.py analyze <calibration.json> --json
```

### Eval rules and agents

- Rules: `prompt-evals`, `ai-safety`, `ai-customer-facing` + always-applied
- Agents: `@agent(AI_OBSERVABILITY)` for runner/metrics; `@agent(AI_SAFETY)` for adversarial case review

### Eval hooks (CI / template repo)

- `validate-prompt-eval-artifacts` — schema validation on `ai-runtime/eval/` suite, baseline, and calibration JSON edits (skips `fixtures/` response maps and `*.schema.json`)
