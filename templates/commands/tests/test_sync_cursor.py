"""Tests for sync-cursor.py.

Exercises template-to-local, template-to-global, round-trip, pruning, and
dry-run paths. Sync must never copy test directories into global commands or
leave stale skills after template removals.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _commands_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import shutil
import sys
from pathlib import Path

import pytest

from _commands_bootstrap import run_test_file
from _sync_bootstrap import load_sync_cursor

sync_cursor = load_sync_cursor()


def _run_sync(argv: list[str]) -> int:
    """Invoke sync-cursor.main() with a controlled argv — mirrors CLI entry without subprocess."""
    old_argv = sys.argv
    sys.argv = ["sync-cursor.py", *argv]
    try:
        return sync_cursor.main()
    finally:
        sys.argv = old_argv


def test_templates_to_local_creates_cursor_tree(tmp_project: Path) -> None:
    """Default mode materializes the full .cursor tree from minimal templates."""
    # Act
    assert _run_sync(["--project-root", str(tmp_project), "--hooks-variant", "windows"]) == 0
    # Assert — each component type lands under .cursor; prompts stay template-only
    cursor = tmp_project / ".cursor"
    assert (cursor / "agents" / "agent_a.md").is_file()
    assert (cursor / "rules" / "rule_a.mdc").is_file()
    assert (cursor / "hooks" / "scripts" / "script.ps1").is_file()
    assert (cursor / "skills" / "foo" / "SKILL.md").is_file()
    assert (cursor / "USAGE.md").is_file()
    assert (cursor / "rules" / "RULES.md").is_file()
    assert not (cursor / "prompts").exists()


def test_templates_to_global_copies_commands_not_tests(tmp_project: Path) -> None:
    """Global sync ships runnable commands but excludes pytest fixtures and test suites."""
    # Act
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "TemplatesToGlobal"]) == 0
    # Assert
    global_commands = tmp_project / "home" / ".cursor" / "commands"
    assert (global_commands / "sync-cursor.py").is_file()
    assert (global_commands / "README.md").is_file()
    assert not (global_commands / "tests").exists()


def test_templates_to_global_skips_pycache_in_routing(tmp_project: Path) -> None:
    """Global sync copies routing *.py only — never __pycache__ or other repo artifacts."""
    routing = tmp_project / "templates" / "commands" / "routing"
    routing.mkdir()
    (routing / "__init__.py").write_text("# routing package\n", encoding="utf-8")
    pycache = routing / "__pycache__"
    pycache.mkdir()
    (pycache / "init.cpython-313.pyc").write_bytes(b"fake bytecode")

    assert _run_sync(["--project-root", str(tmp_project), "--mode", "TemplatesToGlobal"]) == 0

    global_routing = tmp_project / "home" / ".cursor" / "commands" / "routing"
    assert (global_routing / "__init__.py").is_file()
    assert not (global_routing / "__pycache__").exists()


def test_from_global_skips_pycache_already_in_global(tmp_project: Path) -> None:
    """FromGlobal copies ~/.cursor/ into project .cursor/ only — never templates/commands/."""
    routing = tmp_project / "templates" / "commands" / "routing"
    routing.mkdir()
    (routing / "__init__.py").write_text("# routing\n", encoding="utf-8")

    assert _run_sync(["--project-root", str(tmp_project), "--mode", "TemplatesToGlobal"]) == 0
    global_routing = tmp_project / "home" / ".cursor" / "commands" / "routing"
    stale = global_routing / "__pycache__"
    stale.mkdir()
    (stale / "stale.cpython-313.pyc").write_bytes(b"stale")

    shutil.rmtree(tmp_project / ".cursor", ignore_errors=True)
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "FromGlobal"]) == 0

    cursor = tmp_project / ".cursor"
    assert (cursor / "agents" / "agent_a.md").is_file()
    assert (tmp_project / "templates" / "commands" / "routing" / "__init__.py").is_file()
    assert not (tmp_project / "templates" / "commands" / "routing" / "__pycache__").exists()


def test_templates_to_global_then_from_global_roundtrip(tmp_project: Path) -> None:
    """TemplatesToGlobal then FromGlobal restores project .cursor/ from global (templates-derived)."""
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "TemplatesToGlobal"]) == 0
    home_cursor = tmp_project / "home" / ".cursor"
    assert (home_cursor / "agents" / "agent_a.md").is_file()

    shutil.rmtree(tmp_project / ".cursor", ignore_errors=True)
    assert _run_sync(["--project-root", str(tmp_project), "--mode", "FromGlobal"]) == 0

    local = tmp_project / ".cursor"
    assert (local / "agents" / "agent_a.md").is_file()
    assert (local / "rules" / "rule_a.mdc").is_file()


def test_trigger_file_syncs_matching_component_only(tmp_project: Path) -> None:
    """--trigger-file limits TemplatesToLocal to the edited templates subtree."""
    rule = tmp_project / "templates" / "rules" / "rule_a.mdc"
    rule.write_text("---\ndescription: x\n---\n# rule\n", encoding="utf-8")
    shutil.rmtree(tmp_project / ".cursor", ignore_errors=True)

    assert (
        _run_sync(
            [
                "--project-root",
                str(tmp_project),
                "--trigger-file",
                str(rule),
            ]
        )
        == 0
    )
    cursor = tmp_project / ".cursor"
    assert (cursor / "rules" / "rule_a.mdc").is_file()
    assert not (cursor / "agents").exists()


def test_trigger_file_skips_non_syncable_templates_path(tmp_project: Path) -> None:
    """Edits under templates/commands/ do not materialize .cursor/."""
    cmd = tmp_project / "templates" / "commands" / "sync-cursor.py"
    shutil.rmtree(tmp_project / ".cursor", ignore_errors=True)
    assert (
        _run_sync(
            [
                "--project-root",
                str(tmp_project),
                "--trigger-file",
                str(cmd),
            ]
        )
        == 0
    )
    assert not (tmp_project / ".cursor").exists()


def test_templates_to_local_hooks_only_skips_agents_and_rules(tmp_project: Path) -> None:
    """--components hooks copies hooks tree only."""
    assert _run_sync(["--project-root", str(tmp_project), "--components", "hooks", "--hooks-variant", "windows"]) == 0
    cursor = tmp_project / ".cursor"
    assert (cursor / "hooks" / "scripts" / "script.ps1").is_file()
    assert not (cursor / "agents").exists()
    assert not (cursor / "rules").exists()
    assert not (cursor / "skills").exists()


def test_templates_to_local_hooks_and_rules(tmp_project: Path) -> None:
    """--components hooks,rules syncs both bundles."""
    assert (
        _run_sync(
            [
                "--project-root",
                str(tmp_project),
                "--components",
                "hooks,rules",
                "--hooks-variant",
                "windows",
            ]
        )
        == 0
    )
    cursor = tmp_project / ".cursor"
    assert (cursor / "hooks" / "scripts" / "script.ps1").is_file()
    assert (cursor / "rules" / "rule_a.mdc").is_file()
    assert not (cursor / "agents").exists()


def test_invalid_components_exits_nonzero(tmp_project: Path) -> None:
    """Unknown --components values return exit code 2."""
    assert _run_sync(["--project-root", str(tmp_project), "--components", "hooks,invalid"]) == 2


def test_templates_to_local_hooks_variant_unix(tmp_project: Path) -> None:
    """--hooks-variant unix selects shell scripts instead of PowerShell hooks."""
    # Act
    assert _run_sync(["--project-root", str(tmp_project), "--hooks-variant", "unix"]) == 0
    # Assert
    assert (tmp_project / ".cursor" / "hooks" / "scripts" / "script.sh").is_file()


def test_sync_skills_prunes_stale(tmp_project: Path) -> None:
    """Sync removes skills absent from templates — stale dirs must not linger after refresh."""
    # Arrange
    stale = tmp_project / ".cursor" / "skills" / "stale" / "SKILL.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")
    # Act
    _run_sync(["--project-root", str(tmp_project)])
    # Assert
    assert not stale.exists()
    assert (tmp_project / ".cursor" / "skills" / "foo" / "SKILL.md").is_file()



def test_sync_agents_never_reads_global_fallback(tmp_project: Path) -> None:
    """Agents sync only from templates/subagents — never from ~/.cursor/agents/."""
    global_agents = tmp_project / "home" / ".cursor" / "agents"
    global_agents.mkdir(parents=True)
    (global_agents / "global_only.md").write_text("# global", encoding="utf-8")
    shutil.rmtree(tmp_project / "templates" / "agents" / "subagents", ignore_errors=True)

    _run_sync(["--project-root", str(tmp_project)])
    assert not (tmp_project / ".cursor" / "agents" / "global_only.md").exists()
    assert not (tmp_project / ".cursor" / "agents").exists()


def test_sync_agents_prefers_templates_subagents(tmp_project: Path) -> None:
    """Project sync sources agents from templates/subagents, not orphaned global-only files."""
    # Arrange — global agent that should not appear in project sync output
    global_agents = tmp_project / "home" / ".cursor" / "agents"
    global_agents.mkdir(parents=True)
    (global_agents / "global_only.md").write_text("# global", encoding="utf-8")
    # Act
    _run_sync(["--project-root", str(tmp_project)])
    # Assert
    agents = tmp_project / ".cursor" / "agents"
    assert (agents / "agent_a.md").is_file()
    assert not (agents / "global_only.md").is_file()


def test_missing_templates_dirs_no_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty templates tree should exit cleanly — sync is invoked in partial checkouts."""
    monkeypatch.setattr(sync_cursor.Path, "home", lambda: tmp_path / "home")
    (tmp_path / "templates").mkdir()
    assert _run_sync(["--project-root", str(tmp_path)]) == 0


def test_dry_run_no_files_written(tmp_project: Path) -> None:
    """--dry-run previews copies without touching the filesystem."""
    assert _run_sync(["--project-root", str(tmp_project), "--dry-run"]) == 0
    assert not (tmp_project / ".cursor").exists()


def test_verbose_emits_stderr_json(tmp_project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verbose dry-run logs structured JSON to stderr so stdout stays machine-parseable."""
    _run_sync(["--project-root", str(tmp_project), "--dry-run", "--verbose"])
    err = capsys.readouterr().err
    assert "would_copy" in err
    assert json.loads(err.strip().splitlines()[0])["component"] == "sync_cursor"


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
