#!/usr/bin/env bash
# Redact sensitive file content before passing to model.
# Requires: python3

set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

python3 -c "$(cat <<'PY'
import json, re, sys

raw = sys.stdin.read()
if not raw.strip():
    print('{"permission":"allow"}')
    raise SystemExit(0)

payload = json.loads(raw)
path = payload.get("file_path") or ""
content = payload.get("content") or ""

patterns = (
    r"\.env$",
    r"\.env\.",
    r"\.pem$",
    r"\.key$",
    r"secrets\.",
    r"credentials\.",
    r"config\.local\.",
    r"\.secret",
    r"id_rsa",
    r"id_ed25519",
)
is_sensitive = any(re.search(p, path) for p in patterns)

if is_sensitive:
    redacted = re.sub(r"(?m)^([^#=]+)=(.*)$", r"\1=***REDACTED***", content)
    redacted = re.sub(
        r"(-----BEGIN[^\r\n]+-----)[\s\S]*?(-----END[^\r\n]+-----)",
        r"\1 ***REDACTED*** \2",
        redacted,
    )
    print(json.dumps({"permission": "allow", "content": redacted}, separators=(",", ":")))
else:
    print('{"permission":"allow"}')
PY
)"

exit 0
