#!/usr/bin/env python3
"""Sync Cursor config between project .cursor/, templates/, and ~/.cursor/.

Modes:
  TemplatesToLocal (default) — templates/* → project .cursor/
  TemplatesToGlobal       — templates/* → ~/.cursor/ (user global)
  ToGlobal                — project .cursor/ → ~/.cursor/
  FromGlobal              — ~/.cursor/ → project .cursor/

Copies agents, rules, hooks, skills, commands, and routing catalogs (USAGE.md, RULES.md, SKILLS.md, HOOKS_USAGE.md, etc.).
Does not copy prompts, tests, logs, CI, cache, or other repo-only paths.
Hook scripts are organized under templates/hooks/windows/ (*.ps1) and templates/hooks/unix/ (*.sh).
Installed .cursor/hooks/scripts/ is always flat; only scripts for the active OS variant are copied.
ToGlobal/FromGlobal copy hooks.json plus only *.ps1 (Windows) or *.sh (Unix) matching --hooks-variant auto.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SyncOptions:
    dry_run: bool = False
    verbose: bool = False


_SYNC_OPTS = SyncOptions()


def set_sync_options(*, dry_run: bool = False, verbose: bool = False) -> None:
    global _SYNC_OPTS
    _SYNC_OPTS = SyncOptions(dry_run=dry_run, verbose=verbose)


def _log(level: str, event: str, **fields: object) -> None:
    if not _SYNC_OPTS.verbose:
        return
    record = {"level": level, "component": "sync_cursor", "event": event, **fields}
    print(json.dumps(record, separators=(",", ":")), file=sys.stderr)


def _ensure_dir(path: Path) -> None:
    if not _SYNC_OPTS.dry_run:
        path.mkdir(parents=True, exist_ok=True)


def _copy2(src: Path, dest: Path) -> None:
    if _SYNC_OPTS.dry_run:
        _log("info", "would_copy", src=str(src), dest=str(dest))
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _write_text(path: Path, text: str) -> None:
    if _SYNC_OPTS.dry_run:
        _log("info", "would_write", path=str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_sync_line(msg: str) -> None:
    prefix = "DRY" if _SYNC_OPTS.dry_run else "OK"
    print(f"  {prefix}  {msg}")


def _clear_matching(dir_path: Path, patterns: tuple[str, ...]) -> None:
    if not dir_path.is_dir() or _SYNC_OPTS.dry_run:
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


def resolve_agents_source(project_root: Path, global_cursor: Path) -> Path | None:
    templates_subagents = project_root / "templates" / "agents" / "subagents"
    if templates_subagents.is_dir() and any(templates_subagents.glob("*.md")):
        return templates_subagents
    agents_global = global_cursor / "agents"
    if agents_global.is_dir() and any(agents_global.glob("*.md")):
        return agents_global
    return None


def sync_agents_from_source(source_dir: Path, dest_cursor: Path) -> int:
    files = sorted(source_dir.glob("*.md"))
    if not files:
        return 0
    dest = dest_cursor / "agents"
    _ensure_dir(dest)
    _clear_matching(dest, ("*.md",))
    n = 0
    for f in files:
        _copy2(f, dest / f.name)
        _write_sync_line(f"agents/{f.name}")
        n += 1
    return n


def sync_agents_dir(source_cursor: Path, dest_cursor: Path) -> int:
    src = source_cursor / "agents"
    if not src.is_dir():
        return 0
    files = sorted(src.glob("*.md"))
    if not files:
        return 0
    dest = dest_cursor / "agents"
    _ensure_dir(dest)
    _clear_matching(dest, ("*.md",))
    n = 0
    for f in files:
        _copy2(f, dest / f.name)
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
    _ensure_dir(dest)
    _clear_matching(dest, ("*.mdc",))
    n = 0
    for f in files:
        _copy2(f, dest / f.name)
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
    _ensure_dir(dest_cursor)
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
            _copy2(t, dest_cursor / "hooks.json")
            _write_sync_line(f"hooks.json (from templates/{t.name})")
            n += 1
        elif src_json.is_file():
            _copy2(src_json, dest_cursor / "hooks.json")
            _write_sync_line("hooks.json")
            n += 1
    else:
        if src_json.is_file():
            _copy2(src_json, dest_cursor / "hooks.json")
            _write_sync_line("hooks.json")
            n += 1
        elif project_root is not None:
            th = project_root / "templates" / "hooks"
            t = resolve_hooks_json_template(th, hooks_variant)
            if t is not None:
                _copy2(t, dest_cursor / "hooks.json")
                _write_sync_line(f"hooks.json (from templates/{t.name})")
                n += 1

    dest_scripts = dest_cursor / "hooks" / "scripts"
    _ensure_dir(dest_scripts)
    _clear_matching(dest_scripts, ("*.ps1", "*.sh"))

    for f in script_files:
        _copy2(f, dest_scripts / f.name)
        if template_fallback:
            _write_sync_line(f"hooks/scripts/{f.name} (from templates/hooks/{pk}/)")
        else:
            _write_sync_line(f"hooks/scripts/{f.name}")
        n += 1
    policy_src: Path | None = None
    if project_root is not None:
        thooks = project_root / "templates" / "hooks"
        if (thooks / "policy").is_dir():
            policy_src = thooks
    if policy_src is None and (source_cursor / "hooks" / "policy").is_dir():
        policy_src = source_cursor / "hooks"
    if policy_src is not None:
        n += sync_hooks_policy(policy_src, dest_cursor / "hooks")
    return n


def sync_hooks_policy(source_hooks: Path, dest_hooks: Path) -> int:
    """Copy hooks/policy/ tree (hook_policy.py + JSON catalogs)."""
    src = source_hooks / "policy"
    if not src.is_dir():
        return 0
    dest = dest_hooks / "policy"
    _ensure_dir(dest)
    n = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or f.suffix == ".pyc":
            continue
        rel = f.relative_to(src)
        out = dest / rel
        _copy2(f, out)
        _write_sync_line(f"hooks/policy/{rel.as_posix()}")
        n += 1
    return n


def _prune_stale_skills(dest_skills: Path, expected_rels: set[Path]) -> int:
    """Remove SKILL.md files under dest_skills not present in expected_rels."""
    if not dest_skills.is_dir() or _SYNC_OPTS.dry_run:
        return 0
    removed = 0
    for existing in sorted(dest_skills.rglob("SKILL.md")):
        rel = existing.relative_to(dest_skills)
        if rel in expected_rels:
            continue
        existing.unlink()
        removed += 1
        parent = existing.parent
        while parent != dest_skills and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    return removed


def sync_skills_tree(source_skills: Path, dest_skills: Path) -> int:
    if not source_skills.is_dir():
        return 0
    skill_files = sorted(source_skills.rglob("SKILL.md"))
    if not skill_files:
        return 0
    _ensure_dir(dest_skills)
    expected: set[Path] = set()
    n = 0
    for f in skill_files:
        rel = f.relative_to(source_skills)
        expected.add(rel)
        out = dest_skills / rel
        _copy2(f, out)
        _write_sync_line(f"skills/{rel.as_posix()}")
        n += 1
    pruned = _prune_stale_skills(dest_skills, expected)
    if pruned:
        _write_sync_line(f"skills/ (pruned {pruned} stale SKILL.md)")
    return n


# Routing catalogs: mirrored under templates/ and .cursor/ (prompts/ excluded).
CATALOG_SYNC_PATHS: tuple[str, ...] = (
    "USAGE.md",
    "rules/RULES.md",
    "skills/SKILLS.md",
    "hooks/HOOKS_USAGE.md",
    "hooks/README.md",
)


def _sync_catalog_paths(source_root: Path, dest_cursor: Path) -> int:
    n = 0
    for rel in CATALOG_SYNC_PATHS:
        src = source_root / rel
        if not src.is_file():
            continue
        dest = dest_cursor / rel
        _copy2(src, dest)
        _write_sync_line(rel.replace("\\", "/"))
        n += 1
    return n


def sync_catalogs_from_templates(templates_root: Path, dest_cursor: Path) -> int:
    """Copy routing catalogs from templates/ to project .cursor/."""
    return _sync_catalog_paths(templates_root, dest_cursor)


def sync_catalogs_tree(source_cursor: Path, dest_cursor: Path) -> int:
    """Copy routing catalogs between .cursor/ trees (ToGlobal / FromGlobal)."""
    return _sync_catalog_paths(source_cursor, dest_cursor)


_COMMAND_SCRIPT_SUFFIXES: tuple[str, ...] = (".py", ".ps1", ".sh")


def _is_sync_command_file(path: Path) -> bool:
    if path.suffix in _COMMAND_SCRIPT_SUFFIXES:
        return True
    return path.suffix == ".md" and path.name.lower() == "readme.md"


def sync_commands_dir(source_commands: Path, dest_commands: Path) -> int:
    """Copy top-level command entrypoints (never tests/ or nested dirs)."""
    if not source_commands.is_dir():
        return 0
    files = sorted(f for f in source_commands.iterdir() if f.is_file() and _is_sync_command_file(f))
    if not files:
        return 0
    _ensure_dir(dest_commands)
    n = 0
    for f in files:
        _copy2(f, dest_commands / f.name)
        _write_sync_line(f"commands/{f.name}")
        n += 1
    return n


def sync_hooks_from_templates(
    project_root: Path, dest_cursor: Path, hooks_variant: str
) -> int:
    """Copy hooks.json, OS scripts, and policy from templates/hooks/."""
    templates_hooks = project_root / "templates" / "hooks"
    if not templates_hooks.is_dir():
        return 0
    copied = 0
    dest_hooks = dest_cursor / "hooks"
    scripts_dest = dest_hooks / "scripts"
    _ensure_dir(dest_hooks)
    _ensure_dir(scripts_dest)

    hj = resolve_hooks_json_template(templates_hooks, hooks_variant)
    if hj is not None:
        _copy2(hj, dest_cursor / "hooks.json")
        label = "hooks.json" if hj.name == "hooks.json" else f"hooks.json (from {hj.name})"
        _write_sync_line(label)
        copied += 1

    hook_scripts = iter_template_hook_scripts(templates_hooks, hooks_variant)
    _clear_matching(scripts_dest, ("*.ps1", "*.sh"))
    for f in hook_scripts:
        _copy2(f, scripts_dest / f.name)
        _write_sync_line(f"hooks/scripts/{f.name}")
        copied += 1
    copied += sync_hooks_policy(templates_hooks, dest_hooks)
    return copied


def write_global_hooks_json(
    dest_cursor: Path, templates_hooks: Path, home: Path, hooks_variant: str
) -> int:
    """Install hooks.json with absolute script paths for ~/.cursor."""
    pk = platform_hooks_variant(hooks_variant)
    if pk == "windows":
        src = templates_hooks / "hooks.global.windows.json"
        if not src.is_file():
            return 0
        home_json = str(home).replace("\\", "\\\\")
        text = src.read_text(encoding="utf-8").replace("%USERPROFILE%", home_json)
        label = "hooks.global.windows.json"
    else:
        src = templates_hooks / "hooks.global.unix.json"
        if not src.is_file():
            return 0
        home_json = json.dumps(str(home).replace("\\", "/"))[1:-1]
        text = src.read_text(encoding="utf-8").replace("$HOME", home_json)
        label = "hooks.global.unix.json"
    _ensure_dir(dest_cursor)
    _write_text(dest_cursor / "hooks.json", text)
    _write_sync_line(f"hooks.json (global absolute paths from {label})")
    return 1


def sync_templates_to_cursor(
    project_root: Path,
    dest_cursor: Path,
    hooks_variant: str,
    global_cursor: Path | None = None,
) -> int:
    """Copy templates/agents, rules, hooks, skills, and routing catalogs into dest_cursor."""
    copied = 0
    home_cursor = global_cursor or Path.home() / ".cursor"
    templates_root = project_root / "templates"

    agents_src = resolve_agents_source(project_root, home_cursor)
    if agents_src is not None:
        copied += sync_agents_from_source(agents_src, dest_cursor)

    copied += sync_rules_dir(templates_root, dest_cursor)
    copied += sync_hooks_from_templates(project_root, dest_cursor, hooks_variant)
    copied += sync_skills_tree(templates_root / "skills", dest_cursor / "skills")
    copied += sync_catalogs_from_templates(templates_root, dest_cursor)
    return copied


def sync_commands_for_project(project_root: Path, *, to_global: bool, global_cursor: Path) -> int:
    """Sync templates/commands/ between project and ~/.cursor/commands/."""
    src = project_root / "templates" / "commands"
    dest = global_cursor / "commands" if to_global else project_root / "templates" / "commands"
    if to_global:
        return sync_commands_dir(src, dest)
    return sync_commands_dir(global_cursor / "commands", dest)


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
        choices=("TemplatesToLocal", "TemplatesToGlobal", "ToGlobal", "FromGlobal"),
        default="TemplatesToLocal",
    )
    parser.add_argument(
        "--hooks-variant",
        choices=("auto", "windows", "unix"),
        default="auto",
        help="OS hook set: auto (this OS), windows (*.ps1), or unix (*.sh). Used for templates and ToGlobal/FromGlobal.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print would-copy paths without writing files.")
    parser.add_argument("--verbose", action="store_true", help="Emit structured JSON logs to stderr.")
    args = parser.parse_args()
    set_sync_options(dry_run=args.dry_run, verbose=args.verbose)

    script_dir = Path(__file__).resolve().parent
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = script_dir.parent.parent

    local_cursor = project_root / ".cursor"
    home = Path.home()
    global_cursor = home / ".cursor"

    copied = 0
    mode = args.mode

    if mode == "TemplatesToGlobal":
        print(f"Mode: templates/ -> {global_cursor}")
        pk = platform_hooks_variant(args.hooks_variant)
        print(f"Hooks: {pk} (from templates/hooks/{pk}/)")
        copied += sync_templates_to_cursor(project_root, global_cursor, args.hooks_variant, global_cursor)
        copied += sync_commands_dir(project_root / "templates" / "commands", global_cursor / "commands")
        templates_hooks = project_root / "templates" / "hooks"
        if templates_hooks.is_dir():
            copied += write_global_hooks_json(global_cursor, templates_hooks, home, args.hooks_variant)
    elif mode == "ToGlobal":
        print(f"Mode: project .cursor/ -> {global_cursor}")
        print(f"Hooks: {platform_hooks_variant(args.hooks_variant)} scripts only")
        copied += sync_agents_dir(local_cursor, global_cursor)
        copied += sync_rules_dir(local_cursor, global_cursor)
        copied += sync_hooks_tree(local_cursor, global_cursor, args.hooks_variant, project_root)
        templates_hooks = project_root / "templates" / "hooks"
        if templates_hooks.is_dir():
            copied += write_global_hooks_json(global_cursor, templates_hooks, home, args.hooks_variant)
        copied += sync_skills_tree(local_cursor / "skills", global_cursor / "skills")
        copied += sync_catalogs_tree(local_cursor, global_cursor)
        copied += sync_commands_for_project(project_root, to_global=True, global_cursor=global_cursor)
    elif mode == "FromGlobal":
        print(f"Mode: {global_cursor} -> project .cursor/")
        print(f"Hooks: {platform_hooks_variant(args.hooks_variant)} scripts only")
        copied += sync_agents_dir(global_cursor, local_cursor)
        copied += sync_rules_dir(global_cursor, local_cursor)
        copied += sync_hooks_tree(global_cursor, local_cursor, args.hooks_variant, project_root)
        copied += sync_skills_tree(global_cursor / "skills", local_cursor / "skills")
        copied += sync_catalogs_tree(global_cursor, local_cursor)
        copied += sync_commands_for_project(project_root, to_global=False, global_cursor=global_cursor)
    else:
        print("Mode: templates/ (+ agent fallback) -> project .cursor/")
        pk = platform_hooks_variant(args.hooks_variant)
        print(f"Hooks: {pk} (from templates/hooks/{pk}/)")
        copied += sync_templates_to_cursor(
            project_root, local_cursor, args.hooks_variant, global_cursor
        )

    print("")
    print(f"Synced {copied} files ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
