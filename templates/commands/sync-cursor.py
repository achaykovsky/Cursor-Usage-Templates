#!/usr/bin/env python3
"""Sync Cursor config from templates/ into project .cursor/ and ~/.cursor/.

Modes:
  TemplatesToLocal (default) — templates/* → project .cursor/
  TemplatesToGlobal       — templates/* → ~/.cursor/ (user global)
  FromGlobal              — ~/.cursor/ → project .cursor/

templates/ is the only authoring source. Nothing is ever copied *from* project .cursor/.
FromGlobal reads ~/.cursor/ (populated via TemplatesToGlobal) into other projects.

Copies agents, rules, hooks, skills, commands (global only), and routing catalogs.
Does not copy prompts, tests, logs, CI, cache, or other repo-only paths.
Hook scripts live under templates/hooks/windows/ (*.ps1) and templates/hooks/unix/ (*.sh).
Installed .cursor/hooks/scripts/ is flat; only scripts for the active OS variant are copied.
FromGlobal copies hooks.json plus only *.ps1 (Windows) or *.sh (Unix) matching --hooks-variant auto.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SyncOptions:
    dry_run: bool = False
    verbose: bool = False


_sync_opts: ContextVar[SyncOptions] = ContextVar("sync_opts", default=SyncOptions())


def _get_sync_opts() -> SyncOptions:
    return _sync_opts.get()


def set_sync_options(*, dry_run: bool = False, verbose: bool = False) -> None:
    _sync_opts.set(SyncOptions(dry_run=dry_run, verbose=verbose))
    logger.info("set_sync_options", extra={"dry_run": dry_run, "verbose": verbose})


def _log(level: str, event: str, **fields: object) -> None:
    if not _get_sync_opts().verbose:
        return
    record = {"level": level, "component": "sync_cursor", "event": event, **fields}
    print(json.dumps(record, separators=(",", ":")), file=sys.stderr)


def _ensure_dir(path: Path) -> None:
    if not _get_sync_opts().dry_run:
        path.mkdir(parents=True, exist_ok=True)


def _copy2(src: Path, dest: Path) -> None:
    if _get_sync_opts().dry_run:
        _log("info", "would_copy", src=str(src), dest=str(dest))
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _write_text(path: Path, text: str) -> None:
    if _get_sync_opts().dry_run:
        _log("info", "would_write", path=str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_sync_line(msg: str) -> None:
    prefix = "DRY" if _get_sync_opts().dry_run else "OK"
    print(f"  {prefix}  {msg}")


def _clear_matching(dir_path: Path, patterns: tuple[str, ...]) -> None:
    if not dir_path.is_dir() or _get_sync_opts().dry_run:
        return
    for p in patterns:
        for f in dir_path.glob(p):
            if f.is_file():
                f.unlink()


def platform_hooks_variant(variant: str) -> str:
    """Return 'windows' or 'unix' for hook script selection."""
    logger.info("platform_hooks_variant_enter", extra={"variant": variant})
    if variant == "windows":
        result = "windows"
    elif variant == "unix":
        result = "unix"
    else:
        result = "windows" if sys.platform == "win32" else "unix"
    logger.info("platform_hooks_variant_exit", extra={"resolved": result})
    return result


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
            p for p in legacy.iterdir() if p.is_file() and p.suffix == ext
        )
    return []


def resolve_agents_source(project_root: Path) -> Path | None:
    """Return templates/agents/subagents when it contains agent *.md files."""
    logger.info("resolve_agents_source_enter", extra={"project_root": str(project_root)})
    templates_subagents = project_root / "templates" / "agents" / "subagents"
    if templates_subagents.is_dir() and any(templates_subagents.glob("*.md")):
        logger.info("resolve_agents_source_exit", extra={"source": "templates_subagents"})
        return templates_subagents
    logger.info("resolve_agents_source_exit", extra={"source": None})
    return None


def infer_components_for_template_path(project_root: Path, file_path: Path) -> frozenset[str] | None:
    """Map an edited path under templates/ to sync components, or None when no .cursor/ update applies."""
    try:
        rel = file_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        parts = file_path.as_posix().split("templates/", 1)
        if len(parts) < 2:
            return None
        rel = Path("templates") / parts[1]

    rel_posix = rel.as_posix().replace("\\", "/")
    if not rel_posix.startswith("templates/"):
        return None

    rest = rel_posix.removeprefix("templates/")
    if rest.startswith("agents/"):
        return frozenset({"agents"})
    if rest.startswith("rules/"):
        return frozenset({"rules"})
    if rest.startswith("hooks/"):
        return frozenset({"hooks"})
    if rest.startswith("skills/"):
        return frozenset({"skills"})
    if rest in CATALOG_SYNC_PATHS:
        return frozenset({"catalogs"})
    if rest.startswith(("commands/", "prompts/", "mcp/")):
        return None
    return ALL_SYNC_COMPONENTS


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
    return sync_agents_from_source(src, dest_cursor)


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

    For FromGlobal: if the source has no scripts matching this OS (e.g. global was
    populated on another OS), fall back to templates/hooks/windows|unix/ when project_root is set.
    When falling back to template scripts, hooks.json is taken from the same templates variant
    so commands stay consistent. If hooks.json is missing on the source and we are not using
    template scripts, fall back to templates hooks json for this variant.
    """
    logger.info(
        "sync_hooks_tree_enter",
        extra={
            "source": str(source_cursor),
            "dest": str(dest_cursor),
            "hooks_variant": hooks_variant,
            "has_project_root": project_root is not None,
        },
    )
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
        if template_fallback:
            logger.info(
                "sync_hooks_tree_template_fallback",
                extra={"hooks_variant": hooks_variant, "script_count": len(script_files)},
            )

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
    logger.info("sync_hooks_tree_exit", extra={"files_copied": n, "template_fallback": template_fallback})
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
        if not f.is_file() or _should_skip_sync_path(f.relative_to(src)):
            continue
        rel = f.relative_to(src)
        out = dest / rel
        _copy2(f, out)
        _write_sync_line(f"hooks/policy/{rel.as_posix()}")
        n += 1
    return n


def _prune_stale_skills(dest_skills: Path, expected_rels: set[Path]) -> int:
    """Remove SKILL.md files under dest_skills not present in expected_rels."""
    if not dest_skills.is_dir() or _get_sync_opts().dry_run:
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
    """Copy routing catalogs from ~/.cursor/ into project .cursor/ (FromGlobal)."""
    return _sync_catalog_paths(source_cursor, dest_cursor)


_COMMAND_SCRIPT_SUFFIXES: tuple[str, ...] = (".py", ".ps1", ".sh")
# Repo-only dirs that must never land in ~/.cursor/ or project .cursor/ via sync.
_EXCLUDED_SYNC_DIR_NAMES: frozenset[str] = frozenset(
    {"__pycache__", ".pytest_cache", "tests", "logs", ".cache"}
)
_EXCLUDED_SYNC_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo"})


def _should_skip_sync_path(path: Path) -> bool:
    """Skip cache, tests, logs, and bytecode when copying trees to/from global."""
    if path.suffix.lower() in _EXCLUDED_SYNC_SUFFIXES:
        return True
    return any(part in _EXCLUDED_SYNC_DIR_NAMES for part in path.parts)


def _prune_sync_artifacts(root: Path) -> int:
    """Remove excluded artifact dirs/files under a synced destination tree."""
    if not root.is_dir() or _get_sync_opts().dry_run:
        return 0
    removed = 0
    for p in sorted(root.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and p.name in _EXCLUDED_SYNC_DIR_NAMES:
            shutil.rmtree(p, ignore_errors=True)
            removed += 1
        elif p.is_file() and p.suffix.lower() in _EXCLUDED_SYNC_SUFFIXES:
            p.unlink()
            removed += 1
    return removed


def _is_sync_command_file(path: Path) -> bool:
    if path.suffix in _COMMAND_SCRIPT_SUFFIXES:
        return True
    return path.suffix == ".md" and path.name.lower() == "readme.md"


def sync_commands_dir(source_commands: Path, dest_commands: Path) -> int:
    """Copy top-level command entrypoints and the routing package (never tests/)."""
    if not source_commands.is_dir():
        return 0
    files = sorted(f for f in source_commands.iterdir() if f.is_file() and _is_sync_command_file(f))
    if not files:
        n = 0
    else:
        _ensure_dir(dest_commands)
        n = 0
        for f in files:
            _copy2(f, dest_commands / f.name)
            _write_sync_line(f"commands/{f.name}")
            n += 1
    n += _sync_routing_package(source_commands, dest_commands)
    pruned = _prune_sync_artifacts(dest_commands)
    if pruned:
        _write_sync_line(f"commands/ (pruned {pruned} cache/test/log artifacts)")
    return n


def _sync_routing_package(source_commands: Path, dest_commands: Path) -> int:
    """Copy commands/routing/*.py only — no __pycache__, tests, or logs."""
    src = source_commands / "routing"
    if not src.is_dir():
        return 0
    dest = dest_commands / "routing"
    py_files = sorted(
        p
        for p in src.rglob("*.py")
        if p.is_file() and not _should_skip_sync_path(p.relative_to(src))
    )
    if not py_files:
        return 0
    _ensure_dir(dest)
    copied = 0
    for path in py_files:
        rel = path.relative_to(src)
        out = dest / rel
        _copy2(path, out)
        _write_sync_line(f"commands/routing/{rel.as_posix()}")
        copied += 1
    return copied


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
        _write_sync_line(_hooks_json_sync_label(templates_hooks, hj))
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
    src, label = resolve_global_hooks_json_template(templates_hooks, pk)
    if src is None:
        return 0
    text = src.read_text(encoding="utf-8")
    # Legacy templates may still use placeholders; generated files bake them in.
    if "%USERPROFILE%" in text:
        home_json = str(home).replace("\\", "\\\\")
        text = text.replace("%USERPROFILE%", home_json)
    if "$HOME" in text:
        home_json = json.dumps(str(home).replace("\\", "/"))[1:-1]
        text = text.replace("$HOME", home_json)
    _ensure_dir(dest_cursor)
    _write_text(dest_cursor / "hooks.json", text)
    _write_sync_line(f"hooks.json (global absolute paths from {label})")
    return 1


def sync_templates_to_cursor(
    project_root: Path,
    dest_cursor: Path,
    hooks_variant: str,
    components: frozenset[str] | None = None,
) -> int:
    """Copy templates/agents, rules, hooks, skills, and routing catalogs into dest_cursor."""
    active = components or ALL_SYNC_COMPONENTS
    logger.info(
        "sync_templates_to_cursor_enter",
        extra={
            "project_root": str(project_root),
            "dest": str(dest_cursor),
            "hooks_variant": hooks_variant,
            "components": sorted(active),
        },
    )
    copied = 0
    templates_root = project_root / "templates"

    if "agents" in active:
        agents_src = resolve_agents_source(project_root)
        if agents_src is not None:
            copied += sync_agents_from_source(agents_src, dest_cursor)

    if "rules" in active:
        copied += sync_rules_dir(templates_root, dest_cursor)
    if "hooks" in active:
        copied += sync_hooks_from_templates(project_root, dest_cursor, hooks_variant)
    if "skills" in active:
        copied += sync_skills_tree(templates_root / "skills", dest_cursor / "skills")
    if "catalogs" in active:
        copied += sync_catalogs_from_templates(templates_root, dest_cursor)
    logger.info("sync_templates_to_cursor_exit", extra={"files_copied": copied})
    return copied


def sync_commands_to_global(project_root: Path, global_cursor: Path) -> int:
    """Publish templates/commands/ to ~/.cursor/commands/ (TemplatesToGlobal only)."""
    return sync_commands_dir(project_root / "templates" / "commands", global_cursor / "commands")


ALL_SYNC_COMPONENTS = frozenset({"agents", "rules", "hooks", "skills", "catalogs"})


def parse_components(value: str | None) -> frozenset[str]:
    """Parse --components comma list; default is all template components."""
    if not value or not value.strip():
        return ALL_SYNC_COMPONENTS
    parts = {p.strip().lower() for p in value.split(",") if p.strip()}
    unknown = parts - ALL_SYNC_COMPONENTS
    if unknown:
        valid = ", ".join(sorted(ALL_SYNC_COMPONENTS))
        raise ValueError(
            f"Unknown --components: {', '.join(sorted(unknown))}. Valid: {valid}"
        )
    return frozenset(parts)


def resolve_hooks_json_template(templates_hooks: Path, variant: str) -> Path | None:
    """Return source hooks JSON under templates/hooks/{windows|unix}/hooks.json.

    Falls back to legacy generated/ and root-level JSON when OS folders lack hooks.json.
    """
    pk = platform_hooks_variant(variant)

    def pick(platform: str) -> Path | None:
        os_json = templates_hooks / platform / "hooks.json"
        if os_json.is_file():
            return os_json
        gen_flat = templates_hooks / "generated" / f"hooks.{platform}.json"
        if gen_flat.is_file():
            return gen_flat
        if platform == "windows":
            legacy = templates_hooks / "hooks.json"
        else:
            legacy = templates_hooks / "hooks.unix.json"
            if not legacy.is_file():
                legacy = templates_hooks / "hooks.json"
        return legacy if legacy.is_file() else None

    if variant == "windows":
        return pick("windows")
    if variant == "unix":
        return pick("unix")
    if sys.platform == "win32":
        return pick("windows")
    return pick("unix")


def resolve_global_hooks_json_template(templates_hooks: Path, pk: str) -> tuple[Path | None, str]:
    """Return (source path, label) for global hooks.json with absolute script paths."""
    os_global = templates_hooks / pk / "hooks.global.json"
    if os_global.is_file():
        return os_global, f"{pk}/hooks.global.json"

    gen_flat = templates_hooks / "generated" / f"hooks.global.{pk}.json"
    if gen_flat.is_file():
        return gen_flat, f"generated/hooks.global.{pk}.json"

    legacy = templates_hooks / f"hooks.global.{pk}.json"
    if legacy.is_file():
        return legacy, f"hooks.global.{pk}.json"
    return None, ""


def _hooks_json_sync_label(templates_hooks: Path, src: Path) -> str:
    """Human-readable sync line for hooks.json copy."""
    try:
        rel = src.relative_to(templates_hooks).as_posix()
    except ValueError:
        rel = src.name
    return f"hooks.json (from {rel})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Cursor templates to .cursor/ and optional global dir.")
    parser.add_argument(
        "--project-root",
        default="",
        help="Project root (default: parent of templates/)",
    )
    parser.add_argument(
        "--mode",
        choices=("TemplatesToLocal", "TemplatesToGlobal", "FromGlobal"),
        default="TemplatesToLocal",
    )
    parser.add_argument(
        "--trigger-file",
        default="",
        help="Edited file under templates/ (afterFileEdit hook). Infers --components; no-op when not syncable.",
    )
    parser.add_argument(
        "--hooks-variant",
        choices=("auto", "windows", "unix"),
        default="auto",
        help="OS hook set: auto (this OS), windows (*.ps1), or unix (*.sh). Used for templates and FromGlobal.",
    )
    parser.add_argument(
        "--components",
        default="",
        help=(
            "Comma-separated template components to sync: agents, rules, hooks, skills, catalogs. "
            "Default: all. Example: --components hooks or --components hooks,rules"
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Print would-copy paths without writing files.")
    parser.add_argument("--verbose", action="store_true", help="Emit structured JSON logs to stderr.")
    args = parser.parse_args()
    set_sync_options(dry_run=args.dry_run, verbose=args.verbose)
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        components = parse_components(args.components)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

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
    if args.trigger_file:
        mode = "TemplatesToLocal"
        inferred = infer_components_for_template_path(project_root, Path(args.trigger_file))
        if inferred is None:
            logger.info(
                "trigger_file_skip",
                extra={"trigger_file": args.trigger_file, "reason": "not_syncable"},
            )
            return 0
        components = inferred
    logger.info(
        "main_enter",
        extra={
            "mode": mode,
            "project_root": str(project_root),
            "dry_run": args.dry_run,
            "hooks_variant": args.hooks_variant,
            "components": sorted(components),
        },
    )

    if mode == "TemplatesToGlobal":
        print(f"Mode: templates/ -> {global_cursor}")
        pk = platform_hooks_variant(args.hooks_variant)
        if "hooks" in components:
            print(f"Hooks: {pk} (from templates/hooks/{pk}/)")
        copied += sync_templates_to_cursor(
            project_root, global_cursor, args.hooks_variant, components
        )
        if "catalogs" in components or components == ALL_SYNC_COMPONENTS:
            copied += sync_commands_to_global(project_root, global_cursor)
        templates_hooks = project_root / "templates" / "hooks"
        if "hooks" in components and templates_hooks.is_dir():
            copied += write_global_hooks_json(global_cursor, templates_hooks, home, args.hooks_variant)
    elif mode == "FromGlobal":
        print(f"Mode: {global_cursor} -> project .cursor/")
        if "hooks" in components:
            print(f"Hooks: {platform_hooks_variant(args.hooks_variant)} scripts only")
        if "agents" in components:
            copied += sync_agents_dir(global_cursor, local_cursor)
        if "rules" in components:
            copied += sync_rules_dir(global_cursor, local_cursor)
        if "hooks" in components:
            copied += sync_hooks_tree(global_cursor, local_cursor, args.hooks_variant, project_root)
        if "skills" in components:
            copied += sync_skills_tree(global_cursor / "skills", local_cursor / "skills")
        if "catalogs" in components:
            copied += sync_catalogs_tree(global_cursor, local_cursor)
    else:
        print("Mode: templates/ -> project .cursor/")
        pk = platform_hooks_variant(args.hooks_variant)
        if "hooks" in components:
            print(f"Hooks: {pk} (from templates/hooks/{pk}/)")
        copied += sync_templates_to_cursor(
            project_root, local_cursor, args.hooks_variant, components
        )

    print("")
    print(f"Synced {copied} files ({mode})")
    logger.info("main_exit", extra={"mode": mode, "files_copied": copied, "exit_code": 0})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
