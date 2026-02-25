---
name: refactor-safely
description: Plans and executes refactors with impact analysis, test-coverage check, incremental steps, and regression verification. Use when the user requests a refactor, rename, or "clean up without breaking."
---

# Refactor Safely

## Workflow

1. **Define scope and goal**
   - Clarify what is being refactored (e.g. rename symbol, extract function, restructure module) and the desired outcome (readability, reuse, reduce coupling). Avoid scope creep.

2. **Impact analysis**
   - Find all references to the target: same file, other files, tests, config, docs. Use search/grep and (if applicable) IDE rename or symbol search.
   - List call sites, imports, and any external contracts (API names, env vars, CLI flags) that must stay stable or be migrated explicitly.

3. **Check test coverage**
   - Ensure the area under refactor is covered by tests. If not, add minimal tests for current behavior before changing it, so regressions are detectable.
   - Run the relevant test suite and note baseline: all green before refactor.

4. **Execute incrementally**
   - Prefer small, reviewable steps: one rename, one extraction, one file move. Each step should leave the project in a working state (tests pass, build succeeds).
   - For renames: update definition and all references in one logical change. For extractions: introduce new function/module, then replace call sites, then remove old code.
   - Avoid mixing refactor with new features or bug fixes; commit or stage refactor steps separately if the user is using version control.

5. **Verify no regression**
   - After each step (or at the end): run the full test suite and any build/lint steps. Fix any new failures before proceeding or report pre-existing failures.
   - If the refactor touches public API or config, note any migration needed for callers or deployment.

## Notes

- If the refactor is large, propose a short plan (ordered steps) and get user confirmation before making many edits.
- Preserve behavior: refactor should not change observable outcomes; only structure, names, or organization.
