"""Tests for hook policy engine.

Classifies shell (db, git), MCP, and fixture-driven scenarios. Default posture
is allow for reads, ask for writes/destructive ops, deny for catastrophic SQL
and bad commit messages — tests lock that matrix to policy JSON.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from _hooks_bootstrap import ensure_policy_path, run_test_file

ensure_policy_path()

import hook_policy  # noqa: E402


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _payload(cmd: str, **extra: object) -> dict:
    """Minimal beforeShellExecution payload — domain classifiers expect hook_event_name + command."""
    base = {"hook_event_name": "beforeShellExecution", "command": cmd, "workspace_roots": ["/proj"]}
    base.update(extra)
    return base


class ShellDbPolicyTests(unittest.TestCase):
    """Database shell commands: carrier detection vs literal SQL semantics."""

    def test_grep_update_allowed(self) -> None:
        """grep matching 'update' in a file is not a SQL UPDATE — must not trigger db_shell ask."""
        p = _payload("grep -i update README.md")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(Path("/proj")))
        self.assertEqual(r["permission"], "allow")

    def test_terraform_apply_allowed(self) -> None:
        """Infra apply is outside db_shell scope — delegated to other hooks or user judgment."""
        p = _payload("terraform apply -auto-approve")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_psql_delete_asks(self) -> None:
        """DELETE with WHERE is destructive but scoped — default mode asks rather than deny."""
        p = _payload('psql -c "DELETE FROM users WHERE id = 1"')
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_psql_select_allowed(self) -> None:
        """Read-only SQL must never block agent investigation workflows."""
        p = _payload('psql -c "SELECT 1"')
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_drop_database_denied(self) -> None:
        """DROP DATABASE is always deny — no ask mode override in default policy."""
        p = _payload("psql -c 'DROP DATABASE prod'")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "deny")

    def test_alembic_upgrade_asks(self) -> None:
        """Schema migrations mutate production data shape — treated as write/ask."""
        p = _payload("alembic upgrade head")
        r = hook_policy.classify_shell_db(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")


class ShellGitPolicyTests(unittest.TestCase):
    """Git commit message format and argv parsing edge cases."""

    def test_bad_commit_denied(self) -> None:
        """'wip' messages fail conventional-commit advisory in default deny mode."""
        p = _payload('git commit -m "wip"')
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "deny")

    def test_good_commit_allowed(self) -> None:
        """feat: prefix satisfies git_commit_format regex."""
        p = _payload('git commit -m "feat: add login endpoint"')
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_commit_without_m_allowed(self) -> None:
        """Bare git commit opens editor — unparsed commits default allow unless mode says deny."""
        p = _payload("git commit")
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_multiple_m_allowed(self) -> None:
        """Multiple -m flags (title + body) must not false-positive as bad format."""
        p = _payload('git commit -m "feat: title" -m "body line"')
        r = hook_policy.classify_shell_git(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")


class McpPolicyTests(unittest.TestCase):
    """MCP tool classification via mcp_tools.json and name heuristics."""

    def test_unknown_tool_asks(self) -> None:
        """Uncataloged tools require user confirmation — security default for MCP write surface."""
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-custom",
            "tool_name": "do_something_opaque",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_list_releases_read(self) -> None:
        """GitHub list_* tools are pre-classified read in mcp_tools.json."""
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-github",
            "tool_name": "list_releases",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_get_deploy_status_read(self) -> None:
        """get_* metadata queries stay allow-by-default."""
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-github",
            "tool_name": "get_deploy_status",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_create_pr_asks(self) -> None:
        """create_pull_request is write — triggers mcp_write ask mode."""
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-github",
            "tool_name": "create_pull_request",
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_git_add_read(self) -> None:
        """GitKraken git_add_or_commit with action=add is staged as read via tool_arguments."""
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-eamodio.gitlens-extension-GitKraken",
            "tool_name": "git_add_or_commit",
            "arguments": {"action": "add", "directory": "/proj"},
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "allow")

    def test_git_commit_write_asks(self) -> None:
        """Same tool with action=commit crosses into write classification."""
        p = {
            "hook_event_name": "beforeMCPExecution",
            "server": "user-eamodio.gitlens-extension-GitKraken",
            "tool_name": "git_add_or_commit",
            "arguments": {"action": "commit", "directory": "/proj", "message": "feat: x"},
        }
        r = hook_policy.classify_mcp(p, hook_policy.load_policy(None))
        self.assertEqual(r["permission"], "ask")

    def test_server_prefix_read_classifies_uncataloged_tool(self) -> None:
        """Per-server prefix_read in mcp_tools.json applies before global heuristics."""
        policy = hook_policy.load_policy(None)
        policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
        policy["_mcp_tools"] = {
            "servers": {
                "user-custom": {
                    "prefix_read": ["fetch_widget_"],
                }
            }
        }
        risk = hook_policy._mcp_risk_from_catalog(
            "user-custom", "fetch_widget_details", {}, policy
        )
        self.assertEqual(risk, "read")

    def test_server_prefix_write_classifies_uncataloged_tool(self) -> None:
        """Per-server prefix_write marks state-changing tools before falling back to unknown."""
        policy = hook_policy.load_policy(None)
        policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
        policy["_mcp_tools"] = {
            "servers": {
                "user-custom": {
                    "prefix_write": ["publish_report_"],
                }
            }
        }
        risk = hook_policy._mcp_risk_from_catalog(
            "user-custom", "publish_report_now", {}, policy
        )
        self.assertEqual(risk, "write")

    def test_explicit_tool_entry_overrides_server_prefix(self) -> None:
        """Explicit tools map entry wins over prefix heuristics on the same server."""
        policy = hook_policy.load_policy(None)
        policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
        policy["_mcp_tools"] = {
            "servers": {
                "user-custom": {
                    "prefix_read": ["fetch_widget_"],
                    "tools": {"fetch_widget_details": "write"},
                }
            }
        }
        risk = hook_policy._mcp_risk_from_catalog(
            "user-custom", "fetch_widget_details", {}, policy
        )
        self.assertEqual(risk, "write")


class SharedDestructiveSqlTests(unittest.TestCase):
    """shared_destructive_sql expands into db_shell and shell_destructive deny lists."""

    def test_shared_rules_materialized_on_load(self) -> None:
        policy = hook_policy.load_policy(None)
        policy = {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}
        db_ids = {r.get("id") for r in (policy.get("db_shell") or {}).get("deny") or []}
        shell_ids = {r.get("id") for r in (policy.get("shell_destructive") or {}).get("deny") or []}
        self.assertIn("drop_database", db_ids)
        self.assertIn("delete_all_rows", db_ids)
        self.assertIn("drop_table_or_database_bare", shell_ids)
        self.assertIn("delete_all_rows_bare", shell_ids)
        self.assertIn("alembic_downgrade", db_ids)


class PrePushPolicyTests(unittest.TestCase):
    """Pre-push test gate: ask on missing runner, deny on failure by default."""

    def _policy(self) -> dict:
        policy = hook_policy.load_policy(None)
        return {k: v for k, v in policy.items() if k != hook_policy._POLICY_LOAD_FAILURES_KEY}

    def test_non_push_command_allowed(self) -> None:
        p = _payload("git status")
        r = hook_policy.classify_pre_push(p, self._policy())
        self.assertEqual(r["permission"], "allow")

    def test_no_test_config_allowed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = _payload("git push", workspace_roots=[tmp])
            r = hook_policy.classify_pre_push(p, self._policy())
            self.assertEqual(r["permission"], "allow")

    @patch.object(hook_policy.shutil, "which", return_value=None)
    def test_missing_poetry_asks(self, _which: object) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
            p = _payload("git push", workspace_roots=[str(root)])
            r = hook_policy.classify_pre_push(p, self._policy())
            self.assertEqual(r["permission"], "ask")

    @patch.object(hook_policy, "_run_pre_push_tests", return_value=1)
    @patch.object(hook_policy.shutil, "which", return_value="/usr/bin/poetry")
    def test_failed_tests_denied(self, _which: object, _run: object) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
            p = _payload("git push", workspace_roots=[str(root)])
            r = hook_policy.classify_pre_push(p, self._policy())
            self.assertEqual(r["permission"], "deny")

    @patch.object(hook_policy, "_run_pre_push_tests", return_value=1)
    @patch.object(hook_policy.shutil, "which", return_value="/usr/bin/poetry")
    def test_advisory_mode_allows_failed_tests(self, _which: object, _run: object) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
            policy = self._policy()
            policy.setdefault("modes", {})["pre_push"] = "advisory"
            p = _payload("git push", workspace_roots=[str(root)])
            r = hook_policy.classify_pre_push(p, policy)
            self.assertEqual(r["permission"], "allow")


class FixtureFileTests(unittest.TestCase):
    """Golden JSON fixtures document expected permission per domain/payload pair."""

    def test_fixture_files_if_present(self) -> None:
        """Each fixtures/*.json must round-trip classify() to its recorded permission."""
        if not FIXTURES.is_dir():
            self.skipTest("no fixtures dir")
        for path in FIXTURES.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if "domain" not in data:
                continue
            domain = data["domain"]
            payload = data["payload"]
            expected = data["permission"]
            result = hook_policy.classify(domain, payload, Path("/proj"))
            self.assertEqual(result["permission"], expected, msg=path.name)


class MainAndErrorPathTests(unittest.TestCase):
    """CLI main() and fail-open behavior when policy load or engine throws."""

    def test_main_invalid_json_emits_log(self) -> None:
        """Malformed stdin must allow (not block agent) while logging invalid_hook_payload."""
        with self.subTest("invalid_json"):
            stderr_capture = _run_main("shell-db", "not-json", expect_stderr=True)
            self.assertIn("invalid_hook_payload", stderr_capture)

    def test_corrupt_policy_file_fail_open_with_stderr(self) -> None:
        """Corrupt default.policy.json: empty merge + policy_load_failed on stderr, allow on stdout."""
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
        """RuntimeError in classifier escalates to ask when policy_engine_error mode is ask."""
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
        """End-to-end main() with bad policy still returns allow JSON on stdout."""
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
    """Context manager swapping sys.stderr — hooks log diagnostics without polluting stdout JSON."""
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
    """Point hook_policy at an isolated policy directory for corruption/override tests."""
    return patch.object(
        hook_policy,
        "_policy_dirs",
        return_value=[policy_dir],
    )


def _run_main(domain: str, stdin_data: str, *, expect_stderr: bool = False) -> str | tuple[str, str]:
    """Simulate hook_policy.py CLI: JSON on stdin, permission JSON on stdout."""
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
    raise SystemExit(run_test_file(__file__))
