# sync-cursor.ps1

Syncs Cursor config (agents, rules, hooks, skills) between **`templates/`**, the project **`.cursor/`**, and the global **`%USERPROFILE%\.cursor\`** directory.

## Modes (`-Mode`)

| Mode | Direction | Use case |
|------|-----------|----------|
| **`TemplatesToLocal`** (default) | `templates/` → project `.cursor/` | Refresh project from repo templates; agents use fallback (see below). |
| **`ToGlobal`** | Project `.cursor/` → `%USERPROFILE%\.cursor\` | Publish this project’s Cursor setup as your user default. |
| **`FromGlobal`** | `%USERPROFILE%\.cursor\` → project `.cursor/` | Pull your global Cursor setup into a repo. |

```powershell
.\templates\commands\sync-cursor.ps1
.\templates\commands\sync-cursor.ps1 -Mode ToGlobal
.\templates\commands\sync-cursor.ps1 -Mode FromGlobal
```

## What Each Mode Syncs

### `TemplatesToLocal` (default)

| Source | Destination |
|--------|-------------|
| `templates/agents/subagents/*.md` or (fallback) `%USERPROFILE%\.cursor\agents\*.md` | `.cursor/agents/` |
| `templates/rules/*.mdc` | `.cursor/rules/` |
| `templates/hooks/hooks.json` | `.cursor/hooks.json` |
| `templates/hooks/scripts/*.ps1` | `.cursor/hooks/scripts/` |
| `templates/skills/**/SKILL.md` | `.cursor/skills/**/` |

**Agent fallback:** If `templates/agents/subagents/` is missing or empty, agents are taken from `%USERPROFILE%\.cursor\agents\` when that folder has `*.md` files.

### `ToGlobal` / `FromGlobal`

Copies between project **`.cursor/`** and **`%USERPROFILE%\.cursor\`**:

| Category | Paths (relative to each Cursor root) |
|----------|--------------------------------------|
| Agents | `agents/*.md` |
| Rules | `rules/*.mdc` |
| Hooks | `hooks.json` at the Cursor root, plus `hooks/scripts/*.ps1` |
| Skills | `skills/**/SKILL.md` (tree preserved) |

For **`ToGlobal`** and **`FromGlobal`**, existing `*.md` in `agents/`, `*.mdc` in `rules/`, and `*.ps1` in `hooks/scripts/` at the **destination** are removed before copy so the destination matches the source set. **`hooks.json`** is overwritten only when the **source** has that file.

## Safety: Empty Sources

If a category has **no files** on the source side (missing folder, or folder with no matching files), that category is **skipped**. The script does **not** clear the destination from an empty source—so you cannot accidentally wipe global or project config by running with missing inputs.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-ProjectRoot` | Parent of `templates/` (inferred from script path) | Root of the project whose `.cursor/` is read or written. |
| `-Mode` | `TemplatesToLocal` | One of `TemplatesToLocal`, `ToGlobal`, `FromGlobal`. |

**`-ProjectRoot`:** When you pass it explicitly, use the full project path you intend (the script does not resolve relative paths with `Resolve-Path`).

## Usage

**From a project that contains `templates/` (e.g. this repo or a submodule/symlink):**

```powershell
.\templates\commands\sync-cursor.ps1
```

**From the repo root:**

```powershell
.\templates\commands\sync-cursor.ps1
```

The script infers project root as the parent of `templates/` (`templates/commands/` → two levels up).

**Push project Cursor config to global:**

```powershell
.\templates\commands\sync-cursor.ps1 -Mode ToGlobal
```

**Pull global Cursor config into the project:**

```powershell
.\templates\commands\sync-cursor.ps1 -Mode FromGlobal
```

## Global Use Across Cursor Projects

Use this script from a central templates repo so any project can sync Cursor config without embedding everything by hand.

### Option A: Clone Once, Symlink or Copy

1. Clone this repo to a fixed location, e.g. `%USERPROFILE%\cursor\Cursor-Usage-Templates`
2. In each project, either:
   - **Symlink:** `mklink /D templates ..\Cursor-Usage-Templates\templates`
   - **Or** add the repo as a submodule: `git submodule add <repo-url> templates`
3. Run `.\templates\commands\sync-cursor.ps1` from the project root (or pass `-ProjectRoot`)

### Option B: Global Script with `-ProjectRoot`

1. Clone this repo to e.g. `%USERPROFILE%\.cursor\Cursor-Usage-Templates`
2. From any project directory:

   ```powershell
   & "$env:USERPROFILE\.cursor\Cursor-Usage-Templates\templates\commands\sync-cursor.ps1" -ProjectRoot $PWD.Path
   ```

3. Add `-Mode ToGlobal` or `-Mode FromGlobal` when syncing with `%USERPROFILE%\.cursor\` instead of templates.

### Option C: Explicit Project Root

Pass `-ProjectRoot` when the script is not under that project’s `templates/commands/` layout.

**Recommended:** Option A with a submodule or symlink so each project opts in and the default `-ProjectRoot` inference stays correct.

## Requirements

- PowerShell 5.1+ or PowerShell Core (`pwsh`)
- Windows-oriented paths (`%USERPROFILE%`); on macOS/Linux set equivalent user config paths or adapt the script.

## After Sync

- **Agents** appear in Cursor Settings → Subagents
- **Rules** apply via globs when editing matching files
- **Hooks** run at lifecycle events (see `templates/prompts/plan-cursor-hooks.md`)
- **Skills** are available to the agent when relevant workflows are triggered
