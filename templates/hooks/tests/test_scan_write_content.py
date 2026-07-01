"""Tests for scan_write_content.py."""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import sys
from io import StringIO

from _hooks_bootstrap import ensure_policy_path, run_test_file

ensure_policy_path()

import scan_write_content  # noqa: E402


def _run_main(*args: str, stdin: str = "") -> tuple[int, str]:
    old_stdin, old_stdout = sys.stdin, sys.stdout
    out_buf = StringIO()
    sys.stdin = StringIO(stdin)
    sys.stdout = out_buf
    try:
        code = scan_write_content.main(list(args))
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    return code, out_buf.getvalue()


def _quoted_literal(length: int = 12) -> str:
    return "'" + ("a" * length) + "'"


def test_log_password_matches_logger_info() -> None:
    text = 'logger.info("user password=%s", pwd)'
    assert "log_password" in scan_write_content.scan_log_edit_content(text)


def test_fstring_secret_log_matches_single_dot_before_method() -> None:
    text = 'logger.info(f"token={token}")'
    assert "fstring_secret_log" in scan_write_content.scan_log_edit_content(text)


def test_log_password_matches_log_debug() -> None:
    assert "log_password" in scan_write_content.scan_log_edit_content('log.debug("secret value")')


def test_write_scan_detects_hardcoded_assignment() -> None:
    label = "api_" + "key"
    text = label + " = " + _quoted_literal()
    assert "hardcoded_api_key" in scan_write_content.scan_write_content(text)


def test_edit_payload_scans_all_edits_once() -> None:
    payload = {
        "edits": [
            {"new_string": 'logger.info("password leaked")'},
            {"newString": 'print("token here")'},
        ]
    }
    issues = scan_write_content.scan_edit_payload(payload, "log-scan")
    assert "log_password" in issues


def test_edit_payload_corpus_mode() -> None:
    payload = {"edits": [{"new_string": "contact: user@example.com"}]}
    issues = scan_write_content.scan_edit_payload(payload, "corpus-pii-scan")
    assert "corpus_email" in issues


def test_edit_payload_invalid_mode_returns_empty() -> None:
    payload = {"edits": [{"new_string": 'logger.info("password")'}]}
    assert scan_write_content.scan_edit_payload(payload, "write-scan") == []


def test_main_edit_payload_command() -> None:
    payload = json.dumps({"edits": [{"new_string": 'logger.info("password=x")'}]})
    code, out = _run_main("edit-payload", "log-scan", stdin=payload)
    assert code == 0
    assert "log_password" in json.loads(out)["issues"]


def test_emit_scan_result_only_allowlisted_rule_ids() -> None:
    label = "api_" + "key"
    stdin = label + " = " + _quoted_literal()
    code, out = _run_main("write-scan", stdin=stdin)
    assert code == 0
    parsed = json.loads(out)
    assert parsed["issues"] == ["hardcoded_api_key"]
    assert _quoted_literal().strip("'") not in out


def test_main_tool_payload_invalid_json() -> None:
    code, out = _run_main("tool-payload", stdin="not-json")
    assert code == 0
    parsed = json.loads(out)
    assert parsed["issues"] == []
    assert parsed["error"] == "invalid_json"


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
