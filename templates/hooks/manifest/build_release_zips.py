#!/usr/bin/env python3
"""Build OS-specific hooks release zip bundles from templates/hooks/."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parent.parent
WINDOWS_JSON = HOOKS_ROOT / "windows" / "hooks.json"
UNIX_JSON = HOOKS_ROOT / "unix" / "hooks.json"


def _parse_version_from_tag(tag: str) -> str:
    """Extract semver from hooks-v1.2.3 tag."""
    prefix = "hooks-v"
    if tag.startswith(prefix):
        return tag[len(prefix) :]
    return tag.lstrip("v")


def _stage_bundle(
    staging: Path,
    *,
    hooks_json_src: Path,
    script_dir: Path,
    script_suffix: str,
    include_policy: bool,
) -> None:
    """Populate staging/ with hooks.json, scripts, and optional policy/."""
    if staging.exists():
        shutil.rmtree(staging)
    scripts_dest = staging / "hooks" / "scripts"
    scripts_dest.mkdir(parents=True)

    shutil.copy2(hooks_json_src, staging / "hooks.json")

    for script in sorted(script_dir.glob(f"*{script_suffix}")):
        if script.suffix != script_suffix:
            continue
        if script.name.startswith("hook-common"):
            continue
        shutil.copy2(script, scripts_dest / script.name)

    if include_policy:
        policy_src = HOOKS_ROOT / "policy"
        if policy_src.is_dir():
            shutil.copytree(policy_src, staging / "hooks" / "policy")


def _write_zip(staging: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.is_file():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(staging).as_posix())


def build_release_zips(output_dir: Path, version: str) -> list[Path]:
    """Build windows and unix zip artifacts; return written zip paths."""
    if not WINDOWS_JSON.is_file() or not UNIX_JSON.is_file():
        raise FileNotFoundError(
            "OS hooks JSON missing; run generate_hooks_json.py first "
            "(expected windows/hooks.json and unix/hooks.json)"
        )

    written: list[Path] = []
    staging_root = output_dir / "_staging"
    try:
        win_stage = staging_root / "windows"
        _stage_bundle(
            win_stage,
            hooks_json_src=WINDOWS_JSON,
            script_dir=HOOKS_ROOT / "windows",
            script_suffix=".ps1",
            include_policy=True,
        )
        win_zip = output_dir / f"cursor-hooks-windows-v{version}.zip"
        _write_zip(win_stage, win_zip)
        written.append(win_zip)

        unix_stage = staging_root / "unix"
        _stage_bundle(
            unix_stage,
            hooks_json_src=UNIX_JSON,
            script_dir=HOOKS_ROOT / "unix",
            script_suffix=".sh",
            include_policy=True,
        )
        unix_zip = output_dir / f"cursor-hooks-unix-v{version}.zip"
        _write_zip(unix_stage, unix_zip)
        written.append(unix_zip)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Build OS-specific hooks release zips.")
    parser.add_argument(
        "--version",
        default="",
        help="Release version (e.g. 1.0.0). Default: read from GITHUB_REF_NAME hooks-v* tag.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Directory for zip artifacts (default: dist/)",
    )
    args = parser.parse_args()

    version = args.version.strip()
    if not version:
        ref = __import__("os").environ.get("GITHUB_REF_NAME", "")
        if ref.startswith("hooks-v"):
            version = _parse_version_from_tag(ref)
        else:
            print("error: --version required (or set GITHUB_REF_NAME=hooks-vX.Y.Z)", file=sys.stderr)
            return 1

    try:
        written = build_release_zips(args.output_dir.resolve(), version)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "version": version,
        "artifacts": [p.name for p in written],
        "install": {
            "windows": "Expand-Archive cursor-hooks-windows-v{version}.zip -DestinationPath .cursor",
            "unix": "unzip cursor-hooks-unix-v{version}.zip -d .cursor/",
        },
    }
    manifest_path = args.output_dir.resolve() / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for path in written:
        print(f"wrote {path}")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
