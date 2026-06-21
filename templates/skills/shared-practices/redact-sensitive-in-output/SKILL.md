---
name: redact-sensitive-in-output
description: Ensures output (docs, logs, repro steps, release notes, suggestions) contains no secrets, PII, or internal paths; use placeholders or redaction. Use when producing any user-facing or shareable output that might contain sensitive or environment-specific data.
---

# Redact Sensitive in Output

Apply **`security.mdc`** for secrets, credentials, PII, and auth policy. This skill covers **shareable output** (chat replies, tickets, repro docs, release notes) where echoing env-specific or internal detail is easy to miss.

## Workflow

1. **Before pasting or suggesting text for others**
   - Replace secrets and connection strings with placeholders (`REDACTED`, `***`, or env var **names** only).
   - Replace real user/patient identifiers and emails with generic IDs (`user_id`, `REDACTED`).

2. **Output-context checklist**
   - **Repro steps / tickets:** Generalize machine-specific paths (`/home/me/...` → "project root" or `<repo-root>`).
   - **User-facing docs / API examples:** No internal stack traces or verbose server errors — log server-side only.
   - **Release notes / changelog:** No internal hostnames, tenant names, or operational secrets.

3. **When in doubt**
   - Recommend redaction or minimal exposure. For regulated data paths in code, use **sensitive-data-handling** (security-workflows).

## Notes

- Applies to suggested commands, MCP excerpts, and hook-visible output — not only final chat replies.
