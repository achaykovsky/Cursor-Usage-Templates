---
name: security-scan-changes
description: For a given change or PR, checks for obvious issues (injection, hardcoded secrets, unsafe deserialization, permission logic), suggests mitigations, and references OWASP-style guidance where relevant. Use when the user asks for a security review or before sensitive releases.
---

# Security Scan Changes

## Workflow

1. **Scope the change**
   - Obtain the diff or list of changed files. Identify touchpoints: user input, auth/authz, persistence, external calls, serialization, and config/secrets.

2. **Check for common issues**
   - **Injection:** User input concatenated into SQL, commands, or HTML without parameterization or encoding. Suggest parameterized queries, prepared statements, or output encoding.
   - **Secrets:** Hardcoded keys, passwords, or tokens. Suggest env vars or secret manager; flag for removal from history if already committed.
   - **Deserialization:** Untrusted data deserialized without validation or type constraints. Suggest schema validation or allowlists.
   - **Auth/authz:** Missing checks, privilege escalation, or broken access control. Suggest explicit checks and fail-secure defaults.
   - **Other:** Insecure defaults, verbose errors to client, or sensitive data in logs. Suggest tightening and redaction.

3. **Suggest mitigations**
   - For each finding: concrete fix (e.g. use parameterized query, move secret to env). Reference OWASP or project security docs when helpful.
   - Prioritize: critical (must fix) vs suggestion (should consider).

4. **Summarize**
   - Short summary: scope reviewed, number and severity of findings, and top actions. If nothing obvious, state that and recommend broader review for high-risk areas.

## Notes

- Do not claim "secure"; this is a lightweight pass. Recommend dedicated security review for sensitive or regulated contexts.
- Apply **redact-sensitive-in-output** (shared-practices): suggest moving or redacting secrets; do not add or commit them.
