#!/usr/bin/env bash
# Run formatter on edited file.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  exit 0
fi

path=$(echo "$raw" | jq -r '.file_path // ""')
r0=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')

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
ext="${path##*.}"

run_in_dir() {
  local dir=$1
  shift
  (cd "$dir" && "$@") >/dev/null 2>&1 || true
}

dir=$(dirname "$path")
base=$(basename "$path")

case ".$ext" in
  .py)
    if command -v black >/dev/null 2>&1; then
      run_in_dir "$dir" black "$base"
    fi
    ;;
  .ts|.tsx|.js|.jsx|.json|.css|.md)
    if command -v npx >/dev/null 2>&1; then
      run_in_dir "$dir" npx prettier --write "$base"
    fi
    ;;
  .go)
    if command -v gofmt >/dev/null 2>&1; then
      run_in_dir "$dir" gofmt -w "$base"
    fi
    ;;
esac
exit 0
