# sync-cursor.ps1

Syncs Cursor config (agents, rules, hooks, skills) from `templates/` into `.cursor/` for the current project.

## What It Syncs

| Source | Destination |
|-------|-------------|
| `templates/agents/subagents/*.md` | `.cursor/agents/` |
| `templates/rules/*.mdc` | `.cursor/rules/` |
| `templates/hooks/hooks.json` | `.cursor/hooks.json` |
| `templates/hooks/scripts/*.ps1` | `.cursor/hooks/scripts/` |
| `templates/skills/**/SKILL.md` | `.cursor/skills/**/` |

**Fallback:** If `templates/agents/subagents/` is missing, uses `%USERPROFILE%\.cursor\agents\` for agents.

## Usage

**From a project that contains this repo:**
```powershell
.\templates\commands\sync-cursor.ps1
```

**From the repo root:**
```powershell
.\templates\commands\sync-cursor.ps1
```

The script infers the project root from its own path (`templates/commands/` → parent of `templates/`).

## Global Use Across Cursor Projects

Use this script from a central templates repo so any project can sync Cursor config without embedding templates.

### Option A: Clone Once, Symlink or Copy

1. Clone this repo to a fixed location, e.g. `%USERPROFILE%\cursor\Cursor-Usage-Templates`
2. In each project, either:
   - **Symlink:** `mklink /D templates ..\Cursor-Usage-Templates\templates`
   - **Or** add the repo as a submodule: `git submodule add <repo-url> templates`
3. Run `.\templates\commands\sync-cursor.ps1` from the project root

### Option B: Global Script with -ProjectRoot

1. Clone this repo to `%USERPROFILE%\.cursor\Cursor-Usage-Templates`
2. From any project directory, run:
   ```powershell
   & "$env:USERPROFILE\.cursor\Cursor-Usage-Templates\templates\commands\sync-cursor.ps1" -ProjectRoot $PWD.Path
   ```
3. Or add to a PATH script: `sync-cursor.ps1` that runs the above with `(Get-Location)` as `-ProjectRoot`.

### Option C: Project Root Detection

The script accepts `-ProjectRoot` to sync into a different directory. When run without it, uses the parent of `templates/` (repo root) as the project.

**Recommended:** Use Option A with a submodule or symlink so each project explicitly opts in and the script path stays correct.

## Requirements

- PowerShell 5.1+ or PowerShell Core (pwsh)
- Windows (paths use `%USERPROFILE%`; adapt for macOS/Linux)

## After Sync

- **Agents** appear in Cursor Settings → Subagents
- **Rules** apply via globs when editing matching files
- **Hooks** run at lifecycle events (see `templates/prompts/plan-cursor-hooks.md`)
- **Skills** are available to the agent when relevant workflows are triggered
