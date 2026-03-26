# Plan: More Precise Cursor Activity Logging

**Goal:** Log Cursor actions so we can answer: *Which files were changed? Why? After which prompt?*

---

## Current State

### What We Log Today
- Raw payload dump per event (beforeSubmitPrompt, afterFileEdit, beforeShellExecution, stop)
- Fields: prompt, workspace_roots, ts, event, plus whatever Cursor sends
- **Issues:**
  - Some entries have `event: null` (payload may omit `hook_event_name` in some cases)
  - No explicit correlation between prompt → edits
  - Full `edits` (old_string, new_string) can be huge; hard to scan
  - No summary view: "prompt X led to changes in files A, B, C"

### What Cursor Provides (per event)

| Event | Key Fields | Correlation |
|-------|------------|-------------|
| **beforeSubmitPrompt** | `prompt`, `conversation_id`, `generation_id`, `attachments` | Start of a "generation" |
| **afterFileEdit** | `file_path`, `edits` (old_string, new_string), `conversation_id`, `generation_id` | Same `generation_id` as the prompt that triggered it |
| **beforeShellExecution** | `command`, `cwd`, `conversation_id`, `generation_id` | Same generation |
| **stop** | `status` (completed/aborted/error), `conversation_id`, `generation_id` | End of generation |

**Key insight:** `conversation_id` + `generation_id` link all events. One prompt → one generation → N file edits, M shell commands.

---

## Constraints

- **Hooks do NOT receive:** LLM reasoning, "why" explanations, or agent intent
- **"Why" = the prompt:** The user prompt is the closest we get to "why"
- **No cross-invocation state:** Each hook run is independent; we cannot keep in-memory session state

---

## Proposed Changes

### 1. Normalize Event Handling
- Always set `event` from `payload.hook_event_name`; if missing, infer from payload shape (e.g. has `file_path` + `edits` → afterFileEdit)
- Ensure `conversation_id` and `generation_id` are always logged when present

### 2. Structured Log Format (per event type)

**beforeSubmitPrompt:**
```json
{
  "ts": "ISO8601",
  "event": "beforeSubmitPrompt",
  "conversation_id": "...",
  "generation_id": "...",
  "prompt": "user prompt (truncated if needed)",
  "prompt_length": 123,
  "attachments": [{"type":"file","file_path":"..."}]
}
```

**afterFileEdit:**
```json
{
  "ts": "ISO8601",
  "event": "afterFileEdit",
  "conversation_id": "...",
  "generation_id": "...",
  "file_path": "path/to/file.py",
  "edit_count": 2,
  "edit_summary": [
    {"old_preview": "first 80 chars...", "new_preview": "first 80 chars...", "lines_changed": "+3,-1"}
  ],
  "edits_full": "..." // optional: keep full diff for small edits; truncate for large
}
```

**beforeShellExecution:**
```json
{
  "ts": "ISO8601",
  "event": "beforeShellExecution",
  "conversation_id": "...",
  "generation_id": "...",
  "command": "git status",
  "cwd": "/path/to/project"
}
```

**stop:**
```json
{
  "ts": "ISO8601",
  "event": "stop",
  "conversation_id": "...",
  "generation_id": "...",
  "status": "completed"
}
```

### 3. Add "Why" and "Which Files" Correlation

- **Which files:** `afterFileEdit` already has `file_path`; add `edit_count` and optional `edit_summary`
- **Why:** The prompt from `beforeSubmitPrompt` with the same `generation_id`
- **After which prompt:** Group by `generation_id`; prompt is the first event, edits follow

**Query pattern:** For generation_id X:
1. Find `beforeSubmitPrompt` with generation_id=X → that's the "why"
2. Find all `afterFileEdit` with generation_id=X → those are "which files"

### 4. Session Summary (optional, at `stop`)

At `stop`, we could emit a **summary line** that aggregates the generation. Options:

- **A. Re-read same log file:** At stop, grep the log for this generation_id, aggregate, write summary line. Risk: race if multiple hooks run concurrently.
- **B. Separate summary file:** `cursor-session-YYYY-MM-DD.json` with one object per generation: `{generation_id, prompt_preview, files_changed[], commands_run[], status}`. Append at stop.
- **C. No summary, query on read:** Keep raw events; provide a small script `.\templates\commands\query-cursor-logs.ps1` that reads the JSONL and outputs "prompt X → files A, B, C" for a given date or generation.

**Recommendation:** Start with C. Simpler, no new files, no race conditions. Add B later if needed.

### 5. Edit Content Handling

- **Full diff:** Keep for edits under ~2KB total (old_string + new_string). Above that, truncate.
- **Summary:** Always add `edit_summary`: array of `{old_preview, new_preview}` (first 80 chars of each) for quick scanning
- **Sensitive data:** Apply redact-sensitive-in-output: never log full content of `.env`, `*.pem`, etc. Redact or skip.

### 6. Implementation Order

| Step | Task | Effort |
|------|------|--------|
| 1 | Fix event handling (never null) | Small |
| 2 | Always log conversation_id, generation_id | Small |
| 3 | For afterFileEdit: add edit_count, edit_summary; truncate large edits | Medium |
| 4 | Normalize output structure per event type (drop noisy fields) | Medium |
| 5 | Add query script: `query-cursor-logs.ps1 -Date 2026-02-25` → prompt → files | Medium |
| 6 | (Optional) Session summary at stop | Medium |

---

## Output Example (after changes)

**Log file (cursor-activity-2026-02-25.jsonl):**
```
{"ts":"2026-02-25T20:11:35Z","event":"beforeSubmitPrompt","conversation_id":"abc","generation_id":"gen1","prompt":"Add logging to the auth module","prompt_length":32}
{"ts":"2026-02-25T20:11:42Z","event":"afterFileEdit","conversation_id":"abc","generation_id":"gen1","file_path":"src/auth/login.py","edit_count":1,"edit_summary":[{"old_preview":"def login(...)","new_preview":"def login(...)\n    logger.info(...)"}]}
{"ts":"2026-02-25T20:11:43Z","event":"afterFileEdit","conversation_id":"abc","generation_id":"gen1","file_path":"src/auth/__init__.py","edit_count":1,"edit_summary":[{"old_preview":"","new_preview":"from .login import login"}]}
{"ts":"2026-02-25T20:11:50Z","event":"stop","conversation_id":"abc","generation_id":"gen1","status":"completed"}
```

**Query output (`query-cursor-logs.ps1 -Date 2026-02-25`):**
```
Generation gen1 (2026-02-25 20:11:35)
  Prompt: Add logging to the auth module
  Files changed: src/auth/login.py, src/auth/__init__.py
  Status: completed
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `templates/hooks/scripts/log-cursor-activity.ps1` | Event normalization, structured output per event, edit summary, truncation |
| `.cursor/hooks/scripts/log-cursor-activity.ps1` | Same (after sync) |
| `templates/commands/query-cursor-logs.ps1` | New: read JSONL, group by generation_id, output prompt → files |
| `templates/prompts/plan-cursor-hooks.md` | Update log hook description |
| `templates/commands/README.md` | Document query script |

---

## Open Questions

1. **Full diff vs summary only:** Keep full `edits` in log for audit, or drop to reduce size? (Recommend: keep for small edits, truncate for large)
2. **Redaction:** Should we redact `prompt` if it contains secrets? (Recommend: apply redact-sensitive-in-output patterns)
3. **beforeReadFile:** Not currently logged. Add for "which files were read"? (Lower priority; can add later)
