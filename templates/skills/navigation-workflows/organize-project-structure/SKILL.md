---
name: organize-project-structure
description: Assesses current project layout, proposes a target structure aligned with conventions and best practices, and plans incremental reorganization. Use when the user wants to "organize the project," "restructure the codebase," "improve folder layout," or "where should X go."
---

# Organize Project Structure

## Workflow

### 1. Assess current structure

- **Map layout:** List top-level dirs and key subdirs with their roles (e.g. `src/`, `api/`, `tests/`, `config/`). Note any conventions already in use (e.g. feature-based vs layer-based).
- **Identify issues:** Scattered modules, inconsistent naming, unclear boundaries, mixed concerns (e.g. API handlers in domain code), orphaned or misplaced files. Cross-reference with `explain-codebase-structure` if needed.
- **Check constraints:** Build config, imports, entry points, package boundaries. Note what must stay stable (public API, config paths, CLI).

### 2. Propose target structure

- **Choose a pattern:** Layer-based (domain, application, infrastructure), feature-based (by feature/domain), or hybrid. Align with project size, team, and existing patterns.
- **Define layout:** Concrete directory tree with rationale for each major dir. Include:
  - Where to put new code (handlers, services, models, tests)
  - Config, scripts, docs placement
  - Any shared vs feature-specific boundaries
- **Document conventions:** Naming (e.g. `snake_case` vs `PascalCase`), file-per-module vs module-per-dir, where tests live (colocated vs `tests/`).

### 3. Plan migration

- **Prioritize:** Group by impact. Low-risk first (e.g. move empty dirs, consolidate config); then medium (move isolated modules); high last (split coupled modules).
- **Order:** Dependencies first. If A imports B, move B before A. Avoid circular refs.
- **Steps:** One logical move per step. Each step should leave the project buildable and tests passing.

### 4. Execute or report

- **Report-only:** Output a structured plan (current → target layout, ordered steps, rationale). User can act manually.
- **Execute:** If user confirms, apply moves incrementally. For each move:
  - Update imports and references
  - Update build/config if needed
  - Run tests; fix if broken
  - Commit or stage atomically

## Notes

- Apply **refactor-safely** principles when executing moves: impact analysis, test coverage, incremental steps.
- Apply **suggest-commands-dont-run-destructive** for mass moves or git operations; prefer suggesting commands over running them unless user explicitly requests.
- For large projects, scope by directory or module; produce a phased plan.
- Respect project-specific conventions (e.g. monorepo layout, framework defaults) over generic advice.
