#!/usr/bin/env bash
# Run tests before git push if project has pytest or npm test.
# Requires: jq

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

cmd=$(echo "$raw" | jq -r '.command // ""' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if ! printf '%s\n' "$cmd" | grep -qE '^[[:space:]]*git[[:space:]]+push\b'; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

cwd=$(echo "$raw" | jq -r '.cwd // empty')
root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
r=$cwd
if [[ -z "$r" ]]; then
  r=$root
fi
if [[ -z "$r" || ! -d "$r" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

cd "$r" || exit 0
ran=false
status=0

if [[ -f pyproject.toml ]] && command -v poetry >/dev/null 2>&1; then
  poetry run pytest -q || status=$?
  ran=true
elif [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
  if node -e "const p=require('./package.json'); process.exit(p.scripts&&p.scripts.test?0:1)" 2>/dev/null; then
    npm test || status=$?
    ran=true
  fi
fi

if [[ "$ran" == false ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

if [[ "$status" -ne 0 ]]; then
  jq -nc '{continue:false,permission:"deny",user_message:"Tests failed. Fix before pushing.",agent_message:"Run tests locally. Use validate-pre-deploy for full pre-push checklist."}'
  exit 0
fi

printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
