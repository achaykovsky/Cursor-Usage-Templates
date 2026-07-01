#!/usr/bin/env bash
# Validate RAG corpus and golden eval JSON after edits.

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

is_corpus=0
is_golden=0
if [[ "$file_path" =~ templates[/\\]ai-runtime[/\\]rag[/\\].*\.json$ ]] || [[ "$file_path" =~ [/\\]rag[/\\].*corpus.*\.json$ ]]; then
  is_corpus=1
fi
if [[ "$file_path" =~ templates[/\\]ai-runtime[/\\]rag[/\\]eval[/\\].*\.json$ ]] || [[ "$file_path" =~ [/\\]rag[/\\]eval[/\\].*\.json$ ]]; then
  is_golden=1
fi
if [[ "$is_corpus" -eq 0 && "$is_golden" -eq 0 ]]; then exit 0; fi
if [[ "$file_path" =~ \.schema\.json$ ]] || [[ "$file_path" =~ golden-questions\.schema\.json$ ]]; then exit 0; fi

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

kind="corpus"
if [[ "$is_golden" -eq 1 ]]; then
  kind="golden"
fi

if ! stderr=$("$py" "$validator" "$kind" "$full_path" 2>&1); then
  msg=$(echo "$stderr" | tr -d '\r' | sed '/^$/d' | head -n 1)
  [[ -z "$msg" ]] && msg="RAG ${kind} validation failed"
  echo "validate-rag-artifacts: $msg" >&2
fi

exit 0
