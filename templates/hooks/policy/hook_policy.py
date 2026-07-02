#!/usr/bin/env python3
"""Cursor hook policy engine — classify shell/MCP/git operations.

Usage:
  python hook_policy.py shell-db   # stdin: beforeShellExecution JSON
  python hook_policy.py shell-git
  python hook_policy.py shell-destructive
  python hook_policy.py pre-push   # stdin: beforeShellExecution JSON (git push)
  python hook_policy.py mcp        # stdin: beforeMCPExecution JSON

Stdout: single JSON hook response (allow | ask | deny).
Stderr: structured audit events via _emit_log (stdlib logger is for debug/trace).

Fail-open by design: invalid stdin JSON, unknown domains, and engine errors
return allow/ask per policy modes so hooks never hard-block the IDE. Tighten
defaults via db_shell.modes / git_shell.modes / mcp.modes in hook-policy JSON
for security-sensitive repos.

Exit 0 always (hooks must not crash Cursor on policy engine errors).
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from mcp_classify import classify_tool_name, load_mcp_heuristics

logger = logging.getLogger(__name__)

_POLICY_LOAD_FAILURES_KEY = "_policy_load_failures"

_DESTRUCTIVE_USER_MSG = "Blocked: destructive command not allowed."
_DESTRUCTIVE_AGENT_MSG = (
    "Command blocked by hook. Use suggest-commands-dont-run-destructive: "
    "suggest the command for the user to run instead."
)


def _allow_shell() -> dict[str, Any]:
    return {"continue": True, "permission": "allow"}


def _ask_shell(user: str, agent: str) -> dict[str, Any]:
    return {
        "continue": True,
        "permission": "ask",
        "user_message": user,
        "agent_message": agent,
    }


def _deny_shell(user: str, agent: str) -> dict[str, Any]:
    return {
        "continue": False,
        "permission": "deny",
        "user_message": user,
        "agent_message": agent,
    }


def _emit_log(level: str, event: str, **fields: Any) -> None:
    """Write structured audit events to stderr (stdout is hook JSON only)."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "component": "hook_policy",
        "event": event,
    }
    for key, value in fields.items():
        if value is not None:
            record[key] = value
    print(json.dumps(record, separators=(",", ":")), file=sys.stderr)


def _policy_dirs(project_root: Path | None) -> list[Path]:
    dirs: list[Path] = []
    script_dir = Path(__file__).resolve().parent
    dirs.append(script_dir)
    if project_root:
        custom = project_root / ".cursor" / "hooks" / "policy"
        if custom.is_dir():
            dirs.append(custom)
    return dirs


def _load_json(path: Path, failures: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _emit_log(
            "error",
            "policy_load_failed",
            path=str(path),
            error_type=type(exc).__name__,
        )
        failures.append({"path": str(path), "error_type": type(exc).__name__})
        return {}
    except OSError as exc:
        _emit_log(
            "error",
            "policy_load_failed",
            path=str(path),
            error_type=type(exc).__name__,
            message=str(exc),
        )
        failures.append({"path": str(path), "error_type": type(exc).__name__})
        return {}


def _policy_cache_key(project_root: Path | None) -> tuple[Any, ...]:
    root_str = str(project_root.resolve()) if project_root else ""
    parts: list[Any] = [root_str]
    for d in _policy_dirs(project_root):
        for name in ("default.policy.json", "mcp_tools.json", "hook-policy.json"):
            path = d / name
            parts.append(str(path))
            parts.append(path.stat().st_mtime if path.is_file() else 0)
    if project_root:
        proj = project_root / ".cursor" / "hook-policy.json"
        parts.append(str(proj))
        parts.append(proj.stat().st_mtime if proj.is_file() else 0)
    return tuple(parts)


def clear_policy_cache() -> None:
    """Clear cached policy loads (for tests)."""
    logger.info("clear_policy_cache", extra={})
    _load_policy_cached.cache_clear()


def _load_policy_impl(project_root: Path | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    mcp_tools: dict[str, Any] = {}
    load_failures: list[dict[str, Any]] = []
    had_policy_file = False
    for d in reversed(_policy_dirs(project_root)):
        default_path = d / "default.policy.json"
        if default_path.is_file():
            had_policy_file = True
        default = _load_json(default_path, load_failures)
        if default:
            merged = _deep_merge(merged, default)
        tools_path = d / "mcp_tools.json"
        if tools_path.is_file():
            had_policy_file = True
        tools = _load_json(tools_path, load_failures)
        if tools:
            mcp_tools = _deep_merge(mcp_tools, tools)
        override_path = d / "hook-policy.json"
        if override_path.is_file():
            had_policy_file = True
        override = _load_json(override_path, load_failures)
        if override:
            merged = _deep_merge(merged, override)
    if project_root:
        proj_override = project_root / ".cursor" / "hook-policy.json"
        if proj_override.is_file():
            had_policy_file = True
            override = _load_json(proj_override, load_failures)
            if override:
                merged = _deep_merge(merged, override)
    if load_failures and had_policy_file and not merged and not mcp_tools:
        _emit_log("error", "policy_empty")
    _expand_shared_destructive_sql(merged)
    merged["_mcp_tools"] = mcp_tools
    merged[_POLICY_LOAD_FAILURES_KEY] = load_failures
    return merged


def _expand_shared_destructive_sql(merged: dict[str, Any]) -> None:
    """Materialize shared_destructive_sql.deny into db_shell and shell_destructive deny lists."""
    shared = merged.get("shared_destructive_sql") or {}
    shared_deny = shared.get("deny") or []
    if not shared_deny:
        return

    db_cfg = merged.setdefault("db_shell", {})
    shell_cfg = merged.setdefault("shell_destructive", {})
    db_deny = list(db_cfg.get("deny") or [])
    shell_deny = list(shell_cfg.get("deny") or [])
    db_ids = {str(rule.get("id")) for rule in db_deny if rule.get("id")}
    shell_ids = {str(rule.get("id")) for rule in shell_deny if rule.get("id")}

    for rule in shared_deny:
        pattern = rule.get("pattern")
        if not pattern:
            continue
        apply_to = rule.get("apply") or ["db_shell", "shell_destructive"]
        rule_id = str(rule.get("id") or "shared")

        if "db_shell" in apply_to and rule_id not in db_ids:
            db_rule: dict[str, Any] = {"id": rule_id, "pattern": pattern}
            if rule.get("db_requires_sql_carrier"):
                db_rule["requires_sql_carrier"] = True
            db_deny.append(db_rule)
            db_ids.add(rule_id)

        shell_rule_id = str(rule.get("shell_id") or rule_id)
        if "shell_destructive" in apply_to and shell_rule_id not in shell_ids:
            shell_deny.append({"id": shell_rule_id, "pattern": pattern})
            shell_ids.add(shell_rule_id)

    db_cfg["deny"] = db_deny
    shell_cfg["deny"] = shell_deny


@lru_cache(maxsize=32)
def _load_policy_cached(cache_key: tuple[Any, ...]) -> str:
    root_str = cache_key[0]
    project_root = Path(root_str) if root_str else None
    return json.dumps(_load_policy_impl(project_root), sort_keys=True)


def load_policy(project_root: Path | None) -> dict[str, Any]:
    logger.info("load_policy_enter", extra={"has_project_root": project_root is not None})
    raw = _load_policy_cached(_policy_cache_key(project_root))
    policy = json.loads(raw)
    logger.info(
        "load_policy_exit",
        extra={
            "mcp_tool_servers": len((policy.get("_mcp_tools") or {}).get("servers", {})),
            "load_failure_count": len(policy.get(_POLICY_LOAD_FAILURES_KEY) or []),
        },
    )
    return policy


def _policy_load_error_response(policy: dict[str, Any]) -> dict[str, Any] | None:
    failures = policy.get(_POLICY_LOAD_FAILURES_KEY) or []
    if not failures:
        return None
    mode = (policy.get("modes") or {}).get("policy_load_error", "allow")
    if mode == "ask":
        return _ask_shell(
            "Hook policy file could not be loaded. Confirm before continuing.",
            "Policy load error: one or more policy JSON files are corrupt or unreadable. "
            "Check stderr for policy_load_failed events.",
        )
    if mode == "deny":
        return _deny_shell(
            "Hook policy file could not be loaded.",
            "Policy load error: fix corrupt policy JSON before retrying.",
        )
    return None


def _policy_engine_error_response(policy: dict[str, Any], domain: str, exc: Exception) -> dict[str, Any]:
    _emit_log(
        "error",
        "policy_engine_error",
        domain=domain,
        error_type=type(exc).__name__,
    )
    mode = (policy.get("modes") or {}).get("policy_engine_error", "allow")
    if mode == "ask":
        return _ask_shell(
            "Policy engine error while classifying this hook.",
            "Policy engine error: check stderr for policy_engine_error event.",
        )
    if mode == "deny":
        return _deny_shell(
            "Policy engine error while classifying this hook.",
            "Policy engine error: fix the policy engine before retrying.",
        )
    return _allow_shell()


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in patch.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _first(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for k in keys:
        v = payload.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _project_root(payload: dict[str, Any]) -> Path | None:
    roots = payload.get("workspace_roots") or []
    if roots:
        return Path(str(roots[0]))
    cwd = payload.get("cwd")
    if cwd:
        return Path(str(cwd))
    return None


def _parse_argv(cmd: str) -> list[str]:
    if not cmd.strip():
        return []
    try:
        return shlex.split(cmd, posix=os.name != "nt")
    except ValueError:
        return cmd.split()


def _argv_contains(argv: list[str], tokens: list[str]) -> bool:
    lower = [a.lower() for a in argv]
    need = [t.lower() for t in tokens]
    for i in range(len(lower) - len(need) + 1):
        if lower[i : i + len(need)] == need:
            return True
    return False


def _db_binaries(policy: dict[str, Any]) -> set[str]:
    cfg = policy.get("db_shell") or {}
    return {b.lower() for b in cfg.get("binaries", [])}


def _has_db_context(argv: list[str], binaries: set[str]) -> bool:
    if not argv:
        return False
    exe = Path(argv[0]).name.lower()
    if exe in binaries:
        return True
    for tok in argv:
        base = Path(tok).name.lower()
        if base in binaries:
            return True
    return False


def _sql_carrier_segments(cmd: str, argv: list[str], binaries: set[str]) -> list[str]:
    """Return SQL text segments only when carried by a DB client (-c, -e, heredoc)."""
    segments: list[str] = []
    if not _has_db_context(argv, binaries):
        return segments

    for i, tok in enumerate(argv):
        if tok in ("-c", "-e", "--command") and i + 1 < len(argv):
            segments.append(_strip_outer_quotes(argv[i + 1]))
        if tok.startswith("-c") and len(tok) > 2:
            segments.append(_strip_outer_quotes(tok[2:]))

    heredoc = re.search(r"<<-?\s*['\"]?(\w+)['\"]?\s*\n([\s\S]*?)\n\1", cmd)
    if heredoc:
        segments.append(heredoc.group(2))

    return segments


def _is_readonly_sql(sql: str, policy: dict[str, Any]) -> bool:
    cfg = policy.get("db_shell") or {}
    for rule in cfg.get("allow_readonly_sql", []):
        pat = rule.get("pattern")
        if pat and re.search(pat, sql.strip()):
            return True
    return False


def classify_shell_db(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    logger.info("classify_shell_db_enter", extra={})
    mode = (policy.get("modes") or {}).get("db_shell", "ask")
    if mode == "off":
        return _allow_shell()

    cmd = _first(payload, ("command",))
    if not cmd:
        return _allow_shell()

    argv = _parse_argv(cmd)
    binaries = _db_binaries(policy)
    cfg = policy.get("db_shell") or {}

    if cfg.get("require_db_context", True) and not _has_db_context(argv, binaries):
        return _allow_shell()

    sql_segments = _sql_carrier_segments(cmd, argv, binaries)

    for rule in cfg.get("deny", []):
        pat = rule.get("pattern")
        if not pat:
            continue
        if rule.get("requires_sql_carrier") and not sql_segments:
            continue
        targets = sql_segments if rule.get("requires_sql_carrier") else [cmd]
        for target in targets:
            if re.search(pat, target):
                return _deny_shell(
                    "Blocked: destructive database operation detected.",
                    f"DB policy ({rule.get('id', 'deny')}): blocked destructive command. "
                    "Ask the user explicitly; prefer backup + rollback + scoped target.",
                )

    for rule in cfg.get("ask", []):
        matched = False
        if rule.get("argv_contains") and _argv_contains(argv, rule["argv_contains"]):
            matched = True
        pat = rule.get("pattern")
        if pat:
            if rule.get("requires_sql_carrier"):
                if sql_segments and any(re.search(pat, s) for s in sql_segments):
                    matched = True
            elif re.search(pat, cmd):
                matched = True
        if matched:
            if mode == "log":
                _emit_log(
                    "info",
                    "policy_would_ask",
                    domain="shell-db",
                    rule_id=rule.get("id", "ask"),
                )
                return _allow_shell()
            return _ask_shell(
                "Database write/schema command detected. Confirm this action is explicitly requested "
                "and scoped to the intended environment.",
                f"DB policy ({rule.get('id', 'ask')}): require explicit user approval for write/schema ops.",
            )

    if sql_segments and all(_is_readonly_sql(s, policy) for s in sql_segments if s.strip()):
        logger.info("classify_shell_db_exit", extra={"decision": "allow", "reason": "readonly_sql"})
        return _allow_shell()

    logger.info("classify_shell_db_exit", extra={"decision": "allow", "reason": "default"})
    return _allow_shell()


def classify_shell_destructive(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Deny known-destructive shell commands on the full command string (no DB-carrier gate)."""
    logger.info("classify_shell_destructive_enter", extra={})
    mode = (policy.get("modes") or {}).get("shell_destructive", "deny")
    if mode == "off":
        return _allow_shell()

    cmd = _first(payload, ("command",))
    if not cmd:
        return _allow_shell()

    cfg = policy.get("shell_destructive") or {}
    for rule in cfg.get("deny", []):
        pat = rule.get("pattern")
        if pat and re.search(pat, cmd):
            logger.info(
                "classify_shell_destructive_exit",
                extra={"decision": "deny", "rule_id": rule.get("id", "deny")},
            )
            return _deny_shell(_DESTRUCTIVE_USER_MSG, _DESTRUCTIVE_AGENT_MSG)

    logger.info("classify_shell_destructive_exit", extra={"decision": "allow"})
    return _allow_shell()


def _npm_has_test_script(project_root: Path) -> bool:
    package_json = project_root / "package.json"
    if not package_json.is_file():
        return False
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    scripts = data.get("scripts") or {}
    return bool(scripts.get("test"))


def _detect_pre_push_runner(project_root: Path) -> tuple[str | None, str | None]:
    """Return (runner_id, missing_tool). runner_id is poetry_pytest | npm_test | pytest_direct."""
    if (project_root / "pyproject.toml").is_file():
        if shutil.which("poetry"):
            return "poetry_pytest", None
        return None, "poetry"

    if _npm_has_test_script(project_root):
        if shutil.which("npm"):
            return "npm_test", None
        return None, "npm"

    if any((project_root / name).is_file() for name in ("pytest.ini", "setup.cfg", "tox.ini")):
        if shutil.which("pytest"):
            return "pytest_direct", None
        if shutil.which("poetry"):
            return "poetry_pytest", None
        return None, "pytest"

    return None, None


def _run_pre_push_tests(project_root: Path, runner: str) -> int:
    cwd = str(project_root)
    if runner == "poetry_pytest":
        proc = subprocess.run(
            ["poetry", "run", "pytest", "-q"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return proc.returncode
    if runner == "npm_test":
        proc = subprocess.run(["npm", "test"], cwd=cwd, capture_output=True, text=True)
        return proc.returncode
    if runner == "pytest_direct":
        proc = subprocess.run(["pytest", "-q"], cwd=cwd, capture_output=True, text=True)
        return proc.returncode
    return 0


def classify_pre_push(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Run configured tests before git push; ask when runner missing, deny on failure by default."""
    logger.info("classify_pre_push_enter", extra={})
    mode = (policy.get("modes") or {}).get("pre_push", "deny")
    if mode in ("off", "allow"):
        return _allow_shell()

    cmd = _first(payload, ("command",))
    if not cmd or not re.search(r"\bgit\s+push\b", cmd):
        return _allow_shell()

    project_root = _project_root(payload)
    if not project_root or not project_root.is_dir():
        return _allow_shell()

    runner, missing_tool = _detect_pre_push_runner(project_root)
    if missing_tool:
        _emit_log(
            "warn",
            "pre_push_runner_missing",
            tool=missing_tool,
            project_root=str(project_root),
        )
        if mode == "advisory":
            return _allow_shell()
        return _ask_shell(
            f"Push paused: {missing_tool} is not on PATH but this project expects tests before push.",
            f"Install {missing_tool}, run tests locally, or set modes.pre_push to advisory/off in "
            ".cursor/hook-policy.json.",
        )

    if not runner:
        logger.info("classify_pre_push_exit", extra={"decision": "allow", "reason": "no_test_config"})
        return _allow_shell()

    exit_code = _run_pre_push_tests(project_root, runner)
    if exit_code == 0:
        logger.info("classify_pre_push_exit", extra={"decision": "allow", "runner": runner})
        return _allow_shell()

    _emit_log(
        "warn",
        "pre_push_tests_failed",
        runner=runner,
        exit_code=exit_code,
        project_root=str(project_root),
    )
    if mode == "advisory":
        return _allow_shell()
    if mode == "ask":
        return _ask_shell(
            "Tests failed before push. Confirm you still want to push.",
            "Run tests locally. Use validate-pre-deploy for the full pre-push checklist.",
        )
    return _deny_shell(
        "Tests failed. Fix before pushing.",
        "Run tests locally. Use validate-pre-deploy for full pre-push checklist.",
    )


def _is_git_argv(argv: list[str]) -> bool:
    if not argv:
        return False
    return Path(argv[0]).stem.lower() == "git"


def _strip_outer_quotes(value: str) -> str:
    s = value.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _extract_commit_message(cmd: str, argv: list[str]) -> str | None:
    if not _is_git_argv(argv):
        return None
    if "commit" not in [a.lower() for a in argv]:
        return None
    messages: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "-m" and i + 1 < len(argv):
            messages.append(_strip_outer_quotes(argv[i + 1]))
            i += 2
            continue
        if argv[i].startswith("-m") and len(argv[i]) > 2:
            messages.append(_strip_outer_quotes(argv[i][2:]))
        i += 1
    if messages:
        return "\n".join(messages)
    if re.search(r"\bgit\s+commit\b", cmd) and "-m" not in cmd:
        return None
    return None


def _git_history_rewrite_mode(policy: dict[str, Any]) -> str:
    return str((policy.get("modes") or {}).get("git_history_rewrite", "deny"))


def _history_rewrite_action(
    mode: str,
    user_msg: str,
    agent_msg: str,
    rule_id: str,
) -> dict[str, Any]:
    if mode in ("off", "allow"):
        return _allow_shell()
    if mode == "advisory":
        _emit_log("warn", "policy_would_deny", domain="shell-git", rule_id=rule_id)
        return _allow_shell()
    if mode == "log":
        _emit_log("info", "policy_would_deny", domain="shell-git", rule_id=rule_id)
        return _allow_shell()
    if mode == "ask":
        return _ask_shell(user_msg, agent_msg)
    return _deny_shell(user_msg, agent_msg)


def _amend_rewrites_pushed_history(git_root: Path) -> bool:
    """True when amend would rewrite a commit already reachable on the tracking branch."""
    if not (git_root / ".git").is_dir():
        return False
    try:
        status = subprocess.check_output(
            ["git", "-C", str(git_root), "status", "-sb"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        # Fail closed: cannot verify unpushed-only amend eligibility.
        return True
    first_line = status.splitlines()[0] if status else ""
    if "..." not in first_line:
        return False
    if "[ahead" in first_line and "[behind" not in first_line:
        return False
    return True


def _match_policy_pattern_rules(cmd: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    for rule in rules:
        pat = rule.get("pattern")
        if pat and re.search(pat, cmd):
            return rule
    return None


def _classify_git_history_rewrite(
    cmd: str, git_cfg: dict[str, Any], policy: dict[str, Any], git_root: Path | None
) -> dict[str, Any] | None:
    mode = _git_history_rewrite_mode(policy)
    if mode in ("off", "allow"):
        return None

    for rule in git_cfg.get("gh_merge_deny_flags") or []:
        pat = rule.get("pattern")
        if pat and re.search(pat, cmd):
            rule_id = str(rule.get("id", "gh_merge_flag"))
            return _history_rewrite_action(
                mode,
                f"Blocked: {rule_id.replace('_', ' ')} is not allowed by git-github-workflow policy.",
                "Use merge commit only; do not delete the branch. See git-github-workflow.mdc.",
                rule_id,
            )

    matched = _match_policy_pattern_rules(cmd, git_cfg.get("history_rewrite_deny") or [])
    if not matched:
        return None

    rule_id = str(matched.get("id", "history_rewrite"))
    if rule_id == "amend_pushed":
        if git_root and not _amend_rewrites_pushed_history(git_root):
            return None
        return _history_rewrite_action(
            mode,
            "Blocked: git commit --amend would rewrite history already on the remote.",
            "Amend only when the branch is ahead (unpushed). Add a new commit otherwise.",
            rule_id,
        )

    return _history_rewrite_action(
        mode,
        f"Blocked: {rule_id.replace('_', ' ')} rewrites git history.",
        "Use merge commits and forward fixes. Override via modes.git_history_rewrite in hook-policy.json "
        "only for documented emergencies.",
        rule_id,
    )


def _mcp_tool_arguments_denied(tool: str, args: dict[str, Any], policy: dict[str, Any]) -> bool:
    catalog = policy.get("_mcp_tools") or {}
    deny_when = (catalog.get("tool_arguments") or {}).get(tool, {}).get("deny_when")
    if not deny_when:
        return False
    for key, values in deny_when.items():
        val = args.get(key)
        if val is not None and str(val) in [str(v) for v in values]:
            return True
    return False


def classify_shell_git(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    logger.info("classify_shell_git_enter", extra={})
    cmd = _first(payload, ("command",))
    if not cmd:
        return _allow_shell()

    argv = _parse_argv(cmd)
    project_root = _project_root(payload)
    git_root = project_root
    cwd = payload.get("cwd")
    if cwd:
        git_root = Path(str(cwd))

    git_cfg = policy.get("git") or {}
    modes = policy.get("modes") or {}

    history_block = _classify_git_history_rewrite(cmd, git_cfg, policy, git_root)
    if history_block is not None:
        return history_block

    msg = _extract_commit_message(cmd, argv)
    if msg is not None:
        first_line = msg.splitlines()[0] if msg else ""
        max_len = int(git_cfg.get("max_subject_length", 72))
        min_len = int(git_cfg.get("min_subject_length", 10))
        fmt_mode = modes.get("git_commit_format", "deny")

        if len(first_line) > max_len:
            if fmt_mode == "advisory":
                return _allow_shell()
            return _deny_shell(
                f"Commit message first line too long ({len(first_line)} > {max_len} chars).",
                "Use prepare-atomic-commit: keep first line <= 72 chars.",
            )

        if len(first_line) < min_len:
            if fmt_mode == "advisory":
                return _allow_shell()
            return _deny_shell(
                "Commit message too short. Use imperative mood (e.g. 'Add X', 'Fix Y').",
                "Use prepare-atomic-commit for message format.",
            )

        skip = False
        if git_root and (git_root / ".cursor" / "allow-non-conventional-commit").is_file():
            skip = True
        if not skip and git_cfg.get("conventional_commits", True):
            pat = git_cfg.get(
                "conventional_pattern",
                r"^(feat|fix|chore|docs|refactor|test|style|perf|build|ci)(\([a-z0-9-]+\))?!?: .+",
            )
            if not re.match(pat, first_line):
                if fmt_mode == "advisory":
                    return _allow_shell()
                return _deny_shell(
                    "Commit message should follow conventional format: type(scope): description "
                    "(e.g. feat: add login). Create .cursor/allow-non-conventional-commit to skip.",
                    "Use prepare-atomic-commit for conventional commits.",
                )
    elif re.search(r"\bgit\s+commit\b", cmd):
        unparsed = modes.get("git_commit_unparsed", "allow")
        if unparsed == "deny":
            return _deny_shell(
                "Could not parse commit message for validation.",
                "Use git commit -m \"type(scope): description\" or prepare-atomic-commit.",
            )

    logger.info("classify_shell_git_exit", extra={"decision": "allow"})
    return _allow_shell()


def _mcp_risk_from_server_prefixes(tool: str, server_cfg: dict[str, Any]) -> str | None:
    """Apply per-server prefix_read/prefix_write from mcp_tools.json before global heuristics."""
    for prefix in server_cfg.get("prefix_read") or []:
        prefix_text = str(prefix)
        if prefix_text and tool.startswith(prefix_text):
            return "read"
    for prefix in server_cfg.get("prefix_write") or []:
        prefix_text = str(prefix)
        if prefix_text and tool.startswith(prefix_text):
            return "write"
    return None


def _mcp_risk_from_catalog(
    server: str, tool: str, args: dict[str, Any], policy: dict[str, Any]
) -> str:
    catalog = policy.get("_mcp_tools") or {}
    servers = catalog.get("servers") or {}
    tool_args_rules = catalog.get("tool_arguments") or {}

    if tool in ("mcp_auth",):
        return "read"

    server_cfg = servers.get(server) or {}
    tools_map = server_cfg.get("tools") or {}
    if tool in tools_map:
        base = tools_map[tool]
    else:
        base = "unknown"

    arg_rule = tool_args_rules.get(tool) or {}
    for risk, cond in (("write", arg_rule.get("write_when")), ("read", arg_rule.get("read_when"))):
        if not cond:
            continue
        match = True
        for key, values in cond.items():
            val = args.get(key)
            if val is None or str(val) not in [str(v) for v in values]:
                match = False
                break
        if match:
            return risk

    if base != "unknown":
        return base

    server_prefix_risk = _mcp_risk_from_server_prefixes(tool, server_cfg)
    if server_prefix_risk is not None:
        return server_prefix_risk

    heuristics = load_mcp_heuristics(policy)
    classified = classify_tool_name(tool, heuristics)
    if classified != "unknown":
        return classified

    default_srv = server_cfg.get("default_risk")
    if default_srv:
        return default_srv

    mcp_cfg = policy.get("mcp") or {}
    return mcp_cfg.get("default_unknown_risk", "unknown")


def classify_mcp(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    server = _first(payload, ("server", "server_name", "mcp_server"))
    tool = _first(payload, ("tool_name", "toolName", "name", "mcp_tool_name"))
    logger.info(
        "classify_mcp_enter",
        extra={"server": server or "(unknown)", "tool": tool or "(missing)"},
    )
    if not tool:
        logger.info("classify_mcp_exit", extra={"decision": "allow", "reason": "missing_tool"})
        return _allow_shell()

    args = payload.get("arguments") or payload.get("tool_input") or payload.get("args") or {}
    if not isinstance(args, dict):
        args = {}

    if _mcp_tool_arguments_denied(tool, args, policy):
        mode = _git_history_rewrite_mode(policy)
        logger.info("classify_mcp_denied_args", extra={"tool": tool, "mode": mode})
        return _history_rewrite_action(
            mode,
            f"MCP tool '{tool}' arguments violate git-github-workflow policy (e.g. squash/rebase merge).",
            "Use merge_method merge only; verify CI checks before merge_pull_request.",
            f"mcp_{tool}",
        )

    risk = _mcp_risk_from_catalog(server, tool, args, policy)
    modes = policy.get("modes") or {}
    mcp_cfg = policy.get("mcp") or {}
    logger.info("classify_mcp_risk", extra={"tool": tool, "risk": risk})

    if risk == "read":
        logger.info("classify_mcp_exit", extra={"decision": "allow", "risk": risk})
        return _allow_shell()

    if risk == "unknown":
        unknown_mode = modes.get("mcp_unknown", "ask")
        if unknown_mode in ("off", "allow"):
            return _allow_shell()
        if unknown_mode == "log":
            _emit_log("info", "policy_would_ask", domain="mcp", rule_id="mcp_unknown", tool=tool)
            return _allow_shell()
        return _ask_shell(
            f"MCP tool '{tool}' on server '{server}' is not cataloged. Approve only if intended.",
            "Add tool to hooks/policy/mcp_tools.json or .cursor/hook-policy.json with explicit risk.",
        )

    if risk in ("write", "admin"):
        is_db = bool(re.search(mcp_cfg.get("db_server_pattern", ""), server, re.I))
        risk_type = "DB-write or schema-change" if is_db else "state-changing"
        write_mode = modes.get("mcp_write", "ask")
        if write_mode in ("off", "allow"):
            return _allow_shell()
        if write_mode == "log":
            _emit_log(
                "info",
                "policy_would_ask",
                domain="mcp",
                rule_id="mcp_write",
                tool=tool,
                server=server,
            )
            return _allow_shell()
        return _ask_shell(
            f"MCP tool '{tool}' on server '{server}' looks {risk_type}. "
            "Approve only if this action is explicitly requested.",
            "Default policy: MCP operations should be read-only unless user explicitly asks for writes.",
        )

    logger.info("classify_mcp_exit", extra={"decision": "allow", "risk": risk})
    return _allow_shell()


def classify(domain: str, payload: dict[str, Any], project_root: Path | None) -> dict[str, Any]:
    logger.info("classify_enter", extra={"domain": domain, "has_project_root": project_root is not None})
    policy = load_policy(project_root)
    load_error = _policy_load_error_response(policy)
    if load_error is not None:
        logger.info("classify_exit", extra={"domain": domain, "decision": load_error.get("permission")})
        return load_error
    policy = {k: v for k, v in policy.items() if k != _POLICY_LOAD_FAILURES_KEY}
    if domain == "shell-db":
        result = classify_shell_db(payload, policy)
    elif domain == "shell-git":
        result = classify_shell_git(payload, policy)
    elif domain == "shell-destructive":
        result = classify_shell_destructive(payload, policy)
    elif domain == "pre-push":
        result = classify_pre_push(payload, policy)
    elif domain == "mcp":
        result = classify_mcp(payload, policy)
    else:
        result = _allow_shell()
    logger.info("classify_exit", extra={"domain": domain, "decision": result.get("permission")})
    return result


def main() -> int:
    if len(sys.argv) < 2:
        logger.info("main_exit", extra={"decision": "allow", "reason": "missing_domain"})
        print(json.dumps(_allow_shell()), end="")
        return 0
    domain = sys.argv[1]
    logger.info("main_enter", extra={"domain": domain})
    raw = sys.stdin.read()
    if not raw.strip():
        logger.info("main_exit", extra={"domain": domain, "decision": "allow", "reason": "empty_payload"})
        print(json.dumps(_allow_shell()), end="")
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _emit_log("warn", "invalid_hook_payload", domain=domain)
        logger.warning("main_invalid_payload", extra={"domain": domain})
        print(json.dumps(_allow_shell()), end="")
        return 0
    project_root = _project_root(payload)
    try:
        result = classify(domain, payload, project_root)
    except Exception as exc:
        policy = load_policy(project_root)
        policy = {k: v for k, v in policy.items() if k != _POLICY_LOAD_FAILURES_KEY}
        result = _policy_engine_error_response(policy, domain, exc)
        logger.error(
            "main_classify_failed",
            extra={"domain": domain, "error_type": type(exc).__name__},
        )
    logger.info("main_exit", extra={"domain": domain, "decision": result.get("permission")})
    print(json.dumps(result, separators=(",", ":")), end="")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
