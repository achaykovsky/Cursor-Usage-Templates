"""Integration tests for redact-sensitive-read.ps1 stdout JSON contract.

Windows must pass through redact_sensitive.py JSON unchanged. Re-serializing
redacted bodies with ConvertTo-Json corrupts Unicode (e.g. em-dash) and breaks
Cursor beforeReadFile hooks.
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

REPO = Path(__file__).resolve().parents[3]
HOOK = REPO / ".cursor" / "hooks" / "scripts" / "redact-sensitive-read.ps1"
HOOK_COMMON = REPO / "templates" / "hooks" / "windows" / "hook-common.ps1"
HOOK_WINDOWS = Path(__file__).resolve().parents[1] / "windows"


def _pwsh() -> str:
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    pytest.skip("PowerShell not available")


def _deploy_hooks(hook_project: Path) -> None:
    scripts_dst = hook_project / ".cursor" / "hooks" / "scripts"
    policy_dst = hook_project / ".cursor" / "hooks" / "policy"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    policy_dst.mkdir(parents=True, exist_ok=True)
    for name in ("hook-common.ps1", "redact-sensitive-read.ps1"):
        shutil.copy2(HOOK_WINDOWS / name, scripts_dst / name)
    shutil.copy2(
        REPO / "templates" / "hooks" / "policy" / "redact_sensitive.py",
        policy_dst / "redact_sensitive.py",
    )


def _run_hook(project_root: Path, payload: dict, *, ensure_ascii: bool = True) -> tuple[int, str, str]:
    script = project_root / ".cursor" / "hooks" / "scripts" / "redact-sensitive-read.ps1"
    if not script.is_file():
        pytest.skip("redact-sensitive-read.ps1 not deployed")

    raw = json.dumps(payload, ensure_ascii=ensure_ascii)
    proc = subprocess.run(
        [
            _pwsh(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ],
        input=raw.encode("utf-8"),
        capture_output=True,
        cwd=str(project_root),
        timeout=60,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, stdout, stderr


def _assert_valid_hook_json(stdout: str, stderr: str, code: int) -> dict:
    assert code == 0, stderr
    lines = [line for line in stdout.splitlines() if line.strip()]
    assert len(lines) == 1, stdout[:200]
    return json.loads(lines[0])


@pytest.fixture()
def hook_project(tmp_path: Path) -> Path:
    _deploy_hooks(tmp_path)
    return tmp_path


def test_redact_read_plain_file_allows(hook_project: Path) -> None:
    payload = {
        "file_path": "README.md",
        "content": "hello",
        "workspace_roots": [str(hook_project)],
    }
    code, stdout, stderr = _run_hook(hook_project, payload)
    result = _assert_valid_hook_json(stdout, stderr, code)
    assert result["permission"] == "allow"


def test_redact_read_unicode_body_json_is_valid(hook_project: Path) -> None:
    """Regression: ConvertTo-Json re-serialization broke on em-dash in hook-common.ps1."""
    content = HOOK_COMMON.read_text(encoding="utf-8")
    payload = {
        "hook_event_name": "beforeReadFile",
        "file_path": str(HOOK_COMMON),
        "content": content,
        "workspace_roots": [str(hook_project)],
    }
    code, stdout, stderr = _run_hook(hook_project, payload, ensure_ascii=False)
    result = _assert_valid_hook_json(stdout, stderr, code)
    assert result["permission"] == "allow"
    if "content" in result:
        assert "super-secret" not in result["content"]


def test_redact_read_sensitive_env_redacts(hook_project: Path) -> None:
    payload = {
        "file_path": str(hook_project / ".env"),
        "content": "API_KEY=super-secret\n",
        "workspace_roots": [str(hook_project)],
    }
    code, stdout, stderr = _run_hook(hook_project, payload)
    result = _assert_valid_hook_json(stdout, stderr, code)
    assert result["permission"] == "allow"
    assert "content" in result
    assert "super-secret" not in result["content"]
    assert "***REDACTED***" in result["content"]


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
