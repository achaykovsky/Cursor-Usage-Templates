---
name: redact-sensitive-in-output
description: Ensures output (docs, logs, repro steps, release notes, suggestions) contains no secrets, PII, or internal paths; use placeholders or redaction. Use when producing any user-facing or shareable output that might contain sensitive or environment-specific data.
---

# Redact Sensitive in Output

Apply this whenever producing output that may be shared, pasted into tickets, or committed.

## Rules

- **Secrets:** Do not include API keys, passwords, tokens, or connection strings. Use placeholders (e.g. `REDACTED`, `***`, or "present in X") or env var names.
- **PII:** Do not log or echo real user/patient identifiers, emails, or auth material. Use placeholders (e.g. `user_id`, `REDACTED`).
- **Internal paths:** In repro steps or docs intended for others, generalize or redact machine-specific paths (e.g. `/home/me/...` → "project root" or placeholder).
- **Errors:** Do not expose internal errors or stack traces in API responses or user-facing docs; suggest logging server-side only.
- **Release notes / changelog:** Do not include internal or sensitive details.

## When in doubt

Recommend redaction or minimal exposure. Treat config, credentials, and user identifiers as sensitive.
