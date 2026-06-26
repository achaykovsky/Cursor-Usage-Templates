#!/usr/bin/env bash
# Redact sensitive file content before passing to model.

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

raw=$(cat || true)
_hook_script="$(basename "${BASH_SOURCE[0]}")"
trap 'register_hook_execution "$raw" "$_hook_script"' EXIT
if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

project_root=""
if command -v jq >/dev/null 2>&1; then
  project_root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
fi

if py=$(find_python) && script=$(find_redact_script "$project_root"); then
  printf '%s' "$raw" | "$py" "$script" redact-read-payload
  exit 0
fi

printf '%s\n' '{"permission":"allow"}'
exit 0
