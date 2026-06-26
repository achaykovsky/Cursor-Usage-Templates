#!/usr/bin/env python3
"""Generate platform hooks JSON from hooks.manifest.yaml.

Writes OS-specific JSON next to scripts under templates/hooks/:
  windows/hooks.json
  windows/hooks.global.json
  unix/hooks.json
  unix/hooks.global.json

Usage:
  python generate_hooks_json.py          # write files
  python generate_hooks_json.py --check  # exit 1 if OS hooks JSON would change
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MANIFEST_NAME = "hooks.manifest.yaml"

# (platform subdir, output filename) -> command path template
OUTPUT_SPECS: dict[tuple[str, str], dict[str, str]] = {
    ("windows", "hooks.json"): {
        "prefix": "pwsh -NoProfile -ExecutionPolicy Bypass -File ",
        "dir": ".cursor/hooks/scripts",
        "ext": ".ps1",
        "join": "/",
    },
    ("unix", "hooks.json"): {
        "prefix": "bash ",
        "dir": ".cursor/hooks/scripts",
        "ext": ".sh",
        "join": "/",
    },
    ("windows", "hooks.global.json"): {
        "prefix": 'pwsh -NoProfile -ExecutionPolicy Bypass -File "',
        "dir": "%USERPROFILE%\\.cursor\\hooks\\scripts",
        "ext": ".ps1",
        "join": "\\",
        "suffix": '"',
    },
    ("unix", "hooks.global.json"): {
        "prefix": 'bash "$HOME/.cursor/hooks/scripts/',
        "dir": "",
        "ext": '.sh"',
        "join": "",
    },
}


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load manifest YAML; PyYAML required."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required: pip install pyyaml (or poetry install --with dev)"
        ) from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a mapping: {path}")
    return data


def _script_path(template: dict[str, str], script: str) -> str:
    """Build full command path for one script entry."""
    ext = template["ext"]
    joiner = template["join"]
    prefix = template["prefix"]
    suffix = template.get("suffix", "")
    dir_part = template["dir"]
    if dir_part == "":
        return f"{prefix}{script}{ext}"
    if joiner == "\\":
        return f'{prefix}{dir_part}{joiner}{script}{ext}{suffix}'
    return f"{prefix}{dir_part}{joiner}{script}{ext}{suffix}"


def _build_hook_entry(script: str, template: dict[str, str], matcher: str | None) -> dict[str, str]:
    entry: dict[str, str] = {"command": _script_path(template, script)}
    if matcher:
        entry["matcher"] = matcher
    return entry


def generate_all(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    """Return {(platform, filename): hooks_json} for each OS output."""
    version = manifest.get("version", 1)
    hooks_spec = manifest.get("hooks", {})
    if not isinstance(hooks_spec, dict):
        raise ValueError("manifest.hooks must be a mapping")

    outputs: dict[tuple[str, str], dict[str, Any]] = {}
    for key, path_template in OUTPUT_SPECS.items():
        hooks_out: dict[str, list[dict[str, str]]] = {}
        for event, entries in hooks_spec.items():
            if not isinstance(entries, list):
                raise ValueError(f"hooks.{event} must be a list")
            built: list[dict[str, str]] = []
            for item in entries:
                if not isinstance(item, dict) or "script" not in item:
                    raise ValueError(f"invalid entry under hooks.{event}: {item!r}")
                matcher = item.get("matcher")
                built.append(
                    _build_hook_entry(
                        str(item["script"]),
                        path_template,
                        str(matcher) if matcher is not None else None,
                    )
                )
            hooks_out[str(event)] = built
        outputs[key] = {"version": version, "hooks": hooks_out}
    return outputs


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _output_path(hooks_root: Path, platform: str, filename: str) -> Path:
    return hooks_root / platform / filename


def write_generated(hooks_root: Path, outputs: dict[tuple[str, str], dict[str, Any]]) -> list[str]:
    """Write all OS hooks JSON files; return list of written paths."""
    written: list[str] = []
    for (platform, filename), payload in outputs.items():
        dest = _output_path(hooks_root, platform, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_canonical_json(payload), encoding="utf-8")
        written.append(str(dest))
    return written


def check_generated(hooks_root: Path, outputs: dict[tuple[str, str], dict[str, Any]]) -> list[str]:
    """Return list of relative paths that differ from expected content."""
    stale: list[str] = []
    for (platform, filename), payload in outputs.items():
        dest = _output_path(hooks_root, platform, filename)
        rel = f"{platform}/{filename}"
        expected = _canonical_json(payload)
        if not dest.is_file() or dest.read_text(encoding="utf-8") != expected:
            stale.append(rel)
    return stale


def manifest_script_names(manifest: dict[str, Any]) -> set[str]:
    """Collect script basenames referenced in the manifest."""
    names: set[str] = set()
    hooks_spec = manifest.get("hooks", {})
    if not isinstance(hooks_spec, dict):
        return names
    for entries in hooks_spec.values():
        if not isinstance(entries, list):
            continue
        for item in entries:
            if isinstance(item, dict) and "script" in item:
                names.add(str(item["script"]))
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate platform hooks JSON from manifest.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to hooks.manifest.yaml (default: alongside this script)",
    )
    parser.add_argument(
        "--hooks-root",
        type=Path,
        default=None,
        help="Hooks template root (default: parent of manifest/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if OS hooks JSON files are missing or out of date",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    manifest_path = args.manifest or (script_dir / MANIFEST_NAME)
    hooks_root = args.hooks_root or script_dir.parent

    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = _load_yaml(manifest_path)
    outputs = generate_all(manifest)

    if args.check:
        stale = check_generated(hooks_root, outputs)
        if stale:
            print(
                "hooks JSON is stale or missing: "
                + ", ".join(stale)
                + "\nRun: python templates/hooks/manifest/generate_hooks_json.py",
                file=sys.stderr,
            )
            return 1
        print("hooks JSON is up to date")
        return 0

    written = write_generated(hooks_root, outputs)
    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
