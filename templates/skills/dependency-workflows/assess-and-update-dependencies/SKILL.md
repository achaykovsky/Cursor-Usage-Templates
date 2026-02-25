---
name: assess-and-update-dependencies
description: Lists direct and transitive dependencies, checks for known vulnerabilities and outdated major/minor versions, proposes an upgrade path with breaking-change awareness, and suggests lockfile or CI updates. Use when the user asks to "update deps," "check vulnerabilities," or "upgrade X."
---

# Assess and Update Dependencies

## Workflow

1. **List dependencies**
   - Identify the dependency manifest(s): e.g. `package.json`, `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `pom.xml`.
   - List direct dependencies and, if relevant and easy to obtain, key transitive ones (e.g. from lockfile or `pip show`). Note current versions.

2. **Check for vulnerabilities**
   - If the ecosystem has a standard tool (e.g. `npm audit`, `pip-audit`, `cargo audit`, `go list -m -u` with govulncheck), recommend running it and summarize findings.
   - For reported vulnerabilities: note severity, affected package and version, and whether an upgrade or patch is available. Do not run tools that modify the system without user confirmation; prefer showing commands.

3. **Assess outdated packages**
   - Use ecosystem-appropriate commands (e.g. `npm outdated`, `pip list --outdated`, `cargo outdated`) to list newer versions. Categorize: patch/minor vs major.
   - For each dependency the user wants to update: note the current version, latest compatible version, and latest major (if different). Flag likely breaking changes for major bumps (changelog, migration guide, or common breaking patterns).

4. **Propose upgrade path**
   - Recommend order: security-related updates first, then patch/minor, then major. For major upgrades, suggest one at a time with test/run verification between.
   - List concrete version targets and, if applicable, exact install/update commands (e.g. `npm install pkg@x.y.z`, `poetry add pkg==x.y.z`).
   - Mention lockfile: after updating, regenerate lockfile (e.g. `npm install`, `poetry lock`, `pip freeze`) and run tests.

5. **CI and reproducibility**
   - If the project has CI: note that CI should run with updated deps and lockfile. Suggest committing manifest + lockfile together.
   - Pin versions in recommendations where the project expects reproducible builds.

## Notes

- Apply **suggest-commands-dont-run-destructive** (shared-practices). Prefer listing commands and proposed versions.
- If the user only asked to "check" or "assess," limit to listing and recommendations; do not apply changes.
