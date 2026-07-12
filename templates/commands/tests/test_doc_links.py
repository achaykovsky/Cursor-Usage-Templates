"""Validate relative markdown links in templates/ and repo README.

Broken doc links fail silently for readers; this parametrized suite catches
missing files and stale anchors before sync or publish. External URLs are
skipped because they require network checks outside pytest scope.

Synced outputs (``.cursor/`` after ``FromGlobal``) flatten ``agents/subagents/*.md``
to ``agents/*.md``; those sources are validated in ``test_synced_output_relative_link``.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _commands_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import re
from pathlib import Path
from urllib.parse import unquote

import pytest

from _commands_bootstrap import run_test_file

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / "templates"
CURSOR = ROOT / ".cursor"
DOC_ROOTS = (TEMPLATES, ROOT / "README.md")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# Skip schemes that are not repo-relative paths
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")
# Agent subagent sources flatten on sync — link bases differ from templates/ layout
SYNC_FLATTEN_SUBAGENTS = "agents/subagents"


def _slugify(text: str) -> str:
    """Mirror GitHub-style anchor generation so header lookups match link targets."""
    text = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"\s+", "-", text).strip("-")


def _headers(path: Path) -> set[str]:
    """Collect anchor IDs from markdown headings, including explicit {#id} suffixes."""
    headers: set[str] = set()
    if not path.is_file():
        return headers
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*(?:\{#([^}]+)\})?\s*$", line)
        if not match:
            continue
        title = match.group(2).strip()
        anchor = (match.group(3) or _slugify(title)).lower()
        headers.add(anchor)
        headers.add(_slugify(title).lower())
    return headers


def _iter_doc_files() -> list[Path]:
    """All markdown sources that participate in the templates doc graph."""
    files: list[Path] = []
    for root in DOC_ROOTS:
        if root.is_file():
            files.append(root)
        else:
            for path in sorted(root.rglob("*.md")):
                if SYNC_FLATTEN_SUBAGENTS in path.as_posix():
                    continue
                files.append(path)
            files.extend(sorted(root.rglob("*.mdc")))
    return files


def _template_to_cursor_rel(template_path: Path) -> Path:
    """Map a templates/ source path to its .cursor/ path after sync."""
    rel = template_path.relative_to(TEMPLATES)
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "agents" and parts[1] == "subagents":
        return Path("agents") / Path(*parts[2:])
    return rel


def _cursor_to_template_rel(cursor_rel: Path) -> Path:
    """Map a .cursor/ relative path back to templates/ source when synced."""
    parts = cursor_rel.parts
    if parts and parts[0] == "agents":
        return Path("agents", "subagents", *parts[1:])
    return cursor_rel


def _iter_synced_doc_sources() -> list[tuple[Path, Path]]:
    """(template_source, link_resolve_base_under_.cursor) for synced markdown."""
    pairs: list[tuple[Path, Path]] = []
    catalog_files = (
        "USAGE.md",
        "rules/RULES.md",
        "skills/SKILLS.md",
        "hooks/HOOKS_USAGE.md",
    )
    for rel in catalog_files:
        src = TEMPLATES / rel
        if src.is_file():
            pairs.append((src, CURSOR / Path(rel).parent))
    subagents = TEMPLATES / "agents" / "subagents"
    if subagents.is_dir():
        for src in sorted(subagents.glob("*.md")):
            pairs.append((src, CURSOR / "agents"))
    skills_root = TEMPLATES / "skills"
    if skills_root.is_dir():
        for src in sorted(skills_root.rglob("SKILL.md")):
            rel = src.relative_to(skills_root)
            pairs.append((src, CURSOR / "skills" / rel.parent))
    return pairs


def _collect_synced_links() -> list[tuple[Path, Path, str, str]]:
    """Links in synced sources resolved from post-sync .cursor/ bases."""
    links: list[tuple[Path, Path, str, str]] = []
    for source, link_base in _iter_synced_doc_sources():
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            target = match.group(2).strip()
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            links.append((source, link_base, match.group(0), target))
    return links


def _collect_links() -> list[tuple[Path, str, str]]:
    """Build the parametrization table once at collection time (not per test run)."""
    links: list[tuple[Path, str, str]] = []
    for doc in _iter_doc_files():
        text = doc.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            target = match.group(2).strip()
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            links.append((doc, match.group(0), target))
    return links


def _is_gfm_separator_row(line: str) -> bool:
    """True for alignment rows like |---|---| (not prose cells starting with '| ')."""
    stripped = line.strip()
    return (
        stripped.startswith("|")
        and stripped.endswith("|")
        and stripped.count("-") >= 3
    )


def _find_intra_table_blank_line(text: str) -> str | None:
    """Return a snippet if a blank line splits header/separator/data within one GFM table."""
    lines = text.splitlines()
    in_table = False
    prev_kind = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_pipe_row = stripped.startswith("|") and stripped.endswith("|")
        if not is_pipe_row:
            in_table = False
            continue
        is_separator = _is_gfm_separator_row(stripped)
        if not in_table:
            in_table = True
            prev_kind = "header"
            continue
        if i > 0 and not lines[i - 1].strip():
            prev_idx = i - 2
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            if prev_idx < 0:
                continue
            prev = lines[prev_idx].strip()
            if not (prev.startswith("|") and prev.endswith("|")):
                continue
            prev_sep = _is_gfm_separator_row(prev)
            if prev_kind == "header" and is_separator:
                return f"{prev}\n\n{stripped}"
            if prev_sep and not is_separator:
                return f"{prev}\n\n{stripped}"
            if prev_kind == "data" and not is_separator:
                return f"{prev}\n\n{stripped}"
        if is_separator:
            prev_kind = "separator"
        else:
            prev_kind = "data"
    return None


def _collect_broken_table_docs() -> list[Path]:
    """Markdown sources that must not have blank lines between GFM table rows."""
    return _iter_doc_files()


@pytest.mark.parametrize("doc", _collect_broken_table_docs(), ids=lambda p: str(p.relative_to(ROOT)))
def test_gfm_tables_have_contiguous_rows(doc: Path) -> None:
    """Blank lines between table rows break GFM rendering (pipes show as plain text)."""
    text = doc.read_text(encoding="utf-8", errors="replace")
    snippet = _find_intra_table_blank_line(text)
    assert snippet is None, (
        f"{doc.relative_to(ROOT)}: blank line between GFM table rows near:\n{snippet!r}"
    )


@pytest.mark.parametrize("source,markdown,target", _collect_links(), ids=lambda value: str(value))
def test_relative_markdown_link(source: Path, markdown: str, target: str) -> None:
    """Each relative link must resolve inside the repo and point at a valid anchor when present."""
    anchor = ""
    path_part = target
    if "#" in path_part:
        path_part, anchor = path_part.split("#", 1)
        path_part = path_part.strip()
        anchor = unquote(anchor).lower()

    # Same-file anchor-only links (e.g. [text](#section))
    if not path_part:
        headers = _headers(source)
        assert anchor in headers or _slugify(anchor) in headers, (
            f"{source.relative_to(ROOT)}: {markdown} — missing anchor #{anchor}"
        )
        return

    # Resolve relative to the source file, then enforce repo boundary
    resolved = (source.parent / path_part).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise AssertionError(
            f"{source.relative_to(ROOT)}: {markdown} — link escapes repo root"
        ) from exc
    assert resolved.exists(), (
        f"{source.relative_to(ROOT)}: {markdown} — missing {resolved.relative_to(ROOT)}"
    )
    if anchor:
        headers = _headers(resolved)
        assert anchor in headers or _slugify(anchor) in headers, (
            f"{source.relative_to(ROOT)}: {markdown} — bad anchor in {resolved.relative_to(ROOT)}"
        )


@pytest.mark.parametrize(
    "source,link_base,markdown,target",
    _collect_synced_links(),
    ids=lambda value: str(value),
)
def test_synced_output_relative_link(
    source: Path, link_base: Path, markdown: str, target: str
) -> None:
    """Links in synced markdown must resolve under .cursor/ after FromGlobal layout."""
    anchor = ""
    path_part = target
    if "#" in path_part:
        path_part, anchor = path_part.split("#", 1)
        path_part = path_part.strip()
        anchor = unquote(anchor).lower()

    cursor_dest = _template_to_cursor_rel(source)
    resolve_from = link_base if path_part else CURSOR / cursor_dest.parent

    if not path_part:
        headers = _headers(TEMPLATES / _cursor_to_template_rel(cursor_dest))
        assert anchor in headers or _slugify(anchor) in headers, (
            f"{source.relative_to(ROOT)} (as .cursor/{cursor_dest}): {markdown} — missing anchor #{anchor}"
        )
        return

    resolved_cursor = (resolve_from / path_part).resolve()
    try:
        cursor_rel = resolved_cursor.relative_to(CURSOR)
    except ValueError as exc:
        raise AssertionError(
            f"{source.relative_to(ROOT)} (as .cursor/{cursor_dest}): {markdown} — "
            f"link escapes .cursor/ ({resolved_cursor})"
        ) from exc

    template_rel = _cursor_to_template_rel(cursor_rel)
    template_target = TEMPLATES / template_rel
    assert template_target.is_file(), (
        f"{source.relative_to(ROOT)} (as .cursor/{cursor_dest}): {markdown} — "
        f"missing synced target templates/{template_rel.as_posix()}"
    )
    if anchor:
        headers = _headers(template_target)
        assert anchor in headers or _slugify(anchor) in headers, (
            f"{source.relative_to(ROOT)}: {markdown} — bad anchor in templates/{template_rel.as_posix()}"
        )


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
