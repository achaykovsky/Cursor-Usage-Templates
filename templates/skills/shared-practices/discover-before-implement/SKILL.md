---
name: discover-before-implement
description: Search the repo for existing modules, utilities, components, hooks, skills, or platform templates before adding new surface area; validate security of reuse candidates (dependency CVEs, unsafe patterns); prefer extend, configure, or wrap over create. Use when implementing, adding, building, scaffolding, or creating endpoints, components, modules, shared helpers, or adopting dependencies.
---

# Discover Before Implement

## Workflow

1. **Scope**
   - What capability is being added (API route, UI component, test helper, hook, infra module, bot/RAG handler).
   - Note whether the path implies **new packages** or only **internal** reuse.

2. **Discover**
   - Grep/Glob for names, patterns, and adjacent layers; read 2–3 best candidates.
   - Check `templates/` (especially `ai-runtime/`, `hooks/`, `skills/`) for platform artifacts.
   - Check manifest(s) for packages that already provide the capability.

3. **Validate reuse candidates (security)**
   - **Internal candidate:** Identify security touchpoints (user input, auth/authz, crypto, deserialization, secrets, external I/O). If non-trivial → read/run **security-scan-changes** on the candidate module or planned diff scope.
   - **Dependency candidate (reuse existing declared package):** List implicated packages + versions from manifest/lockfile/imports. Read/run **assess-and-update-dependencies** for those packages. When audit tools exist in the environment (`pip-audit`, `npm audit`, `govulncheck`, etc.), run them read-only and summarize findings — do not install or upgrade without user confirmation per **suggest-commands-dont-run-destructive**.
   - **Adopt new dependency:** Require **assess-and-update-dependencies** before adding to manifest; do not install without user confirmation.
   - **CVE policy:** Unresolved **CRITICAL** CVE with no fix → **block reuse**; escalate `@agent(SECURITY)` or choose a safer alternative. **HIGH** → warn and require stated mitigation before `proceed with mitigation`.
   - **Block unsafe reuse** for known unsafe API usage (e.g. `pickle` on untrusted data, `eval` on user input) or abandoned packages with no security path.

4. **Decide**
   - `extend` | `configure` | `wrap` | `create` with one-line justification.
   - Security posture: `proceed` | `proceed with mitigation` | `do not reuse`.

5. **Proceed**
   - Run domain skill only after decision and security check status are stated in reply or plan.

## Output Contract

- Search terms / paths checked
- Best existing candidates (path + one line each)
- Packages implicated (name + version if known)
- Security validation status (scanned / recommended command / not applicable / blocked)
- Decision + justification
- If `create`: what was not reusable and why
- If blocked reuse: alternative path (patch dep, different module, new safer dep)

## Routing boundaries

- **explain-codebase-structure** — repo map / "where is X" when discover needs orientation
- **audit-codebase-cleanup** — post-hoc duplication audit; not a substitute for discover
- **design-feature-from-requirements** — design phase; discover runs before or feeds step 2
- **assess-and-update-dependencies** — CVE/outdated check when reuse implicates packages or before adopting new deps
- **security-scan-changes** — OWASP pass when reused internal code has security touchpoints
- **suggest-commands-dont-run-destructive** — list audit/install commands; do not apply dep changes without confirmation
- **validate-pre-deploy** — pre-release dep vuln gate; cross-check before shipping reused dep paths

## Notes

- Greenfield scaffold: reuse **patterns and conventions**, not existing app code; still assess **new** deps before add.
- User override: `"new module, do not reuse X"` — document override, skip discover for that scope.
- Trivial internal reuse (pure formatting, no I/O, no secrets): skip full dep audit; optional quick scan only.
- Reuse internal module with vulnerable transitive dep: patch/upgrade dep first or choose a different path.
- Exemplar of delegating to existing helpers: `plan-python-remediation-sync-scripts.md` (sync dedup pattern).
