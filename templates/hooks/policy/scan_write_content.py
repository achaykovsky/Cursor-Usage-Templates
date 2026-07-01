#!/usr/bin/env python3
"""Scan write/edit content for secrets in code and log statements."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

# High-precision patterns for blocking writes (avoid excessive false positives).
_WRITE_BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "hardcoded_api_key",
        re.compile(
            r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
    ),
    (
        "aws_access_key",
        re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "private_key_block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
)

# Match logger method calls (logger.info, log.debug) — not bare "logger." before "(".
_LOG_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "log_password",
        re.compile(
            r"(?i)(?:(?:log|logger)\.\w+|console\.log|print)\s*\([^)]*\b(password|secret|api_key|token)\b"
        ),
    ),
    (
        "fstring_secret_log",
        re.compile(r"(?i)(?:log|logger)\.\w+\([^)]*f['\"][^'\"]*\{.*(password|secret|token)"),
    ),
)


_CORPUS_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("corpus_email", re.compile(r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("corpus_ssn_like", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "corpus_api_key",
        re.compile(r"(?i)(api[_-]?key|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    ),
)

# Allowlist for stdout — CodeQL flags echoing scan input; we emit rule IDs only.
_KNOWN_RULE_IDS: frozenset[str] = frozenset(
    rule_id
    for patterns in (_WRITE_BLOCK_PATTERNS, _LOG_SECRET_PATTERNS, _CORPUS_PII_PATTERNS)
    for rule_id, _ in patterns
)

_VALID_EDIT_SCAN_MODES: frozenset[str] = frozenset({"log-scan", "corpus-pii-scan"})


def scan_write_content(text: str) -> list[str]:
    if not text:
        return []
    issues: list[str] = []
    for rule_id, pattern in _WRITE_BLOCK_PATTERNS:
        if pattern.search(text):
            issues.append(rule_id)
    return issues


def scan_log_edit_content(text: str) -> list[str]:
    if not text:
        return []
    issues: list[str] = []
    for rule_id, pattern in _LOG_SECRET_PATTERNS:
        if pattern.search(text):
            issues.append(rule_id)
    return issues


def scan_corpus_pii_content(text: str) -> list[str]:
    if not text:
        return []
    issues: list[str] = []
    for rule_id, pattern in _CORPUS_PII_PATTERNS:
        if pattern.search(text):
            issues.append(rule_id)
    return issues


def scan_payload_tool_content(payload: dict[str, Any]) -> list[str]:
    """Extract write tool content from preToolUse hook payload."""
    candidates: list[str] = []
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("content", "new_string", "text", "body"):
            val = tool_input.get(key)
            if isinstance(val, str):
                candidates.append(val)
    elif isinstance(tool_input, str):
        candidates.append(tool_input)

    for key in ("content", "new_string"):
        val = payload.get(key)
        if isinstance(val, str):
            candidates.append(val)

    issues: list[str] = []
    for text in candidates:
        for issue in scan_write_content(text):
            if issue not in issues:
                issues.append(issue)
    return issues


def scan_edit_payload(payload: dict[str, Any], scan_mode: str) -> list[str]:
    """Extract and scan all afterFileEdit edits in one pass (avoids per-line Python spawns)."""
    if scan_mode not in _VALID_EDIT_SCAN_MODES:
        return []

    edits = payload.get("edits")
    if not isinstance(edits, list):
        return []

    scan_fn = scan_corpus_pii_content if scan_mode == "corpus-pii-scan" else scan_log_edit_content
    issues: list[str] = []
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        new_string = edit.get("new_string") or edit.get("newString")
        if not isinstance(new_string, str):
            continue
        for issue in scan_fn(new_string):
            if issue not in issues:
                issues.append(issue)
    return issues


def _emit_scan_result(issue_ids: list[str]) -> None:
    """Write JSON result with allowlisted rule IDs only — never echo scanned secret text."""
    safe_ids = [rule_id for rule_id in issue_ids if rule_id in _KNOWN_RULE_IDS]
    sys.stdout.write(json.dumps({"issues": safe_ids}))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "usage: scan_write_content.py "
            "<write-scan|log-scan|corpus-pii-scan|tool-payload|edit-payload> [scan-mode]",
            file=sys.stderr,
        )
        return 2

    command = args[0]
    raw = sys.stdin.read()

    if command == "write-scan":
        issues = scan_write_content(raw)
    elif command == "log-scan":
        issues = scan_log_edit_content(raw)
    elif command == "corpus-pii-scan":
        issues = scan_corpus_pii_content(raw)
    elif command == "tool-payload":
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"issues": [], "error": "invalid_json"}))
            return 0
        if not isinstance(payload, dict):
            payload = {}
        issues = scan_payload_tool_content(payload)
    elif command == "edit-payload":
        scan_mode = args[1] if len(args) > 1 else "log-scan"
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"issues": [], "error": "invalid_json"}))
            return 0
        if not isinstance(payload, dict):
            payload = {}
        issues = scan_edit_payload(payload, scan_mode)
    else:
        print(f"unknown command: {command}", file=sys.stderr)
        return 2

    _emit_scan_result(issues)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
