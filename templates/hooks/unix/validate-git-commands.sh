#!/usr/bin/env bash
# Validate git commands (policy engine).

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

root=$(project_root_from_payload "$raw" || true)
invoke_hook_policy shell-git "$raw" "$root"
exit 0
