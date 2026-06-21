---
name: save-tokens-in-context
description: Reduces Cursor/context token use via concise prompts, file references instead of pastes, dense replies, and minimal code echo. Use when the user cares about cost, long chats, or "save tokens" / "be concise" / "don't repeat code."
---

# Save Tokens in Context

Apply **`token-efficiency.mdc`** first (inputs, tool use, replies, code citations, scope). This skill adds only what the rule does not cover.

## Workflow

### User (prompt side)

- Paste errors as **text** (message + relevant stack frame), not screenshots of logs.
- Say **"summary only"** or **"no full file"** when a short answer is enough.
- Split huge refactors across turns with explicit checkpoints (one primary goal per message).

### Agent (behavior)

- For long listings in replies, **truncate** and point to paths plus grep patterns instead of enumerating every match.

### When brevity conflicts with quality

If being concise would skip safety (security, data loss, breaking changes), prioritize correctness and state the tradeoff in one line.

## Notes

- Pair with **route-task-to-model** when choosing a cheaper model tier for routine edits.
