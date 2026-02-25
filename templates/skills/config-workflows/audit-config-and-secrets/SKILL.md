---
name: audit-config-and-secrets
description: Finds config and secret usage across the repo; checks for hardcoding, env vs file, and suggests safe patterns (env vars, secret manager, no logs). Use when the user asks to "audit secrets," "where is config," or "check for leaked credentials."
---

# Audit Config and Secrets

## Workflow

1. **Find config and secret usage**
   - Search for: env reads (e.g. `process.env`, `os.environ`, `getenv`), config files (e.g. `.env`, `config.yaml`, `settings.*`), and literal strings that look like secrets (passwords, API keys, tokens). Note which are placeholders vs real.
   - List where config is loaded (entry point, config module) and how it is passed through the app.

2. **Check for hardcoding and leakage**
   - **Hardcoding:** Secrets or sensitive config in source, config files committed to repo, or in logs. Flag each occurrence; suggest moving to env or secret manager and adding to .gitignore if not already.
   - **Logs:** Config or secrets printed in log statements or error messages. Suggest redaction or removal.
   - **Exposure:** Secrets in client-side code, public APIs, or docs. Suggest server-side only and redaction in docs.

3. **Recommend safe patterns**
   - **Env vars:** Non-secret config (e.g. feature flags, URLs) via env; document required vars in README or env.example. No defaults for secrets.
   - **Secret manager:** For production, suggest using a secret manager (e.g. vault, cloud secret store) and injecting at runtime; avoid committing secrets.
   - **.gitignore:** Ensure .env and other local secret files are ignored; suggest adding if missing.

4. **Summarize**
   - List: locations of config and secrets, findings (hardcoded, logged, or exposed), and top actions. Apply **redact-sensitive-in-output** (shared-practices).

## Notes

- Treat API keys, passwords, tokens, and connection strings as secrets. When in doubt, flag and suggest env or secret manager.
- If the user only asked "where is config," focus on mapping; still flag obvious secrets.
