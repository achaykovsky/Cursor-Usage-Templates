"""Integration tests for log-resource-usage hook ledger fields.

Spawns the real PowerShell hook against a deployed script copy because ledger
shape is defined by hook-common.ps1, not Python. Skips when pwsh is unavailable.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from _hooks_bootstrap import run_test_file

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "before-submit-prompt.json"
FIXTURE_AGENTS = Path(__file__).resolve().parent / "fixtures" / "before-submit-prompt-agents.json"
FIXTURE_CLEANUP = Path(__file__).resolve().parent / "fixtures" / "before-submit-prompt-cleanup.json"


def _pwsh() -> str:
    """Prefer pwsh (Core) over Windows PowerShell 5.x for consistent UTF-8 behavior."""
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    pytest.skip("PowerShell not available")


def _payload(project_root: Path, fixture: Path = FIXTURE) -> bytes:
    """Substitute project root into fixture JSON — hooks resolve paths from workspace_roots."""
    raw = fixture.read_text(encoding="utf-8")
    raw = raw.replace("__PROJECT_ROOT__", str(project_root).replace("\\", "/"))
    return raw.encode("utf-8")


def _run_hook(project_root: Path, stdin_bytes: bytes) -> tuple[int, str, str]:
    """Execute log-resource-usage.ps1 with hook stdin bytes; boundary mock at subprocess."""
    script = project_root / ".cursor" / "hooks" / "scripts" / "log-resource-usage.ps1"
    common = script.parent / "hook-common.ps1"
    if not script.is_file() or not common.is_file():
        pytest.skip("hook scripts not deployed under .cursor/hooks/scripts")

    proc = subprocess.run(
        [
            _pwsh(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ],
        input=stdin_bytes,
        capture_output=True,
        cwd=str(project_root),
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace"), proc.stderr.decode(
        "utf-8", errors="replace"
    )


def _deploy_hooks(hook_project: Path, templates_root: Path) -> None:
    """Copy only the scripts under test — avoids full sync-cursor for faster isolation."""
    scripts_dst = hook_project / ".cursor" / "hooks" / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for name in ("hook-common.ps1", "log-resource-usage.ps1"):
        src = templates_root / "hooks" / "windows" / name
        shutil.copy2(src, scripts_dst / name)
    hooks_json = templates_root / "hooks" / "windows" / "hooks.json"
    if not hooks_json.is_file():
        hooks_json = templates_root / "hooks" / "hooks.json"
    if hooks_json.is_file():
        shutil.copy2(hooks_json, hook_project / ".cursor" / "hooks.json")


def _deploy_subagent_catalog(hook_project: Path, templates_root: Path) -> None:
    """Copy subagent .md files so prompt path references resolve to frontmatter invoke names."""
    src = templates_root / "agents" / "subagents"
    dst = hook_project / "templates" / "agents" / "subagents"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _deploy_routing(hook_project: Path, templates_root: Path) -> None:
    """Copy routing.py shim and routing/ package for hook prompt predictions."""
    src_commands = templates_root / "commands"
    dst = hook_project / "templates" / "commands"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_commands / "routing.py", dst / "routing.py")
    shutil.copytree(src_commands / "routing", dst / "routing", dirs_exist_ok=True)


@pytest.fixture
def hook_project(tmp_path: Path) -> Path:
    """Minimal git workspace with hook scripts copied from templates."""
    templates_root = Path(__file__).resolve().parents[2]
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".git").mkdir()
    _deploy_hooks(project, templates_root)
    _deploy_routing(project, templates_root)
    return project


def test_before_submit_prompt_records_hooks_executed(hook_project: Path) -> None:
    """beforeSubmitPrompt must seed hooks_executed with this hook's event:script entry."""
    code, _, stderr = _run_hook(hook_project, _payload(hook_project))
    assert code == 0, stderr

    ledger = json.loads(
        (hook_project / "logs" / "resource-ledger" / "active.json").read_text(encoding="utf-8")
    )
    executed = ledger.get("hooks_executed") or []
    assert "beforeSubmitPrompt:log-resource-usage.ps1" in executed
    configured = ledger.get("hooks_configured") or []
    assert len(configured) > len(executed)


def _run_hook_script(project_root: Path, script_name: str, stdin_bytes: bytes) -> tuple[int, str, str]:
    script = project_root / ".cursor" / "hooks" / "scripts" / script_name
    if not script.is_file():
        pytest.skip(f"{script_name} not deployed")
    proc = subprocess.run(
        [_pwsh(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        input=stdin_bytes,
        capture_output=True,
        cwd=str(project_root),
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace"), proc.stderr.decode(
        "utf-8", errors="replace"
    )


def test_register_hook_execution_appends_from_other_scripts(hook_project: Path) -> None:
    """Non-ledger hooks must append to hooks_executed via Register-HookExecution."""
    templates_root = Path(__file__).resolve().parents[2]
    scripts_dst = hook_project / ".cursor" / "hooks" / "scripts"
    for name in ("hook-common.ps1", "log-resource-usage.ps1", "log-prompt-context.ps1"):
        shutil.copy2(templates_root / "hooks" / "windows" / name, scripts_dst / name)

    payload_bytes = _payload(hook_project)
    code, _, stderr = _run_hook(hook_project, payload_bytes)
    assert code == 0, stderr

    code, _, stderr = _run_hook_script(hook_project, "log-prompt-context.ps1", payload_bytes)
    assert code == 0, stderr

    ledger = json.loads(
        (hook_project / "logs" / "resource-ledger" / "active.json").read_text(encoding="utf-8")
    )
    executed = set(ledger.get("hooks_executed") or [])
    assert "beforeSubmitPrompt:log-resource-usage.ps1" in executed
    assert "beforeSubmitPrompt:log-prompt-context.ps1" in executed


def test_before_submit_prompt_records_model_and_token_estimate(hook_project: Path) -> None:
    """beforeSubmitPrompt must populate active.json with model slug and char-based token estimate."""
    # Act
    code, stdout, stderr = _run_hook(hook_project, _payload(hook_project))
    assert code == 0, stderr
    assert "allow" in stdout

    # Assert — ledger fields used for log archival (not shown in agent Resources used table)
    active = hook_project / "logs" / "resource-ledger" / "active.json"
    assert active.is_file()
    ledger = json.loads(active.read_text(encoding="utf-8"))

    assert ledger["generation_id"] == "gen-test-1"
    assert ledger["model"] == "composer-2.5-fast"
    assert ledger["tokens"]["estimated"] is True
    assert ledger["tokens"]["input_tokens"] > 0
    assert ledger["prompt_chars"] > 0


def test_before_submit_prompt_records_agents_requested(hook_project: Path) -> None:
    """Prompt @agent() and subagents/*.md paths must populate agents_requested for the ledger."""
    templates_root = Path(__file__).resolve().parents[2]
    _deploy_subagent_catalog(hook_project, templates_root)

    code, _, stderr = _run_hook(hook_project, _payload(hook_project, FIXTURE_AGENTS))
    assert code == 0, stderr

    ledger = json.loads(
        (hook_project / "logs" / "resource-ledger" / "active.json").read_text(encoding="utf-8")
    )
    requested = set(ledger.get("agents_requested") or [])
    assert {"DOCS", "BACKEND_PYTHON", "TESTER"}.issubset(requested)


def test_before_submit_prompt_records_skills_matched(hook_project: Path) -> None:
    """Cleanup/review prompt wording must populate skills_matched for the Resources used table."""
    code, _, stderr = _run_hook(hook_project, _payload(hook_project, FIXTURE_CLEANUP))
    assert code == 0, stderr

    ledger = json.loads(
        (hook_project / "logs" / "resource-ledger" / "active.json").read_text(encoding="utf-8")
    )
    matched = set(ledger.get("skills_matched") or [])
    assert "audit-codebase-cleanup" in matched
    assert "review-pull-request" in matched
    assert "security-scan-changes" in matched


def test_before_submit_prompt_utf8_bom_stdin(hook_project: Path) -> None:
    """UTF-8 BOM stdin must still populate active.json (Windows Cursor hook pipe)."""
    payload = b"\xef\xbb\xbf" + _payload(hook_project)
    code, stdout, stderr = _run_hook(hook_project, payload)
    assert code == 0, stderr
    assert "allow" in stdout

    ledger = json.loads(
        (hook_project / "logs" / "resource-ledger" / "active.json").read_text(encoding="utf-8")
    )
    assert ledger["generation_id"] == "gen-test-1"
    assert ledger["prompt_chars"] > 0


def test_before_submit_prompt_utf16_le_stdin(hook_project: Path) -> None:
    """UTF-16-LE stdin without BOM must still populate active.json."""
    payload = _payload(hook_project).decode("utf-8").encode("utf-16-le")
    code, _, stderr = _run_hook(hook_project, payload)
    assert code == 0, stderr

    ledger = json.loads(
        (hook_project / "logs" / "resource-ledger" / "active.json").read_text(encoding="utf-8")
    )
    assert ledger["generation_id"] == "gen-test-1"
    assert ledger["prompt_chars"] > 0


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
