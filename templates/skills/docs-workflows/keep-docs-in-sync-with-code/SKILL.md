---
name: keep-docs-in-sync-with-code
description: After code or config changes, finds affected docs (README, ADRs, comments), updates or flags outdated sections, and preserves examples and accuracy. Use after a significant code change or when the user asks to "update the docs."
---

# Keep Docs in Sync with Code

## Workflow

1. **Identify the change scope**
   - From the recent code or config change: list modified APIs (functions, classes, endpoints), config keys, CLI flags, file paths, or behavior that users or other devs rely on.
   - Note anything that is part of the "public" surface: exported symbols, HTTP routes, env vars, config options.

2. **Find affected docs**
   - Search for references to the changed names and concepts: README, CONTRIBUTING, docs/ folder, ADRs, inline comments and docstrings, and example snippets in docs.
   - Prioritize: user-facing README and getting-started first, then API/design docs, then internal notes.

3. **Update or flag**
   - **Update:** If a doc describes old behavior, names, or examples, change it to match the code. Update code samples so they run (correct imports, paths, flags). Bump "last updated" or version in docs if the project uses that.
   - **Flag:** If a section is obsolete but rewriting is out of scope, add a short note (e.g. "Deprecated: see X" or "As of v2, ...") rather than leaving it misleading.
   - Preserve intent: keep the doc's structure and audience; only fix accuracy and examples.

4. **Verify examples**
   - If docs contain runnable examples (code blocks, curl, commands): check that they still match the codebase and run (or note any required env/setup). Fix or remove broken examples.

5. **Summarize**
   - List the files you changed or flagged and what was updated (e.g. "README: install command and env vars; docs/api.md: endpoint path and response example").

## Notes

- Prefer minimal edits: change only what the code change invalidates. Avoid rewriting for style unless the user asks.
- Apply **redact-sensitive-in-output** (shared-practices) when updating docs or examples.
