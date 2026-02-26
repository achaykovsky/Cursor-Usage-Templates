# Cursor Usage Templates

Centralized Markdown templates for Cursor instructions at multiple scopes: base templates, subagents, rules, hooks, and skills. Sync into `.cursor/` for any project.

## Quick Start

1. **Sync Cursor config** into your project:
   ```powershell
   .\templates\commands\sync-cursor.ps1
   ```
   Copies agents, rules, hooks, and skills from `templates/` to `.cursor/`.

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
| `templates/hooks/hooks.json` | `.cursor/hooks.json` |
| `templates/hooks/scripts/*.ps1` | `.cursor/hooks/scripts/` |
| `templates/skills/**/SKILL.md` | `.cursor/skills/**/` |

See `templates/commands/README.md` for global use (submodule, symlink, `-ProjectRoot`).

## Base Templates

- **`templates/workspace.md`** – Organization-wide rules, tooling, testing policy
- **`templates/project.md`** – Project-specific standards, architecture patterns
- **`templates/user.md`** – Personal coding style, tool preferences

## Subagents

Subagents live in `templates/agents/subagents/` and sync to `.cursor/agents/`. They appear in **Settings > Subagents**. Invoke via `@agent(NAME)`.

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
| FRONTEND | frontend_engineer.md | React/TypeScript, UX |
| BACKEND_GO | backend_go_engineer.md | Go backend |
| BACKEND_PYTHON | backend_python_engineer.md | FastAPI/Django, async |
| PERFORMANCE | performance_engineer.md | Profiling, optimization |
| DATA_ENGINEER | data_engineer.md | ETL/ELT, pipelines |

See `templates/agents/subagents/AGENTS.md` for full descriptions and `AGENTS_USAGE.md` for examples.

## Rules

Rules in `templates/rules/*.mdc` sync to `.cursor/rules/` and apply via globs (e.g. `**/*.py` → `python-backend.mdc`). `security.mdc` is always applied.

## Hooks

`templates/hooks/` provides lifecycle hooks (format-after-edit, block-destructive-shell, etc.). See `templates/prompts/plan-cursor-hooks.md` for setup.

## Skills

Skills in `templates/skills/**/SKILL.md` sync to `.cursor/skills/`. The agent uses them when relevant workflows are triggered (e.g. "update the docs" → keep-docs-in-sync-with-code).

## Project Structure

```
templates/
├── workspace.md
├── project.md
├── user.md
├── commands/
│   ├── README.md
│   └── sync-cursor.ps1
├── agents/
│   └── subagents/           # .cursor/agents/
│       ├── AGENTS.md
│       ├── AGENTS_USAGE.md
│       ├── product_manager.md
│       └── ...
├── rules/                   # .cursor/rules/
│   ├── security.mdc
│   ├── python-backend.mdc
│   └── ...
├── hooks/                   # .cursor/hooks.json + hooks/scripts/
│   ├── hooks.json
│   └── scripts/*.ps1
├── skills/                  # .cursor/skills/
│   └── **/SKILL.md
└── prompts/
    ├── plan-cursor-hooks.md
    └── plan-cursor-activity-logging.md
```

## Troubleshooting

**Subagents not recognized:** Run `sync-cursor.ps1`. Ensure files exist in `templates/agents/subagents/` or `%USERPROFILE%\.cursor\agents\`.

**Template conflicts:** `user.md` = global; `project.md` = project-only; `workspace.md` = org-wide.
