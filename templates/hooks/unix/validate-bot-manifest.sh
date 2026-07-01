#!/usr/bin/env bash
# Validate bot manifest JSON under templates/ai-runtime/bots after edits.

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

raw=$(cat || true)
_hook_script="$(basename "${BASH_SOURCE[0]}")"
trap 'register_hook_execution "$raw" "$_hook_script"' EXIT

if [[ -z "${raw//[[:space:]]/}" ]]; then exit 0; fi
if ! command -v jq >/dev/null 2>&1; then exit 0; fi

event=$(echo "$raw" | jq -r '.hook_event_name // empty')
if [[ "$event" != "afterFileEdit" ]]; then exit 0; fi

file_path=$(echo "$raw" | jq -r '.file_path // empty')
if [[ ! "$file_path" =~ templates[/\\]ai-runtime[/\\]bots[/\\].*\.json$ ]]; then exit 0; fi
if [[ "$file_path" =~ manifest\.schema\.json$ ]]; then exit 0; fi

project_root=$(project_root_from_payload "$raw")
[[ -z "$project_root" ]] && exit 0

validator="${project_root}/templates/ai-runtime/validate_bot_runtime.py"
[[ ! -f "$validator" ]] && exit 0
if ! py=$(find_python); then exit 0; fi

if [[ "$file_path" = /* ]]; then
  full_path="$file_path"
else
  full_path="${project_root}/${file_path}"
fi
[[ ! -f "$full_path" ]] && exit 0

if ! stderr=$("$py" "$validator" manifest "$full_path" 2>&1); then
  msg=$(echo "$stderr" | tr -d '\r' | sed '/^$/d' | head -n 1)
  [[ -z "$msg" ]] && msg="manifest validation failed"
  echo "validate-bot-manifest: $msg" >&2
fi

exit 0
