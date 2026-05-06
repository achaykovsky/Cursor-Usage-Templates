---
name: suggest-commands-dont-run-destructive
description: Prefer suggesting commands for the user to run; do not run destructive or environment-changing commands without explicit user request. Use when the workflow involves git, package installs, publish, deploy, or data/schema changes.
---

# Suggest Commands, Don't Run Destructive

Apply this when your workflow could modify the user's environment or data.

## Rules

- **Prefer suggesting:** List exact commands and steps for the user to run. Prefer "suggest" and "propose" over executing unless the user clearly asked you to run them.
- **Do not run without explicit ask:** Destructive git (e.g. `git reset --hard`), package install/update, push/publish, deploy, or irreversible data/schema operations (e.g. drop table, delete data) — only run or recommend running after the user has explicitly requested it.
- **Validate/report only when appropriate:** For "check" or "assess" requests, limit to listing and recommendations; do not apply changes. For pre-deploy or release, validate and report; let the user run deploy or publish.
- **MCP parity:** Apply the same policy to MCP tools. Read-only MCP calls are fine; state-changing MCP actions (create/update/delete/deploy/publish/comment/merge) require explicit user request.

## Scope

Applies to: commit/tag push, dependency install/update, release publish, production deploy, migrations that remove or overwrite data.

Also applies to: MCP tool calls with side effects (issue creation, ticket updates, PR merge/tag/release, deploy triggers, DB writes).
