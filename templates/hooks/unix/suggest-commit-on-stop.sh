#!/usr/bin/env bash
# Git summary on session stop (bash 3.2+ compatible; no associative arrays).

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  exit 0
fi

root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
if [[ -z "$root" || ! -d "${root}/.git" ]]; then
  exit 0
fi

cd "$root" || exit 0

status=$(git status -sb 2>/dev/null || true)
diff_stat=$(git diff --stat 2>/dev/null || true)
staged=$(git diff --cached --stat 2>/dev/null || true)
staged_names=$(git diff --cached --name-only 2>/dev/null || true)
unstaged_names=$(git diff --name-only 2>/dev/null || true)

if [[ -z "$status" && -z "$diff_stat" && -z "$staged" ]]; then
  exit 0
fi

echo ""
echo "--- Session stopped. Git summary ---"
[[ -n "$status" ]] && printf '%s\n' "$status"
if [[ -n "$staged" ]]; then
  echo ""
  echo "Staged:"
  printf '%s\n' "$staged"
fi
if [[ -n "$diff_stat" ]]; then
  echo ""
  echo "Unstaged:"
  printf '%s\n' "$diff_stat"
fi

all_files=()
while IFS= read -r line; do
  [[ -n "$line" ]] && all_files+=("$line")
done < <(printf '%s\n%s\n' "$staged_names" "$unstaged_names" | sort -u | grep -v '^$' || true)
if ((${#all_files[@]} <= 1)); then
  echo ""
  echo "Use @prepare-atomic-commit for full commit grouping."
  exit 0
fi

classify() {
  local f=$1
  if printf '%s\n' "$f" | grep -qE 'test[s_]?/|_test\.|\.test\.|spec\.|/tests/'; then
    echo test
    return
  fi
  if printf '%s\n' "$f" | grep -qE '^docs/|/docs/|README|\.md$'; then
    echo docs
    return
  fi
  if printf '%s\n' "$f" | grep -qE '\.(py|go|ts|tsx|js|jsx)$' && ! printf '%s\n' "$f" | grep -qi test; then
    echo feat
    return
  fi
  if printf '%s\n' "$f" | grep -qE '\.(json|yaml|yml)$|pyproject|package\.json'; then
    echo chore
    return
  fi
  echo chore
}

feat=() docs=() test=() chore_g=()
for f in "${all_files[@]}"; do
  g=$(classify "$f")
  case $g in
    feat) feat+=("$f") ;;
    docs) docs+=("$f") ;;
    test) test+=("$f") ;;
    *) chore_g+=("$f") ;;
  esac
done

nonempty=0
((${#feat[@]} > 0)) && ((nonempty++))
((${#docs[@]} > 0)) && ((nonempty++))
((${#test[@]} > 0)) && ((nonempty++))
((${#chore_g[@]} > 0)) && ((nonempty++))

if ((nonempty > 1)); then
  echo ""
  echo "--- Suggested commit split ---"
  if ((${#feat[@]} > 0)); then
    echo ""
    echo "feat: add or update feature"
    printf '  %s\n' "${feat[@]}"
  fi
  if ((${#docs[@]} > 0)); then
    echo ""
    echo "docs: update documentation"
    printf '  %s\n' "${docs[@]}"
  fi
  if ((${#test[@]} > 0)); then
    echo ""
    echo "test: add or update tests"
    printf '  %s\n' "${test[@]}"
  fi
  if ((${#chore_g[@]} > 0)); then
    echo ""
    echo "chore: update config or misc"
    printf '  %s\n' "${chore_g[@]}"
  fi
fi

echo ""
echo "Use @prepare-atomic-commit for full commit grouping."
exit 0
