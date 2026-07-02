"""Extended hook policy tests: main(), force-push, overrides, modes, heredoc.

Complements test_hook_policy.py with CLI edge cases, project-level overrides,
mode toggles (off/log/advisory), and platform-specific parsing (Windows shlex).
"""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from _hooks_bootstrap import ensure_policy_path, run_test_file

ensure_policy_path()

import hook_policy  # noqa: E402


def _payload(cmd: str, **extra: object) -> dict:
    """Build beforeShellExecution payload; extra keys simulate cwd/workspace_roots overrides."""
    base = {"hook_event_name": "beforeShellExecution", "command": cmd, "workspace_roots": ["/proj"]}
    base.update(extra)
    return base


def _policy_with_modes(**modes: str) -> dict:
    """Clone loaded policy with selective mode overrides — avoids mutating global cache."""
    policy = hook_policy.load_policy(None)
    policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
    policy.setdefault("modes", {}).update(modes)
    return policy


def _run_main(domain: str, stdin_data: str) -> tuple[str, str]:
    """Drive hook_policy.main() without subprocess — captures stdout/stderr buffers."""
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
    """Empty stdin is treated as non-blocking hook invocation — fail-open."""
    stdout, _ = _run_main("shell-db", "")
    assert json.loads(stdout)["permission"] == "allow"


def test_main_invalid_json_returns_allow() -> None:
    """Invalid JSON must not crash Cursor; stderr carries invalid_hook_payload."""
    stdout, stderr = _run_main("shell-db", "not-json")
    assert json.loads(stdout)["permission"] == "allow"
    assert "invalid_hook_payload" in stderr


def test_main_valid_payload_roundtrip() -> None:
    """Stdout must be a single JSON line — Cursor parses it directly."""
    payload = json.dumps(_payload('psql -c "SELECT 1"'))
    stdout, _ = _run_main("shell-db", payload)
    result = json.loads(stdout)
    assert result["permission"] == "allow"
    assert "\n" not in stdout.strip()


def test_main_unknown_domain_returns_allow() -> None:
    """Unregistered domains default allow so new hook types do not brick the agent."""
    stdout, _ = _run_main("unknown-domain", json.dumps(_payload("echo hi")))
    assert json.loads(stdout)["permission"] == "allow"


def test_force_push_main_denied(tmp_path: Path) -> None:
    """Force push to detected default branch is deny — protects main/master."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    payload = _payload("git push --force", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    with patch("subprocess.check_output", return_value="main\n"):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "deny"


def test_force_push_with_lease_denied(tmp_path: Path) -> None:
    """Force-with-lease rewrites remote history — blocked by git_history_rewrite policy."""
    (tmp_path / ".git").mkdir()
    payload = _payload("git push --force-with-lease", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "deny"


def test_force_push_feature_branch_denied(tmp_path: Path) -> None:
    """Force push on any branch is blocked when git_history_rewrite is deny."""
    (tmp_path / ".git").mkdir()
    payload = _payload("git push --force", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "deny"


def test_force_push_subprocess_failure_still_denied_by_pattern(tmp_path: Path) -> None:
    """Force push is denied by regex even when branch detection is unavailable."""
    (tmp_path / ".git").mkdir()
    payload = _payload("git push --force", cwd=str(tmp_path), workspace_roots=[str(tmp_path)])
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "deny"


def test_rebase_denied() -> None:
    """Interactive or branch rebase rewrites history."""
    payload = _payload("git rebase main")
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_gh_pr_merge_squash_denied() -> None:
    payload = _payload("gh pr merge 42 --squash")
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_amend_allowed_when_ahead_only(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    payload = _payload(
        'git commit --amend -m "feat: refine login"',
        cwd=str(tmp_path),
        workspace_roots=[str(tmp_path)],
    )
    with patch("subprocess.check_output", return_value="## feature/x...origin/feature/x [ahead 1]\n"):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "allow"


def test_amend_denied_when_up_to_date_with_remote(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    payload = _payload(
        'git commit --amend -m "feat: refine login"',
        cwd=str(tmp_path),
        workspace_roots=[str(tmp_path)],
    )
    with patch("subprocess.check_output", return_value="## main...origin/main\n"):
        result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(tmp_path))
    assert result["permission"] == "deny"


def test_mcp_merge_pull_request_squash_denied() -> None:
    payload = {
        "server": "user-github",
        "tool_name": "merge_pull_request",
        "arguments": {"owner": "o", "repo": "r", "pullNumber": 1, "merge_method": "squash"},
    }
    result = hook_policy.classify_mcp(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_project_override_db_shell_off(tmp_path: Path) -> None:
    """.cursor/hook-policy.json can disable db_shell enforcement for trusted repos."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "hook-policy.json").write_text(
        json.dumps({"modes": {"db_shell": "off"}}), encoding="utf-8"
    )
    payload = _payload('psql -c "DROP DATABASE prod"')
    result = hook_policy.classify("shell-db", payload, tmp_path)
    assert result["permission"] == "allow"


def test_deep_merge_modes(tmp_path: Path) -> None:
    """Project override merges modes deeply — unspecified modes inherit global defaults."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "hook-policy.json").write_text(
        json.dumps({"modes": {"db_shell": "off"}}), encoding="utf-8"
    )
    policy = hook_policy.load_policy(tmp_path)
    assert policy["modes"]["db_shell"] == "off"
    assert policy["modes"]["mcp_write"] == "ask"


def test_heredoc_psql_delete_asks() -> None:
    """Unquoted heredoc delimiter: SQL body scanned, DELETE with WHERE → ask."""
    cmd = "psql <<EOF\nDELETE FROM users WHERE id=1\nEOF"
    payload = _payload(cmd)
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "ask"


def test_heredoc_delimiter_quoted() -> None:
    """Quoted delimiter disables expansion — still scans literal DELETE in body → deny without WHERE."""
    cmd = "psql <<'SQL'\nDELETE FROM users\nSQL"
    payload = _payload(cmd)
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_no_carrier_grep_delete_allowed() -> None:
    """Text search for 'delete' in files must not invoke db_shell carrier rules."""
    payload = _payload("grep delete README.md")
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "allow"


def test_db_shell_log_mode_emits_would_ask(capsys: pytest.CaptureFixture[str]) -> None:
    """log mode allows execution but emits policy_would_ask on stderr for telemetry."""
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
    """advisory mode warns on bad messages via stderr but returns allow."""
    policy = _policy_with_modes(git_commit_format="advisory")
    payload = _payload('git commit -m "wip"')
    result = hook_policy.classify_shell_git(payload, policy)
    assert result["permission"] == "allow"


def test_git_commit_unparsed_deny() -> None:
    """git_commit_unparsed=deny blocks commits when -m message cannot be parsed."""
    policy = _policy_with_modes(git_commit_unparsed="deny")
    payload = _payload("git commit")
    result = hook_policy.classify_shell_git(payload, policy)
    assert result["permission"] == "deny"


def test_mcp_unknown_off() -> None:
    """mcp_unknown=off allows uncataloged MCP tools — for fully trusted environments."""
    policy = _policy_with_modes(mcp_unknown="off")
    payload = {"server": "user-custom", "tool_name": "opaque_tool"}
    result = hook_policy.classify_mcp(payload, policy)
    assert result["permission"] == "allow"


def test_mcp_write_log_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """mcp_write=log mirrors db_shell log — allow plus policy_would_ask audit line."""
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
    """Scoped DELETE is ask-tier — user can confirm row-level destructive ops."""
    payload = _payload('psql -c "DELETE FROM users WHERE id=1"')
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "ask"


def test_delete_all_rows_without_where_denies() -> None:
    """Table-wide DELETE without WHERE is deny — catastrophic data loss vector."""
    payload = _payload('psql -c "DELETE FROM users"')
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_db_binary_argv0_no_full_cmd_scan() -> None:
    """bash -c with embedded psql should not scan the full shell command string."""
    payload = _payload("bash -c 'psql -c \"SELECT 1\" && rm -rf /'")
    result = hook_policy.classify_shell_db(payload, hook_policy.load_policy(None))
    assert result["permission"] == "allow"


def test_policy_cache_invalidates_on_mtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Policy cache must reload when default.policy.json mtime changes mid-session."""
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
    """git.exe prefix must parse on Windows the same as bare git for commit format checks."""
    payload = _payload('git.exe commit -m "feat: add endpoint"')
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(None))
    assert result["permission"] == "allow"


@pytest.mark.parametrize(
    "cmd",
    [
        "rm -rf /",
        "rm -rf $HOME",
        ":(){ :|:& };:",
        'psql -c "DROP TABLE users"',
        "echo DELETE FROM users;",
    ],
)
def test_shell_destructive_denies_known_patterns(cmd: str) -> None:
    """Each legacy block-destructive-shell.ps1 pattern must deny via policy engine."""
    payload = _payload(cmd)
    result = hook_policy.classify_shell_destructive(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"
    assert result["user_message"] == hook_policy._DESTRUCTIVE_USER_MSG


def test_git_reset_hard_denied_via_shell_git() -> None:
    """git reset --hard is handled by git_history_rewrite in shell-git, not shell-destructive."""
    payload = _payload("git reset --hard origin")
    result = hook_policy.classify_shell_git(payload, hook_policy.load_policy(None))
    assert result["permission"] == "deny"


def test_shell_destructive_allows_safe_command() -> None:
    """Non-destructive commands must pass shell-destructive gate."""
    payload = _payload("git status")
    result = hook_policy.classify("shell-destructive", payload, None)
    assert result["permission"] == "allow"


def test_shell_destructive_mode_off_allows_rm_rf() -> None:
    """shell_destructive mode off disables the gate for operators who manage risk elsewhere."""
    policy = hook_policy.load_policy(None)
    policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
    policy.setdefault("modes", {})["shell_destructive"] = "off"
    result = hook_policy.classify_shell_destructive(_payload("rm -rf /"), policy)
    assert result["permission"] == "allow"


def test_main_shell_destructive_domain() -> None:
    """CLI shell-destructive domain round-trips deny JSON on stdout."""
    stdout, _stderr = _run_main("shell-destructive", json.dumps(_payload("rm -rf /")))
    response = json.loads(stdout)
    assert response["permission"] == "deny"


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
