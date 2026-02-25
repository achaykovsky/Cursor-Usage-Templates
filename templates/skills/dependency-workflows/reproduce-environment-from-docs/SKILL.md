---
name: reproduce-environment-from-docs
description: Uses README, Dockerfile, docker-compose, or package manifests to derive setup steps, run commands, and verify the environment (e.g. "can you run the app"). Use when the user wants to "get this running," "set up dev environment," or onboard.
---

# Reproduce Environment from Docs

## Workflow

1. **Find setup sources**
   - Locate README, CONTRIBUTING, Dockerfile, docker-compose, package manifests (e.g. package.json, pyproject.toml), and any setup scripts. Note required tools (runtime, package manager, Docker).

2. **Derive steps**
   - Extract or infer: install dependencies, env vars, database or service startup, build steps, and run command. Preserve order and any documented prerequisites.
   - If steps are missing or ambiguous, state assumptions and suggest the user confirm (e.g. "Assuming Node 18; if not, install from ...").

3. **Run and verify**
   - Execute the steps in order. Use the project's preferred commands (e.g. `npm install`, `poetry install`, `docker-compose up -d`). If a step fails, report the error and suggest a fix (e.g. missing tool, wrong version).
   - Verify the app or service runs (e.g. start command succeeds, health endpoint or smoke check if documented).

4. **Summarize**
   - List what was run and the outcome. Note any deviations from the docs or fixes applied. If something could not be run (e.g. no Docker), say so and give the user the exact steps to run locally.

## Notes

- Do not modify the user's system beyond what is needed for this repo (e.g. avoid global installs if a venv or local tool is sufficient).
- Apply **redact-sensitive-in-output** (shared-practices) for any output or documented steps.
