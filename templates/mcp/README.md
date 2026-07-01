# MCP Servers to Configure

**Hub:** [USAGE.md](../USAGE.md) | **Rules:** [mcp-integrations.mdc](../rules/mcp-integrations.mdc)

This repository does not store live MCP credentials or machine-specific endpoints.
Configure these servers in your local Cursor MCP settings:

1. GitHub MCP
2. Linear MCP or Jira MCP
3. Sentry MCP
4. Docs MCP (Confluence/Notion/internal KB)
5. Database MCP (read-only default)

## Expected usage mapping

- GitHub MCP -> PR review, checks, issues, release notes
- Linear/Jira MCP -> task status, release blockers, signoff traceability
- Sentry MCP -> incident/performance traces and errors
- Docs MCP -> external specs and doc sync validation
- Database MCP (read-only) -> schema/state checks before deploy

## Safety defaults

- CLI-first token routing: see **CLI vs MCP (token routing)** in [mcp-integrations.mdc](../rules/mcp-integrations.mdc) before reaching for MCP.
- Read-only by default.
- State-changing calls require explicit user request/approval.
- Never log secrets or tokens from MCP output.
