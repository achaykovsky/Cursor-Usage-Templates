---
name: add-comments-to-code
description: Adds mandatory inline comments and docstrings explaining why, invariants, and non-obvious logic when writing or editing code. Use when the user asks to "add comments," "document this code," "explain this function," or when shipping new or materially changed logic per ai-guardrails.
---

# Add Comments to Code

## Workflow

1. **Decide what needs a comment**
   - **Required:** Complex branches, regex/math, algorithms, business rules, invariants, non-obvious side effects, workarounds, security/perf tradeoffs.
   - **Required at boundaries:** Public APIs, modules, and non-trivial functions — add a one-line summary plus params/returns where the language supports it (docstring, JSDoc, Go doc comment).
   - **Skip:** Trivial one-liners (imports, simple getters), self-explanatory names, or restating obvious syntax.

2. **Write why, not what**
   - Explain intent, constraints, and rejected alternatives — not a line-by-line narration.
   - Document invariants the code assumes (e.g. "caller holds lock", "ids are unique per tenant").
   - Link decisions to tickets/ADRs when relevant: `TODO(PROJ-123): remove after v2 migration`.

3. **Match project style**
   - Follow existing comment tone, language (`#`, `//`, `/* */`), and docstring format in the file.
   - Python: module docstring + public function docstrings; type hints carry *what*, comments carry *why*.
   - Go: package and exported symbol doc comments.
   - TS/JS: JSDoc on exported functions/types when behavior is not obvious from types alone.

4. **Pair with logging and error handling when authoring**
   - Comments explain static intent; logs capture runtime flow. When adding substantial logic, also apply **add-logging-to-code** (code-workflows) at boundaries and error paths.
   - When adding raise/except or domain error types, apply **add-error-handling-to-code** (code-workflows).

5. **Review before finishing**
   - Every new non-trivial function/block has at least one comment or docstring if a reader would ask "why?".
   - No stale comments contradicting the code; update or remove outdated notes in the same diff.

## Anti-patterns

- **Narrating the obvious:** `# increment i` above `i += 1`.
- **Comment instead of name:** Prefer a clear identifier; comment only what the name cannot carry.
- **Secrets in comments:** No credentials, tokens, or raw PII — same redaction rules as logs (**redact-sensitive-in-output**).
- **Large commented-out blocks:** Delete dead code; use git history instead.

## Notes

- Policy baseline: `documentation.mdc` (code comments) and `ai-guardrails.mdc` (mandatory on new/edited code).
- For README, ADRs, and external docs — use **keep-docs-in-sync-with-code** (docs-workflows), not inline comments alone.
- For structured runtime telemetry — use **add-logging-to-code** (code-workflows).
