#!/usr/bin/env bash
# After edits under templates/, copy changed components into project .cursor/ for immediate try.

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

raw=$(cat || true)
_hook_script="$(basename "${BASH_SOURCE[0]}")"
trap 'register_hook_execution "$raw" "$_hook_script"' EXIT

if [[ -z "${raw//[[:space:]]/}" ]]; then
  exit 0
fi

event=$(echo "$raw" | jq -r '.hook_event_name // ""')
if [[ "$event" != "afterFileEdit" ]]; then
  exit 0
fi

path=$(echo "$raw" | jq -r '.file_path // ""')
r0=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
cwd=$(echo "$raw" | jq -r '.cwd // empty')

if [[ -z "$path" ]]; then
  exit 0
fi

if [[ ! -f "$path" && -n "$r0" ]]; then
  path="${r0%/}/${path#./}"
fi

if [[ ! -f "$path" ]]; then
  exit 0
fi

path=$(cd "$(dirname "$path")" && pwd)/$(basename "$path")

case "$path" in
  */templates/*) ;;
  *) exit 0 ;;
esac

root="$cwd"
if [[ -z "$root" && -n "$r0" ]]; then
  root="$r0"
fi
if [[ -z "$root" || ! -d "$root" ]]; then
  exit 0
fi

sync_py="${root}/templates/commands/sync-cursor.py"
if [[ ! -f "$sync_py" ]]; then
  exit 0
fi

python_bin=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    python_bin="$candidate"
    break
  fi
done
if [[ -z "$python_bin" ]]; then
  exit 0
fi

"$python_bin" "$sync_py" --project-root "$root" --trigger-file "$path" >/dev/null 2>&1 || true
exit 0
