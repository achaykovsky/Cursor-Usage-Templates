---
name: save-tokens-in-context
description: Reduces Cursor/context token use via concise prompts, file references instead of pastes, dense replies, and minimal code echo. Use when the user cares about cost, long chats, or "save tokens" / "be concise" / "don't repeat code."
---

# Save Tokens in Context

Apply these habits so prompts, tool traces, and replies stay small without hiding needed detail.

## For the user (prompt side)

- Prefer `@path` / `@symbol` over pasting hundreds of lines; add line numbers only when the model must see exact text.
- One primary goal per message; split huge refactors across turns with clear checkpoints.
- Paste errors as text (message + relevant stack frame), not screenshots of logs.
- Say "summary only" or "no full file" when a short answer is enough.

## For the agent (behavior)

- **Answer first**, then supporting detail. Avoid preambles ("Here is…", "I'll help you…").
- **Cite** existing code with line-range references; do not reproduce whole files.
- **Batch** tool calls (parallel reads/searches) instead of sequential one-liners when independent.
- **Skip** re-reading files already in the active context unless invalidated.
- **Truncate** long listings in replies; point to paths and grep patterns for the rest.

## When this conflicts with quality

If brevity would skip safety (security, data loss, breaking changes), prioritize correctness and state the tradeoff in one line.
