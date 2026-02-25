---
name: explain-and-navigate-git-history
description: Answers "why is this here," "when did X change," or "who touched this" by inspecting history, blame, and log; summarizes findings. Use when the user asks about history, blame, or reasoning behind code.
---

# Explain and Navigate Git History

## Workflow

1. **Clarify the question**
   - What does the user want? (e.g. why a line exists, when something changed, who last modified a file, what commits touched a path.)
   - Identify the target: file, directory, or symbol/line range.

2. **Inspect history**
   - Use `git log`, `git blame`, or `git log -p` as appropriate for the question.
   - For "why": find the commit that introduced the code; read commit message and optionally the diff.
   - For "when": list commits that touched the target with dates and messages.
   - For "who": blame the relevant lines; note author and commit.

3. **Summarize findings**
   - Give a short answer first (e.g. "Introduced in commit X by Y for Z").
   - Include commit hash(es), author(s), and date. Quote or paraphrase the commit message if it explains intent.
   - If the reason is unclear from history, say so and suggest asking the author or checking linked tickets.

## Notes

- Prefer showing commands the user can run (e.g. `git blame file --line 42`) when that is clearer than pasting raw output.
- Do not modify history; read-only use of git.
