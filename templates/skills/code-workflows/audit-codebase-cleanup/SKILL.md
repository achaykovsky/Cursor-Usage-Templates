---
name: audit-codebase-cleanup
description: Performs a structured, report-only audit of the codebase for duplication, dead code, redundant files, and legacy logic. Identifies and reports issues without modifying files. Use when the user wants to "clean up the codebase," "find dead code," "detect duplication," or "audit for maintainability."
---

# Audit Codebase Cleanup

Report only. Do not modify any files automatically. Output a structured report the user can act on.

## Workflow

### 1. Detect duplicated code

- **Exact duplicates:** Search for identical or near-identical blocks across files (same or similar sequence of statements, same logic with renamed variables). Use diff, hash of normalized lines, or structural comparison. Note file paths and line ranges.
- **Near-duplicates and copy-paste:** Look for repeated patterns that differ only in names, literals, or minor logic (e.g. similar validation, error handling, or CRUD patterns). Flag with "likely copy-paste" and suggest extraction candidates (e.g. shared helper, constant, or module).
- **Report:** List each duplicate or near-duplicate group: files, approximate line ranges, and a short description (e.g. "same validation block," "repeated error-handling pattern"). Group by similarity so the user can prioritize.

### 2. Identify duplicate or redundant files and folders

- **Duplicate files:** Same or almost identical file content in different paths (e.g. copied module, backup, or alternate location). Compare by content hash or normalized content; ignore trivial differences (comments, formatting) if the logic is the same.
- **Redundant folders:** Empty or nearly empty dirs; dirs that only re-export or wrap a single other module; legacy feature folders that are no longer referenced. Cross-check with imports and build/config to see what is actually used.
- **Report:** List duplicate file pairs/groups and redundant folders with paths. For redundant folders, note why they appear unused (no imports, not in build, etc.).

### 3. Detect dead code

- **Unused functions, classes, components, modules:** For each defined symbol (function, class, component, module), search for references (calls, imports, instantiation). Include entry points (main, routes, tests, config). If no reference found outside its definition file (and not exported for public API), flag as potentially unused. Respect dynamic dispatch and string-based references where the project uses them.
- **Unused imports or exports:** List imports that are never used in the file. List exports that are never imported elsewhere. Use static analysis or grep; note false positives (e.g. re-exports for API, side-effect imports).
- **Unreachable logic:** Code after an unconditional return, throw, or exit; branches that are never taken (e.g. condition always false); dead case in a switch. Flag with file and line range.
- **Report:** Group by category (unused symbols, unused imports/exports, unreachable logic). For each item: file, name or range, and brief reason (e.g. "no references found," "code after return").

### 4. Identify legacy or obsolete logic

- **Replaced approaches:** Look for comments, naming, or structure that suggests an old implementation (e.g. "deprecated," "old," "legacy," "TODO remove," "replaced by X"). Cross-check with current architecture or ADRs: is this code still the active path or an obsolete branch?
- **Orphaned code after refactors:** Code that was part of a removed feature or old API (e.g. handlers for removed endpoints, adapters for replaced services). Search for references from current entry points and config.
- **Obsolete patterns:** Conventions or libraries the project has moved away from (e.g. old API client, deprecated API usage). Flag files or blocks that still use them.
- **Report:** List suspected legacy items with file, location, and why it looks obsolete (comment, no references, or mismatch with current design). Distinguish "likely legacy" from "confirmed unused" where possible.

### 5. Produce the final report

- **Structure:** Use clear sections: Duplicated code, Duplicate/redundant files and folders, Dead code (unused symbols, unused imports/exports, unreachable), Legacy/obsolete logic. Within each, list items with file paths and line references.
- **Prioritization:** Optionally tag items by impact (e.g. high: exact duplicates and unused large modules; medium: near-duplicates and unused exports; low: unused imports and small unreachable blocks). Do not modify the codebase; only suggest order of work.
- **Caveats:** Note limitations (e.g. dynamic imports, reflection, or string-based references may cause false positives for "unused"). Recommend manual review before removal.

## Notes

- Stay tech-agnostic where possible: use search, diff, and reference resolution; adapt to the project's language and structure (entry points, public API surface).
- If the codebase is large, scope by directory or module and report that scope; or produce a summary with representative examples and counts.
- Apply **redact-sensitive-in-output** (shared-practices) if the report is shared or pasted elsewhere.
