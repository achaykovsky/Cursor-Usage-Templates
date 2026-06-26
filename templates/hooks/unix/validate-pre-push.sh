#!/usr/bin/env bash
# Run tests before git push when pytest/npm test is configured (policy engine).

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

raw=$(cat || true)
_hook_script="$(basename "${BASH_SOURCE[0]}")"
trap 'register_hook_execution "$raw" "$_hook_script"' EXIT
if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

root=$(project_root_from_payload "$raw" || true)
invoke_hook_policy pre-push "$raw" "$root"
exit 0
