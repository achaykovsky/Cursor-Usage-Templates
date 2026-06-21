#!/usr/bin/env python3
"""Shared sensitive-path and content redaction for Cursor hooks.

CLI:
  python redact_sensitive.py redact-text          # stdin text -> stdout redacted text
  python redact_sensitive.py redact-read-payload  # stdin hook JSON -> stdout hook JSON
"""

from __future__ import annotations

import json
import logging
import re
import sys
from typing import Any

logger = logging.getLogger(__name__)

# Path substrings/regexes — applied to file_path before reads and for targeted content rules.
SENSITIVE_PATH_PATTERNS: tuple[str, ...] = (
    r"\.env$",
    r"\.env\.",
    r"\.pem$",
    r"\.key$",
    r"\.pfx$",
    r"\.p12$",
    r"secrets\.",
    r"credentials\.",
    r"credentials\.json",
    r"config\.local\.",
    r"\.secret",
    r"id_rsa",
    r"id_ed25519",
    r"service-account",
    r"token\.json",
)

_REDACTED = "***REDACTED***"

_CONTENT_ENV_LINE = re.compile(r"(?m)^([^#=]+)=(.*)$")
_CONTENT_PEM = re.compile(r"(-----BEGIN[^\r\n]+-----)[\s\S]*?(-----END[^\r\n]+-----)")
_CONTENT_JSON_SECRET = re.compile(
    r'("(?:password|secret|api_key|apiKey|access_token|refresh_token|'
    r'private_key|client_secret|auth_token|bearer_token)")\s*:\s*"[^"]*"',
    re.IGNORECASE,
)
_CONTENT_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._\-+/=]+\b")
_CONTENT_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")


def is_sensitive_path(path: str) -> bool:
    """Return True when file_path matches known secret/credential locations."""
    if not path:
        return False
    normalized = path.replace("\\", "/")
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in SENSITIVE_PATH_PATTERNS)


def redact_text(text: str) -> str:
    """Redact common secret patterns in arbitrary text (prompts, logs, file bodies)."""
    if not text:
        return text

    redacted = _CONTENT_ENV_LINE.sub(rf"\1={_REDACTED}", text)
    redacted = _CONTENT_PEM.sub(rf"\1 {_REDACTED} \2", redacted)
    redacted = _CONTENT_JSON_SECRET.sub(rf'\1: "{_REDACTED}"', redacted)
    redacted = _CONTENT_BEARER.sub(f"Bearer {_REDACTED}", redacted)
    redacted = _CONTENT_JWT.sub(_REDACTED, redacted)
    return redacted


def redact_content(content: str, path: str = "") -> str:
    """Redact file content; sensitive paths always redact env/PEM-style values."""
    if not content:
        return content
    if is_sensitive_path(path):
        redacted = _CONTENT_ENV_LINE.sub(rf"\1={_REDACTED}", content)
        redacted = _CONTENT_PEM.sub(rf"\1 {_REDACTED} \2", redacted)
        return redact_text(redacted)
    return redact_text(content)


def redact_read_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build beforeReadFile hook response with optional redacted content."""
    path = str(payload.get("file_path") or "")
    content = payload.get("content")
    content_str = "" if content is None else str(content)

    if is_sensitive_path(path):
        return {"permission": "allow", "content": redact_content(content_str, path)}

    redacted = redact_text(content_str)
    if redacted != content_str:
        return {"permission": "allow", "content": redacted}
    return {"permission": "allow"}


def _read_stdin_text() -> str:
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    command = args[0] if args else ""

    if command == "redact-text":
        text = _read_stdin_text()
        sys.stdout.write(redact_text(text))
        return 0

    if command == "redact-read-payload":
        raw = _read_stdin_text()
        if not raw.strip():
            print(json.dumps({"permission": "allow"}), end="")
            return 0
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("redact_read_invalid_json")
            print(json.dumps({"permission": "allow"}), end="")
            return 0
        print(json.dumps(redact_read_payload(payload), separators=(",", ":")), end="")
        return 0

    logger.error("redact_sensitive_unknown_command", extra={"command": command or "(missing)"})
    print(json.dumps({"permission": "allow"}), end="")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
