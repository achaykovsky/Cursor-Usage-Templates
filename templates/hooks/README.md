# Hooks Template Mapping

**User guide:** [HOOKS_USAGE.md](HOOKS_USAGE.md) | **Hub:** [USAGE.md](../USAGE.md) | **Policy engine:** [policy/README.md](policy/README.md)

## Layout

```
templates/hooks/
  manifest/hooks.manifest.yaml   # canonical event → script wiring (edit here)
  manifest/generate_hooks_json.py
  windows/                       # Windows bundle: scripts + hooks JSON
    *.ps1
    hooks.json                   # project .cursor/hooks.json (generated)
    hooks.global.json            # global ~/.cursor/hooks.json (generated)
  unix/                          # Unix bundle: scripts + hooks JSON
    *.sh
    hooks.json
    hooks.global.json
  policy/                        # shared Python policy engine
```

**Flow:** edit `manifest/hooks.manifest.yaml` → run `python templates/hooks/manifest/generate_hooks_json.py` → sync copies the active OS folder's `hooks.json` + scripts into `.cursor/`.

**Template-repo try loop:** `sync-templates-to-local` (`afterFileEdit`) runs `sync-cursor.py --trigger-file` so edits under `templates/` land in `.cursor/` without a manual sync. See [`commands/README.md`](../commands/README.md#auto-sync-on-template-edits-this-repo).

Sync flattens `windows/*.ps1` or `unix/*.sh` into `.cursor/hooks/scripts/` (flat runtime layout). JSON config files stay in the OS template folders and are not copied as scripts.

Regenerate after manifest edits:

```bash
python templates/hooks/manifest/generate_hooks_json.py
python templates/hooks/manifest/generate_hooks_json.py --check   # CI / pre-commit
```

### Global hooks (`~/.cursor/hooks.json`)

When syncing with `sync-cursor.py --mode TemplatesToGlobal`, the platform's `hooks.global.json` is installed with **absolute** script paths:

| OS | Source | Path placeholder |
|----|--------|------------------|
| Windows | `windows/hooks.global.json` | `%USERPROFILE%\.cursor\hooks\scripts\` |
| macOS/Linux | `unix/hooks.global.json` | `$HOME/.cursor/hooks/scripts/` |

That avoids hook failures when the Cursor workspace root is not a git repo (for example `empty-window`).

Project `.cursor/hooks.json` comes from `windows/hooks.json` or `unix/hooks.json` (relative script paths).

### Hooks-only sync

```bash
python templates/commands/sync-cursor.py --components hooks
python templates/commands/sync-cursor.py --components hooks,rules
```

### Release bundles

Tag `hooks-vX.Y.Z` on GitHub to publish `cursor-hooks-windows-vX.Y.Z.zip` and `cursor-hooks-unix-vX.Y.Z.zip`. Extract into `.cursor/` for hooks-only installs without the full templates repo.

### Script contract (`hook-common.ps1`)

Windows hook scripts should dot-source `hook-common.ps1` from `$PSScriptRoot` (informational hooks may omit gated JSON helpers):

- Wrap logic in `try/catch`; log errors to **stderr** only.
- Gated hooks must print **one** JSON line on stdout (`permission` / `continue`).
- On failure, fail open with `{"permission":"allow"}` or `{"continue":true,"permission":"allow"}`.

Additional MCP safety hook:
- `validate-mcp-operations` is mapped to `beforeMCPExecution` in the generated hooks JSON.
- It allows read-oriented MCP tools by default and asks for confirmation on state-changing tools.

Additional DB shell safety hook:
- `validate-db-shell-operations` is mapped to `beforeShellExecution` in the generated hooks JSON.
- It denies clearly destructive DB commands and asks for confirmation on write/schema migration commands.
