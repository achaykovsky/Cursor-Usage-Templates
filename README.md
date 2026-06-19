# Cursor Usage Templates

Centralized Markdown templates for Cursor instructions at multiple scopes: base templates, subagents, rules, hooks, and skills. Sync into `.cursor/` for any project.

**Navigation:** Start at [`templates/USAGE.md`](templates/USAGE.md) (syncs to `.cursor/USAGE.md`). Templates index: [`templates/README.md`](templates/README.md).

## Quick Start

### A. Publish templates to global (from this repo)

```bash
python templates/commands/sync-cursor.py --mode TemplatesToGlobal
```

### B. Initialize any project from global

```bash
python %USERPROFILE%\cursor\Cursor-Usage-Templates\templates\commands\sync-cursor.py --mode FromGlobal --project-root .
```

Then open **`project/.cursor/USAGE.md`**.

### C. Sync templates directly into a project

1. **Sync Cursor config** into your project (requires **Python 3.10+** on `PATH`):
   ```bash
   python templates/commands/sync-cursor.py
   ```
   On Windows you can also run `.\templates\commands\sync-cursor.ps1` (it calls the same script). Copies agents, rules, hooks, and skills from `templates/` to `.cursor/`. **Hooks:** default sync uses PowerShell on Windows and bash on macOS/Linux (`--hooks-variant auto`). See `templates/commands/README.md` for OS prerequisites (`pwsh`, `jq`, etc.).
   If you run sync from a central templates repo in another project, use the global path:
   `& "$env:USERPROFILE\cursor\Cursor-Usage-Templates\templates\commands\sync-cursor.ps1" -Mode FromGlobal`

2. **Copy base templates** into your Cursor instructions panel:
   - `templates/workspace.md` – organization-wide rules
   - `templates/project.md` – project-specific objectives
   - `templates/user.md` – personal preferences

3. **Invoke subagents** in Chat or Composer via `@agent(NAME)`:
   ```
   @agent(REVIEWER) review this function
   @agent(PM) break down this feature into tasks
   ```

4. **Replace placeholders** in templates with concrete details.

## What Gets Synced

| Source | Destination |
|--------|-------------|
| `templates/agents/subagents/*.md` | `.cursor/agents/` |
| `templates/rules/*.mdc` | `.cursor/rules/` |
| `templates/hooks/hooks.json` or `hooks.unix.json` (see sync `--hooks-variant`) | `.cursor/hooks.json` |
| `templates/hooks/windows/*.ps1` or `templates/hooks/unix/*.sh` | `.cursor/hooks/scripts/` (flat; OS only) |
| `templates/skills/**/SKILL.md` | `.cursor/skills/**/` |
| `templates/USAGE.md`, `rules/RULES.md`, `skills/SKILLS.md`, `hooks/HOOKS_USAGE.md`, `hooks/README.md`, `prompts/*.md` | `.cursor/` (same relative paths) |

See `templates/commands/README.md` for global use (submodule, symlink, `--project-root`) and OS-specific hook dependencies.

## Base Templates

- **`templates/workspace.md`** – Organization-wide rules, tooling, testing policy
- **`templates/project.md`** – Project-specific standards, architecture patterns
- **`templates/user.md`** – Personal coding style, tool preferences

## Subagents

Subagents live in `templates/agents/subagents/` and sync to `.cursor/agents/`. They appear in **Settings > Subagents**. Invoke via `@agent(NAME)`.

### Core + Platform Agents

| Invoke | File | Purpose |
|--------|------|---------|
| PM | product_manager.md | Task breakdown, planning, specs |
| REVIEWER | code_reviewer.md | Code quality, maintainability |
| TESTER | test_engineer.md | Test generation, pytest |
| DOCS | documentation_writer.md | API docs, README, architecture |
| SECURITY | security_engineer.md | Vulnerabilities, compliance |
| ARCHITECT | architecture_advisor.md | System design, scalability |
| DEVOPS | devops_engineer.md | CI/CD, Docker, monitoring |
| DATABASE_SQL | sql_database_engineer.md | Schema, migrations, queries |
| DATABASE_NOSQL | nosql_database_engineer.md | MongoDB, DynamoDB, Cassandra |
| BACKEND_GO | backend_go_engineer.md | Go backend |
| BACKEND_PYTHON | backend_python_engineer.md | FastAPI/Django, async |
| PERFORMANCE | performance_engineer.md | Profiling, optimization |
| DATA_ENGINEER | data_engineer.md | ETL/ELT, pipelines |
| INCIDENT | incident_responder.md | Debugging, incidents, RCA |

### Frontend Agents

| Invoke | File | Purpose |
|--------|------|---------|
| FE_UI_ENGINEER | fe_ui_engineer.md | Frontend UI implementation |
| FE_UX_DESIGN | fe_ux_design.md | Frontend UX flows and behavior |
| FE_DESIGN_SYSTEM | fe_design_system.md | Frontend design system consistency |
| FE_STATE_ENGINEER | fe_state_engineer.md | Frontend state and caching strategy |
| FE_TEST_ENGINEER | fe_test_engineer.md | Frontend test coverage and regressions |
| FE_CODE_REVIEWER | fe_code_reviewer.md | Frontend-focused code review and regression risk detection |
| FE_ACCESSIBILITY_ENGINEER | fe_accessibility_engineer.md | Frontend accessibility and WCAG checks |
| FE_PERFORMANCE_ENGINEER | fe_performance_engineer.md | Frontend Core Web Vitals and runtime performance |

See [`templates/agents/subagents/AGENTS.md`](templates/agents/subagents/AGENTS.md) and [`templates/USAGE.md`](templates/USAGE.md) for routing.

Frontend agents are FE-prefixed (`FE_*`) and backend agents are BE/domain-prefixed (`BACKEND_*`, `DATABASE_*`) to keep boundaries explicit.

## Rules

Rules sync to `.cursor/rules/`. Catalog: [`templates/rules/RULES.md`](templates/rules/RULES.md).

## Hooks

User guide: [`templates/hooks/HOOKS_USAGE.md`](templates/hooks/HOOKS_USAGE.md). Extend: [`templates/prompts/plan-cursor-hooks.md`](templates/prompts/plan-cursor-hooks.md).

## MCP Integrations

Recommended MCP servers for this template set:
- GitHub MCP (PR/issues/checks/release evidence)
- Linear or Jira MCP (planning/release blocker tracking)
- Sentry MCP (incident/performance traces and errors)
- Docs MCP such as Confluence/Notion/internal KB (doc/spec synchronization)
- Database MCP in read-only mode (schema/state validation)

Policy:
- Read-only MCP calls are default.
- State-changing MCP actions require explicit user request/approval.

## Skills

Catalog: [`templates/skills/SKILLS.md`](templates/skills/SKILLS.md). Policy: [`templates/USAGE.md`](templates/USAGE.md).

## Project Structure

```
templates/
├── README.md                # Templates folder entry + 3-hop workflow
├── USAGE.md                 # → .cursor/USAGE.md (start here after sync)
├── workspace.md
├── project.md
├── user.md
├── commands/
│   ├── README.md
│   ├── sync-cursor.py
│   └── sync-cursor.ps1
├── agents/
│   └── subagents/           # .cursor/agents/
│       ├── AGENTS.md
│       ├── AGENTS_USAGE.md
│       ├── product_manager.md
│       └── ...
├── rules/                   # .cursor/rules/
│   ├── RULES.md
│   └── *.mdc
├── hooks/                   # .cursor/hooks.json + hooks/scripts/
│   ├── HOOKS_USAGE.md
│   ├── hooks.json
│   ├── hooks.unix.json
│   ├── windows/*.ps1
│   └── unix/*.sh
├── skills/                  # .cursor/skills/
│   ├── SKILLS.md
│   └── **/SKILL.md
├── mcp/
│   └── README.md            # recommended MCP servers and safety defaults
└── prompts/                 # .cursor/prompts/ (planning prompts)
    └── *.md
```

## Troubleshooting

**Subagents not recognized:** Run `python templates/commands/sync-cursor.py`. Ensure files exist in `templates/agents/subagents/` or `~/.cursor/agents/` (Windows: `%USERPROFILE%\.cursor\agents\`).

**Template conflicts:** `user.md` = global; `project.md` = project-only; `workspace.md` = org-wide.
