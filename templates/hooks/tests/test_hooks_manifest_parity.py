"""Manifest parity and generated hooks JSON freshness tests."""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from _hooks_bootstrap import run_test_file

HOOKS_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = HOOKS_ROOT / "manifest"
GENERATOR = MANIFEST_DIR / "generate_hooks_json.py"

# Shared library script — not wired in hooks.json
SKIP_SCRIPTS = frozenset({"hook-common"})


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_hooks_json", GENERATOR)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {GENERATOR}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_manifest() -> dict:
    gen = _load_generator()
    return gen._load_yaml(MANIFEST_DIR / "hooks.manifest.yaml")


def _hook_scripts_in_dir(directory: Path, suffix: str) -> set[str]:
    if not directory.is_dir():
        return set()
    return {
        p.stem
        for p in directory.iterdir()
        if p.is_file() and p.suffix == suffix and p.stem not in SKIP_SCRIPTS
    }


def test_manifest_scripts_match_windows_and_unix() -> None:
    """Every manifest script must exist on both platforms (minus hook-common)."""
    manifest = _load_manifest()
    gen = _load_generator()
    manifest_scripts = gen.manifest_script_names(manifest)
    win = _hook_scripts_in_dir(HOOKS_ROOT / "windows", ".ps1")
    unix = _hook_scripts_in_dir(HOOKS_ROOT / "unix", ".sh")

    assert manifest_scripts, "manifest must reference at least one script"
    assert manifest_scripts == win, f"windows mismatch: manifest={manifest_scripts - win} extra={win - manifest_scripts}"
    assert manifest_scripts == unix, (
        f"unix mismatch: manifest={manifest_scripts - unix} extra={unix - manifest_scripts}"
    )


def test_generated_hooks_json_matches_generator_output() -> None:
    """Committed windows/unix hooks JSON must match what the generator would write."""
    gen = _load_generator()
    manifest = gen._load_yaml(MANIFEST_DIR / "hooks.manifest.yaml")
    outputs = gen.generate_all(manifest)
    stale = gen.check_generated(HOOKS_ROOT, outputs)
    assert not stale, f"stale hooks JSON: {stale}; run generate_hooks_json.py"


def test_generate_hooks_json_check_mode_passes() -> None:
    """CLI --check exits 0 when OS hooks JSON is current."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=HOOKS_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
