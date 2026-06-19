"""Tests for hook policy engine."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

POLICY_DIR = Path(__file__).resolve().parent.parent / "policy"
sys.path.insert(0, str(POLICY_DIR))

import hook_policy  # noqa: E402


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _payload(cmd: str, **extra: object) -> dict:
    base = {"hook_event_name": "beforeShellExecution", "command": cmd, "workspace_roots": ["/proj"]}
    base.update(extra)
    return base


class ShellDbPolicyTests(unittest.TestCase):
    def test_grep_update_allowed(self) -> None:
        p = _payload("grep -i update README.md")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(Path("/proj")))
        self.assertEqual(r["permission"], "allow")

    def test_terraform_apply_allowed(self) -> None:
        p = _payload("terraform apply -auto-approve")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_psql_delete_asks(self) -> None:
        p = _payload('psql -c "DELETE FROM users WHERE id = 1"')
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_psql_select_allowed(self) -> None:
        p = _payload('psql -c "SELECT 1"')
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_drop_database_denied(self) -> None:
        p = _payload("psql -c 'DROP DATABASE prod'")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "deny")

    def test_alembic_upgrade_asks(self) -> None:
        p = _payload("alembic upgrade head")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")


class ShellGitPolicyTests(unittest.TestCase):
    def test_bad_commit_denied(self) -> None:
        p = _payload('git commit -m "wip"')
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "deny")

    def test_good_commit_allowed(self) -> None:
        p = _payload('git commit -m "feat: add login endpoint"')
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_commit_without_m_allowed(self) -> None:
        p = _payload("git commit")
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_multiple_m_allowed(self) -> None:
        p = _payload('git commit -m "feat: title" -m "body line"')
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")


class McpPolicyTests(unittest.TestCase):
    def test_unknown_tool_asks(self) -> None:
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-custom",
            "tool_name": "do_something_opaque",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_list_releases_read(self) -> None:
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-github",
            "tool_name": "list_releases",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_get_deploy_status_read(self) -> None:
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-github",
            "tool_name": "get_deploy_status",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_create_pr_asks(self) -> None:
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-github",
            "tool_name": "create_pull_request",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_git_add_read(self) -> None:
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-eamodio.gitlens-extension-GitKraken",
            "tool_name": "git_add_or_commit",
            "arguments": {"action": "add", "directory": "/proj"},
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_git_commit_write_asks(self) -> None:
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-eamodio.gitlens-extension-GitKraken",
            "tool_name": "git_add_or_commit",
            "arguments": {"action": "commit", "directory": "/proj", "message": "feat: x"},
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")


class FixtureFileTests(unittest.TestCase):
    def test_fixture_files_if_present(self) -> None:
        if not FIXTURES.is_dir():
            self.skipTest("no fixtures dir")
        for path in FIXTURES.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            domain = data["domain"]
            payload = data["payload"]
            expected = data["permission"]
            result = hook_policy.classify(domain, payload, Path("/proj"))
            self.assertEqual(result["permission"], expected, msg=path.name)


class MainAndErrorPathTests(unittest.TestCase):
    def test_main_invalid_json_emits_log(self) -> None:
        with self.subTest("invalid_json"):
            stderr_capture = _run_main("shell-db", "not-json", expect_stderr=True)
            self.assertIn("invalid_hook_payload", stderr_capture)

    def test_corrupt_policy_file_fail_open_with_stderr(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            policy_dir = Path(tmp) / "policy"
            policy_dir.mkdir()
            corrupt = policy_dir / "default.policy.json"
            corrupt.write_text("{not valid", encoding="utf-8")
            (policy_dir / "mcp_tools.json").write_text("{}", encoding="utf-8")

            failures: list[dict] = []
            result = hook_policy._load_json(corrupt, failures)
            self.assertEqual(result, {})
            self.assertEqual(len(failures), 1)

            with patch_policy_dir(policy_dir):
                payload = _payload('psql -c "SELECT 1"')
                with _capture_stderr() as stderr:
                    out = hook_policy.classify("shell-db", payload, None)
                self.assertEqual(out["permission"], "allow")
                self.assertIn("policy_load_failed", stderr.getvalue())

    def test_policy_engine_error_ask_mode(self) -> None:
        payload = json.dumps(_payload("psql -c 'SELECT 1'"))
        policy = hook_policy.load_policy(None)
        policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
        policy.setdefault("modes", {})["policy_engine_error"] = "ask"
        loaded = {**policy, hook_policy._POLICY_LOAD_FAILURES_KEY: []}
        with patch.object(hook_policy, "classify_shell_db", side_effect=RuntimeError("boom")):
            with patch.object(hook_policy, "load_policy", return_value=loaded):
                stdout, stderr = _run_main("shell-db", payload)
        response = json.loads(stdout)
        self.assertEqual(response["permission"], "ask")
        self.assertIn("policy_engine_error", stderr)

    def test_main_corrupt_policy_stdout_allow(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            policy_dir = Path(tmp) / "policy"
            policy_dir.mkdir()
            (policy_dir / "default.policy.json").write_text("{bad", encoding="utf-8")
            (policy_dir / "mcp_tools.json").write_text("{}", encoding="utf-8")
            with patch_policy_dir(policy_dir):
                stdout, stderr = _run_main(
                    "shell-db",
                    json.dumps(_payload('psql -c "SELECT 1"')),
                )
        response = json.loads(stdout)
        self.assertEqual(response["permission"], "allow")
        self.assertIn("policy_load_failed", stderr)


def _capture_stderr():
    from contextlib import contextmanager
    from io import StringIO

    @contextmanager
    def _cm():
        old = sys.stderr
        buf = StringIO()
        sys.stderr = buf
        try:
            yield buf
        finally:
            sys.stderr = old

    return _cm()


def patch_policy_dir(policy_dir: Path):
    return patch.object(
        hook_policy,
        "_policy_dirs",
        return_value=[policy_dir],
    )


def _run_main(domain: str, stdin_data: str, *, expect_stderr: bool = False) -> str | tuple[str, str]:
    from io import StringIO

    old_stdin = sys.stdin
    old_stdout = sys.stdout
    out_buf = StringIO()
    err_buf = StringIO()
    sys.stdin = StringIO(stdin_data)
    sys.stdout = out_buf
    old_argv = sys.argv
    sys.argv = ["hook_policy.py", domain]
    try:
        with patch.object(sys, "stderr", err_buf):
            hook_policy.main()
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sys.argv = old_argv
    if expect_stderr:
        return err_buf.getvalue()
    return out_buf.getvalue(), err_buf.getvalue()


if __name__ == "__main__":
    unittest.main()
