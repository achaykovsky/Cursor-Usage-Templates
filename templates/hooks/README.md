# Hooks Template Mapping

**User guide:** [HOOKS_USAGE.md](HOOKS_USAGE.md) | **Hub:** [USAGE.md](../USAGE.md)

`templates/hooks/hooks.json` and `templates/hooks/hooks.unix.json` intentionally reference commands under `.cursor/hooks/scripts/*`.

Why:
- `templates/hooks/windows/*.ps1` and `templates/hooks/unix/*.sh` are source templates.
- `templates/commands/sync-cursor.py` flattens and copies those scripts into `.cursor/hooks/scripts/`.
- The runtime hook config in `.cursor/hooks.json` must reference `.cursor/hooks/scripts/*`.

This means the command paths in template hook JSON files describe the post-sync runtime location, not the template source location.

### Global hooks (`~/.cursor/hooks.json`)

When syncing with `sync-cursor.py --mode TemplatesToGlobal` or `ToGlobal`, a platform-specific global manifest is installed with **absolute** script paths:

| OS | Template | Path placeholder |
|----|----------|------------------|
| Windows | `hooks.global.windows.json` | `%USERPROFILE%\.cursor\hooks\scripts\` |
| macOS/Linux | `hooks.global.unix.json` | `$HOME/.cursor/hooks/scripts/` |

That avoids hook failures when the Cursor workspace root is not a git repo (for example `empty-window`).

Project `.cursor/hooks.json` keeps **relative** `.cursor/hooks/scripts/*` paths; open the repo root as the workspace (or use `move_agent_to_root`).

### Script contract (`hook-common.ps1`)

Windows hook scripts should dot-source `hook-common.ps1` from `$PSScriptRoot` (informational hooks may omit gated JSON helpers):

- Wrap logic in `try/catch`; log errors to **stderr** only.
- Gated hooks must print **one** JSON line on stdout (`permission` / `continue`).
- On failure, fail open with `{"permission":"allow"}` or `{"continue":true,"permission":"allow"}`.

Additional MCP safety hook:
- `validate-mcp-operations` is mapped to `beforeMCPExecution` in `hooks.json` and `hooks.unix.json`.
- It allows read-oriented MCP tools by default and asks for confirmation on state-changing tools.

Additional DB shell safety hook:
- `validate-db-shell-operations` is mapped to `beforeShellExecution` in `hooks.json` and `hooks.unix.json`.
- It denies clearly destructive DB commands and asks for confirmation on write/schema migration commands.
