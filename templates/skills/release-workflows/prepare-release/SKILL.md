---
name: prepare-release
description: Checklist: version bump, changelog, release notes, tag, build artifacts; validates and suggests exact commands or steps. Use when the user says "prepare release," "cut a release," or "update changelog."
---

# Prepare Release

## Workflow

1. **Determine release type and version**
   - What is being released? (App, library, or package.) Next version: patch, minor, or major? Check current version in manifest (e.g. package.json, pyproject.toml, Cargo.toml) and suggest the new value (e.g. semver).

2. **Changelog and release notes**
   - Collect changes since last release: commits, PRs, or ticket list. Group by category (e.g. Features, Fixes, Breaking changes).
   - Update CHANGELOG or equivalent: add a new section for the release with date and version. Write user-facing release notes (short summary and bullet list). Apply **redact-sensitive-in-output** (shared-practices).

3. **Version bump and tag**
   - Update version in all relevant files (manifest, lockfile if needed, or version constant). Ensure consistency.
   - Propose tag name (e.g. `v1.2.0`) and tag message. Suggest commands: `git tag -a v1.2.0 -m "Release v1.2.0"` or the project's standard.

4. **Build and artifacts**
   - Identify build command (e.g. `npm run build`, `cargo build --release`). Suggest running it and verifying artifacts. Note where outputs go (e.g. `dist/`, target dir). If the project has a release script or CI that publishes, point to it and list any manual steps.

5. **Summarize**
   - Ordered checklist: version bump, changelog updated, tag created, build verified, and (if applicable) publish command. Give exact commands for the user to run.

## Notes

- Apply **suggest-commands-dont-run-destructive** (shared-practices): prefer listing steps and commands; do not push tags or publish unless the user explicitly asks.
- If the project uses automated release (e.g. release please, semantic-release), align with that flow instead of manual steps.
