"""Tests for sync-cursor.py."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sync_cursor = sys.modules["sync_cursor"]


def _run_sync(argv: list[str]) -> int:
    old_argv = sys.argv
    sys.argv = ["sync-cursor.py", *argv]
    try:
        return sync_cursor.main()
    finally:
        sys.argv = old_argv


def test_templates_to_local_creates_cursor_tree(tmp_project: Path) -> None:
    assert _run_sync(["--project-root", str(tmp_project), "--hooks-variant", "windows"]) == 0
    cursor = tmp_project / ".cursor"
    assert (cursor / "agents" / "agent_a.md").is_file()
    assert (cursor / "rules" / "rule_a.mdc").is_file()
    assert (cursor / "hooks" / "scripts" / "script.ps1").is_file()
    assert (cursor / "skills" / "foo" / "SKILL.md").is_file()
    assert (cursor / "USAGE.md").is_file()
    assert (cursor / "rules" / "RULES.md").is_file()
    assert not (cursor / "prompts").exists()


def test_templates_to_global_copies_commands_not_tests(tmp_project: Path) -> None:
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "TemplatesToGlobal"]) == 0
    global_commands = tmp_project / "home" / ".cursor" / "commands"
    assert (global_commands / "sync-cursor.py").is_file()
    assert (global_commands / "README.md").is_file()
    assert not (global_commands / "tests").exists()


def test_templates_to_local_hooks_variant_unix(tmp_project: Path) -> None:
    assert _run_sync(["--project-root", str(tmp_project), "--hooks-variant", "unix"]) == 0
    assert (tmp_project / ".cursor" / "hooks" / "scripts" / "script.sh").is_file()


def test_to_global_and_from_global_roundtrip(tmp_project: Path) -> None:
    local = tmp_project / ".cursor"
    local.mkdir()
    (local / "agents").mkdir()
    shutil.copy(
        tmp_project / "templates" / "agents" / "subagents" / "agent_a.md",
        local / "agents" / "agent_a.md",
    )
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "ToGlobal"]) == 0
    home_cursor = tmp_project / "home" / ".cursor"
    assert (home_cursor / "agents" / "agent_a.md").is_file()
    assert (home_cursor / "commands" / "sync-cursor.py").is_file()

    shutil.rmtree(local)
    shutil.rmtree(tmp_project / "templates" / "commands")
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "FromGlobal"]) == 0
    assert (local / "agents" / "agent_a.md").is_file()
    assert (tmp_project / "templates" / "commands" / "sync-cursor.py").is_file()


def test_sync_skills_prunes_stale(tmp_project: Path) -> None:
    stale = tmp_project / ".cursor" / "skills" / "stale" / "SKILL.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")
    _run_sync(["--project-root", str(tmp_project)])
    assert not stale.exists()
    assert (tmp_project / ".cursor" / "skills" / "foo" / "SKILL.md").is_file()


def test_sync_agents_prefers_templates_subagents(tmp_project: Path) -> None:
    global_agents = tmp_project / "home" / ".cursor" / "agents"
    global_agents.mkdir(parents=True)
    (global_agents / "global_only.md").write_text("# global", encoding="utf-8")
    _run_sync(["--project-root", str(tmp_project)])
    agents = tmp_project / ".cursor" / "agents"
    assert (agents / "agent_a.md").is_file()
    assert not (agents / "global_only.md").is_file()


def test_missing_templates_dirs_no_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sync_cursor.Path, "home", lambda: tmp_path / "home")
    (tmp_path / "templates").mkdir()
    assert _run_sync(["--project-root", str(tmp_path)]) == 0


def test_dry_run_no_files_written(tmp_project: Path) -> None:
    assert _run_sync(["--project-root", str(tmp_project), "--dry-run"]) == 0
    assert not (tmp_project / ".cursor").exists()


def test_verbose_emits_stderr_json(tmp_project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run_sync(["--project-root", str(tmp_project), "--dry-run", "--verbose"])
    err = capsys.readouterr().err
    assert "would_copy" in err
    assert json.loads(err.strip().splitlines()[0])["component"] == "sync_cursor"
