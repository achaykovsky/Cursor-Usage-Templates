"""Integration tests for log-prompt-context hook stdin decoding.

Cursor may pipe UTF-8, UTF-8 BOM, or UTF-16-LE stdin on Windows; the hook
must decode all variants without corrupting prompt text or parse metadata.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from _hooks_bootstrap import run_test_file

HOOKS_WINDOWS = Path(__file__).resolve().parents[1] / "windows"
COMMANDS_DIR = Path(__file__).resolve().parents[2] / "commands"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "before-submit-prompt.json"


def _pwsh() -> str:
    """Resolve PowerShell executable — integration tests require a real shell host."""
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    pytest.skip("PowerShell not available")


def _payload(project_root: Path) -> bytes:
    """Build UTF-8 hook payload with workspace root substituted for fixture paths."""
    raw = FIXTURE.read_text(encoding="utf-8")
    raw = raw.replace("__PROJECT_ROOT__", str(project_root).replace("\\", "/"))
    return raw.encode("utf-8")


def _run_hook(
    project_root: Path,
    stdin_bytes: bytes,
    *,
    hook_script: Path | None = None,
) -> tuple[int, str, str]:
    """Run log-prompt-context.ps1; text=False preserves raw bytes for encoding tests."""
    script = hook_script or (project_root / ".cursor" / "hooks" / "scripts" / "log-prompt-context.ps1")
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
        text=False,
        cwd=str(project_root),
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, stdout, stderr


def _latest_log_line(project_root: Path) -> dict:
    """Read the most recent JSONL row — hooks append one line per beforeSubmitPrompt."""
    log_file = project_root / "logs" / f"{date.today():%Y-%m-%d}" / "cursor-prompt-context.jsonl"
    assert log_file.is_file(), f"missing log file: {log_file}"
    lines = [ln for ln in log_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert lines, "log file is empty"
    return json.loads(lines[-1])


@pytest.fixture
def hook_project(tmp_path: Path) -> Path:
    """Minimal project tree with synced hook scripts and routing.py for predictions."""
    scripts_dir = tmp_path / ".cursor" / "hooks" / "scripts"
    policy_dir = tmp_path / ".cursor" / "hooks" / "policy"
    scripts_dir.mkdir(parents=True)
    policy_dir.mkdir(parents=True)
    hooks_policy = Path(__file__).resolve().parents[1] / "policy"
    for name in ("hook-common.ps1", "log-prompt-context.ps1"):
        shutil.copy2(HOOKS_WINDOWS / name, scripts_dir / name)
    shutil.copy2(hooks_policy / "redact_sensitive.py", policy_dir / "redact_sensitive.py")
    commands_dir = tmp_path / "templates" / "commands"
    commands_dir.mkdir(parents=True)
    shutil.copy2(COMMANDS_DIR / "routing.py", commands_dir / "routing.py")
    shutil.copytree(COMMANDS_DIR / "routing", commands_dir / "routing", dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_log_prompt_context_utf8_stdin(hook_project: Path) -> None:
    """Standard UTF-8 stdin must parse cleanly and log prompt plus correlation IDs."""
    # Arrange
    payload = _payload(hook_project)
    # Act
    code, stdout, stderr = _run_hook(hook_project, payload, hook_script=hook_project / ".cursor" / "hooks" / "scripts" / "log-prompt-context.ps1")
    assert code == 0, stderr
    assert '"permission":"allow"' in stdout.replace(" ", "")

    # Assert
    row = _latest_log_line(hook_project)
    assert row["source"]["has_payload_json"] is True
    assert row["source"]["parse_error"] is None
    assert row["prompt"] == "Add structured logging to the payments module"
    assert row["conversation_id"] == "conv-test-1"
    assert row["generation_id"] == "gen-test-1"
    assert row.get("model") == "composer-2.5-fast"
    assert row["skills"] == []
    assert isinstance(row["predicted_skills"], list)
    assert isinstance(row["predicted_rules"], list)
    assert row["source"].get("prediction_source") == "routing.py"
    assert "security.mdc" in row["predicted_rules"]


def test_log_prompt_context_redacts_secrets_in_prompt(hook_project: Path) -> None:
    """Prompt bodies logged to disk must redact env-style and bearer secrets."""
    raw = FIXTURE.read_text(encoding="utf-8")
    raw = raw.replace("__PROJECT_ROOT__", str(hook_project).replace("\\", "/"))
    payload = json.loads(raw)
    payload["prompt"] = 'Use key API_KEY=super-secret and Bearer eyJhbGciOiJIUzI1NiJ9.a.b'
    stdin = json.dumps(payload).encode("utf-8")

    code, _, stderr = _run_hook(
        hook_project,
        stdin,
        hook_script=hook_project / ".cursor" / "hooks" / "scripts" / "log-prompt-context.ps1",
    )
    assert code == 0, stderr

    row = _latest_log_line(hook_project)
    assert "super-secret" not in row["prompt"]
    assert "eyJhbGciOi" not in row["prompt"]
    assert "***REDACTED***" in row["prompt"]


def test_log_prompt_context_utf8_bom_stdin(hook_project: Path) -> None:
    """UTF-8 BOM prefix is common on Windows — strip it without mangling JSON keys."""
    payload = b"\xef\xbb\xbf" + _payload(hook_project)
    code, stdout, stderr = _run_hook(hook_project, payload, hook_script=hook_project / ".cursor" / "hooks" / "scripts" / "log-prompt-context.ps1")
    assert code == 0, stderr

    row = _latest_log_line(hook_project)
    assert row["source"]["has_payload_json"] is True
    assert row["source"]["parse_error"] is None
    assert row["prompt"] == "Add structured logging to the payments module"
    # Regression guard: mis-decoded BOM produced replacement chars in parse_error
    assert "∩" not in (row["source"].get("parse_error") or "")


def test_log_prompt_context_utf16_le_stdin(hook_project: Path) -> None:
    """Some Cursor builds emit UTF-16-LE; hook must detect encoding without a BOM."""
    text = _payload(hook_project).decode("utf-8")
    payload = text.encode("utf-16-le")
    code, _, stderr = _run_hook(hook_project, payload, hook_script=hook_project / ".cursor" / "hooks" / "scripts" / "log-prompt-context.ps1")
    assert code == 0, stderr

    row = _latest_log_line(hook_project)
    assert row["source"]["has_payload_json"] is True
    assert row["prompt"] == "Add structured logging to the payments module"


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
