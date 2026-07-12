---
name: add-prompt-injection-defenses
description: Adds prompt injection and jailbreak defenses for customer-facing bots — input boundaries, delimiter strategy, tool arg validation. Use when hardening untrusted user input paths.
---

# Add Prompt Injection Defenses

## Workflow

1. **Boundary** — fixed system prompt; user content in delimited blocks with max length.
2. **Instruction hierarchy** — system policy cannot be overridden by user text.
3. **Tool args** — JSON Schema / Pydantic validation; reject overlong or extra fields.
4. **Retrieval** — sanitize RAG chunks; no executable content in context.
5. **Detection** — log suspected injection; policy mode `ask` or `deny` per severity.
6. **Tests** — red-team cases (ignore instructions, role-play admin, encoded payloads).
7. **Export** — add cases to `ai-runtime/eval/adversarial/<bot>-injection.json`; see [adversarial/README.md](../../../ai-runtime/eval/adversarial/README.md). Validate with `validate_bot_runtime.py prompt-eval`.

## Output Contract

- Defense checklist with file paths changed
- Test cases (pass/fail expectations)
- Policy rule IDs added, if any

## Notes

- Follow [input-sanitization.md](../../../ai-runtime/guardrails/input-sanitization.md).
- Pair with `@agent(AI_SAFETY)` and `design-prompt-evals` for adversarial suite coverage.
