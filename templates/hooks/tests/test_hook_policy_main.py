"""Extended hook policy tests: main(), force-push, overrides, modes, heredoc."""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

POLICY_DIR = Path(__file__).resolve().parent.parent / "policy"
sys.path.insert(0, str(POLICY_DIR))

import hook_policy  # noqa: E402


def _payload(cmd: str, **extra: object) -> dict:
    base = {"hook_event_name": "beforeShellExecution", "command": cmd, "workspace_roots": ["/proj"]}
    base.update(extra)
    return base


def _policy_with_modes(**modes: str) -> dict:
    policy = hook_policy.load_policy(None)
    policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
    policy.setdefault("modes", {}).update(modes)
    return policy


def _run_main(domain: str, stdin_data: str) -> tuple[str, str]:
    old_stdin, old_stdout, old_argv = sys.stdin, sys.stdout, sys.argv
    out_buf, err_buf = StringIO(), StringIO()
    sys.stdin = StringIO(stdin_data)
    sys.stdout = out_buf
    sys.argv = ["hook_policy.py", domain]
    try:
        with patch.object(sys, "stderr", err_buf):
            hook_policy.main()
    finally:
        sys.stdin, sys.stdout, sys.argv = old_stdin, old_stdout, old_argv
    return out_buf.getvalue(), err_buf.getvalue()


def test_main_empty_stdin_returns_allow() -> None:
    stdout, _ = _run_main("shell-db", "")
    assert json.loads(stdout)["permission"] == "allow"


def test_main_invalid_json_returns_allow() -> None:
    stdout, stderr = _run_main("shell-db", "not-json")
    assert json.loads(stdout)["permission"] == "allow"
    assert "invalid_hook_payload" in stderr


def test_main_valid_payload_roundtrip() -> None:
    payload = json.dumps(_payload('psql -c "SELECT 1"'))
    stdout, _ = _run_main("shell-db", payload)
    result = json.loads(stdout)
    assert result["permission"] == "allow"
    assert "\n" not in stdout.strip()


def test_main_unknown_domain_returns_allow() -> None:
    stdout, _ = _run_main("unknown-domain", json.dumps(_payload("echo hi")))
    assert json.loads(stdout)["permission"] == "allow"


def test_force_push_main_denied(tmp_path: Path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    payload = _payload("git push --force", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    with patch("subprocess.check_output", return_value="main\n"):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "deny"


def test_force_push_with_lease_allowed(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    payload = _payload("git push --force-with-lease", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    with patch("subprocess.check_output", return_value="main\n"):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "allow"


def test_force_push_feature_branch_allowed(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    payload = _payload("git push --force", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    with patch("subprocess.check_output", return_value="feature/x\n"):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "allow"


def test_force_push_subprocess_failure_allows(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    payload = _payload("git push --force", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    import subprocess

    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "allow"


def test_project_override_db_shell_off(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "hook-policy.json").write_text(
        json.dumps({"modes": {"db_shell": "off"}}), encoding="utf-8"
    )
    payload = _payload('psql -c "DROP DATABASE prod"')
    result = hook_policy.classify("shell-db", payload, tmp_path)
    assert result["permission"] == "allow"


def test_deep_merge_modes(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "hook-policy.json").write_text(
        json.dumps({"modes": {"db_shell": "off"}}), encoding="utf-8"
    )
    policy = hook_policy.load_policy(tmp_path)
    assert policy["modes"]["db_shell"] == "off"
    assert policy["modes"]["mcp_write"] == "ask"


def test_heredoc_psql_delete_asks() -> None:
    cmd = "psql <<EOF\nDELETE FROM users WHERE id=1\nEOF"
    payload = _payload(cmd)
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "ask"


def test_heredoc_delimiter_quoted() -> None:
    cmd = "psql <<'SQL'\nDELETE FROM users\nSQL"
    payload = _payload(cmd)
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_no_carrier_grep_delete_allowed() -> None:
    payload = _payload("grep delete README.md")
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "allow"


def test_db_shell_log_mode_emits_would_ask(capsys: pytest.CaptureFixture[str]) -> None:
    policy = _policy_with_modes(db_shell="log")
    payload = _payload('psql -c "DELETE FROM users WHERE id=1"')
    with capsys.disabled():
        old_stderr = sys.stderr
        err_buf = StringIO()
        sys.stderr = err_buf
        try:
            result = hook_policy.classify_shell_db(payload, policy)
        finally:
            sys.stderr = old_stderr
    assert result["permission"] == "allow"
    assert "policy_would_ask" in err_buf.getvalue()


def test_git_commit_format_advisory() -> None:
    policy = _policy_with_modes(git_commit_format="advisory")
    payload = _payload('git commit -m "wip"')
    result = hook_policy.classify_shell_git(payload, policy)
    assert result["permission"] == "allow"


def test_git_commit_unparsed_deny() -> None:
    policy = _policy_with_modes(git_commit_unparsed="deny")
    payload = _payload("git commit")
    result = hook_policy.classify_shell_git(payload, policy)
    assert result["permission"] == "deny"


def test_mcp_unknown_off() -> None:
    policy = _policy_with_modes(mcp_unknown="off")
    payload = {"server": "user-custom", "tool_name": "opaque_tool"}
    result = hook_policy.classify_mcp(payload, policy)
    assert result["permission"] == "allow"


def test_mcp_write_log_mode(capsys: pytest.CaptureFixture[str]) -> None:
    policy = _policy_with_modes(mcp_write="log")
    payload = {"server": "user-github", "tool_name": "create_pull_request"}
    err_buf = StringIO()
    old_stderr = sys.stderr
    sys.stderr = err_buf
    try:
        result = hook_policy.classify_mcp(payload, policy)
    finally:
        sys.stderr = old_stderr
    assert result["permission"] == "allow"
    assert "policy_would_ask" in err_buf.getvalue()


def test_delete_all_rows_with_where_asks_not_denies() -> None:
    payload = _payload('psql -c "DELETE FROM users WHERE id=1"')
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "ask"


def test_delete_all_rows_without_where_denies() -> None:
    payload = _payload('psql -c "DELETE FROM users"')
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_db_binary_argv0_no_full_cmd_scan() -> None:
    """bash -c with embedded psql should not scan the full shell command string."""
    payload = _payload("bash -c 'psql -c \"SELECT 1\" && rm -rf /'")
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "allow"


def test_policy_cache_invalidates_on_mtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    default = policy_dir / "default.policy.json"
    default.write_text(
        json.dumps({"version": 1, "modes": {"db_shell": "off"}}), encoding="utf-8"
    )
    (policy_dir / "mcp_tools.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(hook_policy, "_policy_dirs", lambda _root: [policy_dir])

    first = hook_policy.load_policy(None)
    assert first["modes"]["db_shell"] == "off"

    default.write_text(
        json.dumps({"version": 1, "modes": {"db_shell": "ask"}}), encoding="utf-8"
    )
    hook_policy.clear_policy_cache()
    second = hook_policy.load_policy(None)
    assert second["modes"]["db_shell"] == "ask"


@pytest.mark.skipif(os.name != "nt", reason="Windows shlex semantics")
def test_windows_cmd_exe_git_commit() -> None:
    payload = _payload('git.exe commit -m "feat: add endpoint"')
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(None))
    assert result["permission"] == "allow"
