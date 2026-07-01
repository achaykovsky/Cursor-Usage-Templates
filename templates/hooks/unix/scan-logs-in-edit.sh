#!/usr/bin/env bash
# Warn when edits introduce secrets in log statements or PII in RAG corpus JSON.

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
scan_mode="log-scan"
if [[ "$file_path" =~ templates[/\\]ai-runtime[/\\]rag[/\\].*\.json$ ]] || [[ "$file_path" =~ [/\\]rag[/\\].*corpus.*\.json$ ]]; then
  if [[ ! "$file_path" =~ \.schema\.json$ ]]; then
    scan_mode="corpus-pii-scan"
  fi
fi

project_root=$(project_root_from_payload "$raw")
if ! py=$(find_python); then exit 0; fi
if ! scanner=$(find_scan_write_script "$project_root"); then exit 0; fi

# Single Python invocation for all edits — avoids per-line process spawn overhead.
out=$(printf '%s' "$raw" | "$py" "$scanner" edit-payload "$scan_mode" 2>/dev/null) || exit 0
collected=$(echo "$out" | jq -r '.issues // [] | join(", ")' 2>/dev/null || true)

if [[ -n "$collected" ]]; then
  if [[ "$scan_mode" == "corpus-pii-scan" ]]; then
    echo "scan-logs-in-edit: possible PII in RAG corpus ($collected). Review sensitive-data-handling and rag-pipeline rules." >&2
  else
    echo "scan-logs-in-edit: possible secret in log statement ($collected). Review sensitive-data-handling skill." >&2
  fi
fi

exit 0
