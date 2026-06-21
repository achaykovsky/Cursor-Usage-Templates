---
name: suggest-commands-dont-run-destructive
description: Prefers suggesting commands for the user to run; does not run destructive or environment-changing commands without explicit user request. Use when the workflow involves git, package installs, publish, deploy, or data/schema changes.
---

# Suggest Commands, Don't Run Destructive

Apply when a workflow could modify the user's environment, data, or external systems. Align with **`ai-guardrails.mdc`** safety and hook gates (`block-destructive-shell`, `validate-git-commands`, `validate-mcp-operations`).

## Workflow

1. **Prefer suggesting**
   - List exact commands and steps for the user to run. Use "suggest" and "propose" over executing unless the user clearly asked you to run them.

2. **Do not run without explicit ask**
   - Destructive git (e.g. `git reset --hard`), package install/update, push/publish, deploy, or irreversible data/schema ops (e.g. drop table, delete data) — only run after explicit user request.

3. **Validate/report only when appropriate**
   - For "check" or "assess" requests: list findings and recommendations; do not apply changes. For pre-deploy or release: validate and report; let the user run deploy or publish.

4. **MCP parity**
   - Read-only MCP calls are fine. State-changing MCP actions (create/update/delete/deploy/publish/comment/merge) require explicit user request.

## Notes

- **Scope:** commit/tag push, dependency install/update, release publish, production deploy, migrations that remove or overwrite data, and MCP tools with side effects (issues, tickets, PR merge/tag/release, deploy triggers, DB writes).
