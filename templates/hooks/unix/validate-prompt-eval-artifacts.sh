#!/usr/bin/env bash
# Validate prompt eval suite and baseline JSON after edits.

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
[[ -z "$file_path" ]] && exit 0

if [[ ! "$file_path" =~ templates[/\\]ai-runtime[/\\]eval[/\\].*\.json$ ]] && [[ ! "$file_path" =~ [/\\]ai-runtime[/\\]eval[/\\].*\.json$ ]]; then
  exit 0
fi
if [[ "$file_path" =~ \.schema\.json$ ]] || [[ "$file_path" =~ prompt-eval\.schema\.json$ ]] || [[ "$file_path" =~ eval-baseline\.schema\.json$ ]] || [[ "$file_path" =~ llm-judge-calibration\.schema\.json$ ]]; then
  exit 0
fi
if [[ "$file_path" =~ [/\\]fixtures[/\\] ]]; then
  exit 0
fi

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

kind="prompt-eval"
if [[ "$file_path" =~ [/\\]calibration[/\\] ]]; then
  kind="judge-calibration"
elif [[ "$file_path" =~ [/\\]baselines[/\\] ]] || [[ "$file_path" =~ baseline\.json$ ]]; then
  kind="eval-baseline"
fi

if ! stderr=$("$py" "$validator" "$kind" "$full_path" 2>&1); then
  msg=$(echo "$stderr" | tr -d '\r' | sed '/^$/d' | head -n 1)
  [[ -z "$msg" ]] && msg="prompt eval ${kind} validation failed"
  echo "validate-prompt-eval-artifacts: $msg" >&2
fi

exit 0
