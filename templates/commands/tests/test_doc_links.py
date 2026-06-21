"""Validate relative markdown links in templates/ and repo README.

Broken doc links fail silently for readers; this parametrized suite catches
missing files and stale anchors before sync or publish. External URLs are
skipped because they require network checks outside pytest scope.
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
DOC_ROOTS = (ROOT / "templates", ROOT / "README.md")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# Skip schemes that are not repo-relative paths
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")


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
            files.extend(sorted(root.rglob("*.md")))
            files.extend(sorted(root.rglob("*.mdc")))
    return files


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


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
