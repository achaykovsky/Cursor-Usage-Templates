# Hooks Template Mapping

`templates/hooks/hooks.json` and `templates/hooks/hooks.unix.json` intentionally reference commands under `.cursor/hooks/scripts/*`.

Why:
- `templates/hooks/windows/*.ps1` and `templates/hooks/unix/*.sh` are source templates.
- `templates/commands/sync-cursor.py` flattens and copies those scripts into `.cursor/hooks/scripts/`.
- The runtime hook config in `.cursor/hooks.json` must reference `.cursor/hooks/scripts/*`.

This means the command paths in template hook JSON files describe the post-sync runtime location, not the template source location.

Additional MCP safety hook:
- `validate-mcp-operations` is mapped to `beforeMCPExecution` in `hooks.json` and `hooks.unix.json`.
- It allows read-oriented MCP tools by default and asks for confirmation on state-changing tools.

Additional DB shell safety hook:
- `validate-db-shell-operations` is mapped to `beforeShellExecution` in `hooks.json` and `hooks.unix.json`.
- It denies clearly destructive DB commands and asks for confirmation on write/schema migration commands.
