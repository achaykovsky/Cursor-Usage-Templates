#!/usr/bin/env python3
"""Sync Cursor config between project .cursor/, templates/, and ~/.cursor/.

Modes:
  TemplatesToLocal (default) — templates/* → project .cursor/
  ToGlobal          — project .cursor/ → ~/.cursor/
  FromGlobal        — ~/.cursor/ → project .cursor/

Hook scripts are organized under templates/hooks/windows/ (*.ps1) and templates/hooks/unix/ (*.sh).
Installed .cursor/hooks/scripts/ is always flat; only scripts for the active OS variant are copied.
ToGlobal/FromGlobal copy hooks.json plus only *.ps1 (Windows) or *.sh (Unix) matching --hooks-variant auto.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _write_sync_line(msg: str) -> None:
    print(f"  OK  {msg}")


def _clear_matching(dir_path: Path, patterns: tuple[str, ...]) -> None:
    if not dir_path.is_dir():
        return
    for p in patterns:
        for f in dir_path.glob(p):
            if f.is_file():
                f.unlink()


def platform_hooks_variant(variant: str) -> str:
    """Return 'windows' or 'unix' for hook script selection."""
    if variant == "windows":
        return "windows"
    if variant == "unix":
        return "unix"
    return "windows" if sys.platform == "win32" else "unix"


def hook_script_suffix_for_platform(pk: str) -> str:
    return ".ps1" if pk == "windows" else ".sh"


def iter_template_hook_scripts(templates_hooks: Path, variant: str) -> list[Path]:
    """Scripts from templates/hooks/windows|unix/, with legacy templates/hooks/scripts/ fallback."""
    pk = platform_hooks_variant(variant)
    sub = templates_hooks / pk
    ext = hook_script_suffix_for_platform(pk)
    if sub.is_dir():
        files = sorted(p for p in sub.iterdir() if p.is_file() and p.suffix == ext)
        if files:
            return files
    legacy = templates_hooks / "scripts"
    if legacy.is_dir():
        return sorted(
            p for p in legacy.iterdir() if p.is_file() and p.suffix in (".ps1", ".sh") and p.suffix == ext
        )
    return []


def sync_agents_dir(source_cursor: Path, dest_cursor: Path) -> int:
    src = source_cursor / "agents"
    if not src.is_dir():
        return 0
    files = sorted(src.glob("*.md"))
    if not files:
        return 0
    dest = dest_cursor / "agents"
    dest.mkdir(parents=True, exist_ok=True)
    _clear_matching(dest, ("*.md",))
    n = 0
    for f in files:
        shutil.copy2(f, dest / f.name)
        _write_sync_line(f"agents/{f.name}")
        n += 1
    return n


def sync_rules_dir(source_cursor: Path, dest_cursor: Path) -> int:
    src = source_cursor / "rules"
    if not src.is_dir():
        return 0
    files = sorted(src.glob("*.mdc"))
    if not files:
        return 0
    dest = dest_cursor / "rules"
    dest.mkdir(parents=True, exist_ok=True)
    _clear_matching(dest, ("*.mdc",))
    n = 0
    for f in files:
        shutil.copy2(f, dest / f.name)
        _write_sync_line(f"rules/{f.name}")
        n += 1
    return n


def sync_hooks_tree(
    source_cursor: Path,
    dest_cursor: Path,
    hooks_variant: str,
    project_root: Path | None = None,
) -> int:
    """Copy hooks.json and only hook scripts for the resolved OS (ps1 or sh).

    For ToGlobal/FromGlobal: if the source has no scripts matching this OS (e.g. global was
    populated on another OS), fall back to templates/hooks/windows|unix/ when project_root is set.
    When falling back to template scripts, hooks.json is taken from the same templates variant
    so commands stay consistent. If hooks.json is missing on the source and we are not using
    template scripts, fall back to templates hooks json for this variant.
    """
    pk = platform_hooks_variant(hooks_variant)
    want_suffix = hook_script_suffix_for_platform(pk)

    n = 0
    dest_cursor.mkdir(parents=True, exist_ok=True)
    src_json = source_cursor / "hooks.json"
    src_scripts = source_cursor / "hooks" / "scripts"

    script_files: list[Path] = []
    if src_scripts.is_dir():
        script_files = sorted(
            p for p in src_scripts.iterdir() if p.is_file() and p.suffix == want_suffix
        )

    template_fallback = False
    th: Path | None = None
    if not script_files and project_root is not None:
        th = project_root / "templates" / "hooks"
        script_files = iter_template_hook_scripts(th, hooks_variant)
        template_fallback = bool(script_files)

    if template_fallback and th is not None:
        t = resolve_hooks_json_template(th, hooks_variant)
        if t is not None:
            shutil.copy2(t, dest_cursor / "hooks.json")
            _write_sync_line(f"hooks.json (from templates/{t.name})")
            n += 1
        elif src_json.is_file():
            shutil.copy2(src_json, dest_cursor / "hooks.json")
            _write_sync_line("hooks.json")
            n += 1
    else:
        if src_json.is_file():
            shutil.copy2(src_json, dest_cursor / "hooks.json")
            _write_sync_line("hooks.json")
            n += 1
        elif project_root is not None:
            th = project_root / "templates" / "hooks"
            t = resolve_hooks_json_template(th, hooks_variant)
            if t is not None:
                shutil.copy2(t, dest_cursor / "hooks.json")
                _write_sync_line(f"hooks.json (from templates/{t.name})")
                n += 1

    dest_scripts = dest_cursor / "hooks" / "scripts"
    dest_scripts.mkdir(parents=True, exist_ok=True)
    _clear_matching(dest_scripts, ("*.ps1", "*.sh"))

    for f in script_files:
        shutil.copy2(f, dest_scripts / f.name)
        if template_fallback:
            _write_sync_line(f"hooks/scripts/{f.name} (from templates/hooks/{pk}/)")
        else:
            _write_sync_line(f"hooks/scripts/{f.name}")
        n += 1
    return n


def sync_skills_tree(source_skills: Path, dest_skills: Path) -> int:
    if not source_skills.is_dir():
        return 0
    skill_files = sorted(source_skills.rglob("SKILL.md"))
    if not skill_files:
        return 0
    dest_skills.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in skill_files:
        rel = f.relative_to(source_skills)
        out = dest_skills / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        _write_sync_line(f"skills/{rel.as_posix()}")
        n += 1
    return n


def resolve_hooks_json_template(templates_hooks: Path, variant: str) -> Path | None:
    """Return source hooks.json path under templates/hooks/ for the chosen variant."""
    unix = templates_hooks / "hooks.unix.json"
    win = templates_hooks / "hooks.json"
    if variant == "windows":
        return win if win.is_file() else None
    if variant == "unix":
        if unix.is_file():
            return unix
        return win if win.is_file() else None
    # auto
    if sys.platform == "win32":
        return win if win.is_file() else None
    if unix.is_file():
        return unix
    return win if win.is_file() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Cursor templates to .cursor/ and optional global dir.")
    parser.add_argument(
        "--project-root",
        default="",
        help="Project root (default: parent of templates/)",
    )
    parser.add_argument(
        "--mode",
        choices=("TemplatesToLocal", "ToGlobal", "FromGlobal"),
        default="TemplatesToLocal",
    )
    parser.add_argument(
        "--hooks-variant",
        choices=("auto", "windows", "unix"),
        default="auto",
        help="OS hook set: auto (this OS), windows (*.ps1), or unix (*.sh). Used for templates and ToGlobal/FromGlobal.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = script_dir.parent.parent

    local_cursor = project_root / ".cursor"
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    global_cursor = home / ".cursor"

    copied = 0
    mode = args.mode

    if mode == "ToGlobal":
        print(f"Mode: project .cursor/ -> {global_cursor}")
        print(f"Hooks: {platform_hooks_variant(args.hooks_variant)} scripts only")
        copied += sync_agents_dir(local_cursor, global_cursor)
        copied += sync_rules_dir(local_cursor, global_cursor)
        copied += sync_hooks_tree(local_cursor, global_cursor, args.hooks_variant, project_root)
        copied += sync_skills_tree(local_cursor / "skills", global_cursor / "skills")
    elif mode == "FromGlobal":
        print(f"Mode: {global_cursor} -> project .cursor/")
        print(f"Hooks: {platform_hooks_variant(args.hooks_variant)} scripts only")
        copied += sync_agents_dir(global_cursor, local_cursor)
        copied += sync_rules_dir(global_cursor, local_cursor)
        copied += sync_hooks_tree(global_cursor, local_cursor, args.hooks_variant, project_root)
        copied += sync_skills_tree(global_cursor / "skills", local_cursor / "skills")
    else:
        print("Mode: templates/ (+ agent fallback) -> project .cursor/")
        pk = platform_hooks_variant(args.hooks_variant)
        print(f"Hooks: {pk} (from templates/hooks/{pk}/)")

        agents_source_global = global_cursor / "agents"
        templates_subagents = project_root / "templates" / "agents" / "subagents"
        if templates_subagents.is_dir() and any(templates_subagents.glob("*.md")):
            subagent_source: Path | None = templates_subagents
        elif agents_source_global.is_dir() and any(agents_source_global.glob("*.md")):
            subagent_source = agents_source_global
        else:
            subagent_source = None

        if subagent_source is not None:
            dest_agents = local_cursor / "agents"
            dest_agents.mkdir(parents=True, exist_ok=True)
            _clear_matching(dest_agents, ("*.md",))
            for f in sorted(subagent_source.glob("*.md")):
                shutil.copy2(f, dest_agents / f.name)
                _write_sync_line(f"agents/{f.name}")
                copied += 1

        templates_rules = project_root / "templates" / "rules"
        if templates_rules.is_dir():
            rule_files = sorted(templates_rules.glob("*.mdc"))
            if rule_files:
                dest_rules = local_cursor / "rules"
                dest_rules.mkdir(parents=True, exist_ok=True)
                for f in rule_files:
                    shutil.copy2(f, dest_rules / f.name)
                    _write_sync_line(f"rules/{f.name}")
                    copied += 1

        templates_hooks = project_root / "templates" / "hooks"
        if templates_hooks.is_dir():
            dest_hooks = local_cursor / "hooks"
            scripts_dest = dest_hooks / "scripts"
            dest_hooks.mkdir(parents=True, exist_ok=True)
            scripts_dest.mkdir(parents=True, exist_ok=True)

            hj = resolve_hooks_json_template(templates_hooks, args.hooks_variant)
            if hj is not None:
                shutil.copy2(hj, local_cursor / "hooks.json")
                label = "hooks.json" if hj.name == "hooks.json" else f"hooks.json (from {hj.name})"
                _write_sync_line(label)
                copied += 1

            hook_scripts = iter_template_hook_scripts(templates_hooks, args.hooks_variant)
            _clear_matching(scripts_dest, ("*.ps1", "*.sh"))
            for f in hook_scripts:
                shutil.copy2(f, scripts_dest / f.name)
                _write_sync_line(f"hooks/scripts/{f.name}")
                copied += 1

        templates_skills = project_root / "templates" / "skills"
        if templates_skills.is_dir():
            dest_skills = local_cursor / "skills"
            skill_files = sorted(templates_skills.rglob("SKILL.md"))
            for f in skill_files:
                rel = f.relative_to(templates_skills)
                out = dest_skills / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, out)
                _write_sync_line(f"skills/{rel.as_posix()}")
                copied += 1

    print("")
    print(f"Synced {copied} files ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
