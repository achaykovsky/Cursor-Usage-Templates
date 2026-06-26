"""Tests for cursor_activity.py.

Covers event inference, payload normalization, sensitive-path redaction, log
querying, and the CLI ``normalize`` subcommand. Normalization must stay stable
because hook scripts append JSONL rows that downstream query tools consume.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _commands_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
from pathlib import Path

import pytest

from _commands_bootstrap import ensure_paths, run_test_file

ensure_paths()

import cursor_activity as ca


def test_infer_event_from_shape() -> None:
    """Hook payloads omit event names; inference must match Cursor field shapes."""
    # Arrange — representative payloads per hook type (no hook_event_name set)
    # Act & Assert — each distinct key set maps to exactly one event
    assert ca.infer_event({"file_path": "a.py", "edits": []}) == "afterFileEdit"
    assert ca.infer_event({"prompt": "hi"}) == "beforeSubmitPrompt"
    assert ca.infer_event({"command": "git status"}) == "beforeShellExecution"
    assert ca.infer_event({"status": "completed"}) == "stop"


def test_normalize_before_submit_prompt() -> None:
    """Prompt submissions must retain attachment metadata without storing raw prompt text in summaries."""
    # Arrange
    payload = {
        "hook_event_name": "beforeSubmitPrompt",
        "conversation_id": "c1",
        "generation_id": "g1",
        "prompt": "Add logging",
        "attachments": [{"type": "file", "file_path": "src/a.py"}],
    }
    # Act
    entry = ca.normalize_activity_entry(payload, ts="2026-02-25T20:11:35Z")
    # Assert — length is stored instead of full prompt to limit log size
    assert entry["event"] == "beforeSubmitPrompt"
    assert entry["prompt_length"] == 11
    assert entry["attachments"][0]["file_path"] == "src/a.py"


def test_normalize_after_file_edit_summary() -> None:
    """Edit logs keep previews for scanning while preserving full diffs for non-sensitive paths."""
    # Arrange
    payload = {
        "conversation_id": "c1",
        "generation_id": "g1",
        "file_path": "src/auth/login.py",
        "edits": [{"old_string": "def login()", "new_string": "def login():\n    pass"}],
    }
    # Act
    entry = ca.normalize_activity_entry(payload, ts="2026-02-25T20:11:42Z")
    # Assert — edits_full enables drill-down; edit_summary keeps rows scannable
    assert entry["edit_count"] == 1
    assert entry["edit_summary"][0]["old_preview"] == "def login()"
    assert "edits_full" in entry


def test_sensitive_path_redacted() -> None:
    """Secret-bearing paths must never persist edit contents — redaction is a security invariant."""
    # Arrange — .env is on the sensitive-path allowlist in cursor_activity
    payload = {
        "file_path": ".env",
        "edits": [{"old_string": "KEY=1", "new_string": "KEY=2"}],
    }
    # Act
    entry = ca.normalize_activity_entry(payload)
    # Assert
    assert entry["redacted"] is True
    assert "edits_full" not in entry


def test_query_logs_groups_by_generation(tmp_path: Path) -> None:
    """query_logs must correlate prompt, edits, and stop events under one generation_id."""
    # Arrange — synthetic JSONL mimicking a single agent turn
    log_dir = tmp_path / ".cursor" / "logs"
    log_dir.mkdir(parents=True)
    lines = [
        {
            "ts": "2026-02-25T20:11:35Z",
            "event": "beforeSubmitPrompt",
            "generation_id": "gen1",
            "prompt": "Add logging to the auth module",
        },
        {
            "ts": "2026-02-25T20:11:42Z",
            "event": "afterFileEdit",
            "generation_id": "gen1",
            "file_path": "src/auth/login.py",
        },
        {
            "ts": "2026-02-25T20:11:50Z",
            "event": "stop",
            "generation_id": "gen1",
            "status": "completed",
        },
    ]
    path = log_dir / "2026-02-25" / "cursor-activity.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in lines) + "\n", encoding="utf-8")

    # Act
    out = ca.query_logs(tmp_path, date="2026-02-25")
    # Assert — human-readable report stitches the turn together
    assert "Generation gen1" in out
    assert "Add logging to the auth module" in out
    assert "src/auth/login.py" in out
    assert "Status: completed" in out


def test_query_logs_reads_legacy_flat_activity_file(tmp_path: Path) -> None:
    """query_logs still reads pre-migration flat files under .cursor/logs/."""
    log_dir = tmp_path / ".cursor" / "logs"
    log_dir.mkdir(parents=True)
    path = log_dir / "cursor-activity-2026-02-25.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {
                    "ts": "2026-02-25T20:11:35Z",
                    "event": "beforeSubmitPrompt",
                    "generation_id": "legacy-gen",
                    "prompt": "legacy prompt",
                },
                {
                    "ts": "2026-02-25T20:11:50Z",
                    "event": "stop",
                    "generation_id": "legacy-gen",
                    "status": "completed",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    out = ca.query_logs(tmp_path, date="2026-02-25")
    assert "Generation legacy-gen" in out
    assert "Status: completed" in out


def test_cmd_normalize_stdin() -> None:
    """CLI normalize reads hook JSON from stdin — same contract hooks use when piping payloads."""
    # Arrange — swap stdin/stdout because main() is not refactored for injectable streams
    payload = {"prompt": "x", "generation_id": "g"}
    raw = json.dumps(payload)
    import io
    import sys

    stdin = io.StringIO(raw)
    stdout = io.StringIO()
    old_in, old_out = sys.stdin, sys.stdout
    try:
        sys.stdin = stdin
        sys.stdout = stdout
        # Act
        assert ca.main(["normalize"]) == 0
    finally:
        sys.stdin, sys.stdout = old_in, old_out
    # Assert
    row = json.loads(stdout.getvalue().strip())
    assert row["event"] == "beforeSubmitPrompt"


def test_validate_log_date_rejects_path_traversal() -> None:
    """--date must not allow path segments that escape the log directory."""
    with pytest.raises(ValueError, match="invalid date"):
        ca.validate_log_date("../../etc/passwd")


def test_query_logs_rejects_invalid_date(tmp_path: Path) -> None:
    """query_logs must reject malformed dates before building file paths."""
    with pytest.raises(ValueError, match="invalid date"):
        ca.query_logs(tmp_path, date="2026-01-01/../secret")


def test_cmd_normalize_invalid_json_returns_error() -> None:
    """Malformed stdin must emit error JSON and exit 1 — hooks must not traceback."""
    import io
    import sys

    stdin = io.StringIO("{not json")
    stdout = io.StringIO()
    old_in, old_out = sys.stdin, sys.stdout
    try:
        sys.stdin = stdin
        sys.stdout = stdout
        assert ca.cmd_normalize() == 1
    finally:
        sys.stdin, sys.stdout = old_in, old_out
    row = json.loads(stdout.getvalue().strip())
    assert row["error"] == "invalid_json"


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
