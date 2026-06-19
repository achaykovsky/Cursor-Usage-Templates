#!/usr/bin/env python3
"""Refresh model tier picks in models-catalog.json from web evidence.

Only ranks models inside the Cursor Task-tool allowlist. Never adds new slugs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

# Must match Cursor Task tool model slugs (subagent model= parameter).
CURSOR_ALLOWLIST: tuple[str, ...] = (
    "claude-4.6-sonnet-medium-thinking",
    "claude-fable-5-thinking-high",
    "claude-opus-4-8-thinking-high",
    "composer-2.5-fast",
    "gpt-5.3-codex",
    "gpt-5.5-medium",
)

DEFAULT_SOURCES: tuple[str, ...] = (
    "https://docs.cursor.com/models",
    "https://cursor.com/changelog",
)

# Tier keyword weights for scoring fetched page text (slug substring → tier).
TIER_KEYWORDS: dict[str, dict[str, int]] = {
    "frontier": {
        "opus": 3,
        "thinking-high": 3,
        "fable": 2,
        "reasoning": 2,
        "architecture": 1,
        "complex": 1,
    },
    "mid_tier": {
        "sonnet": 3,
        "medium-thinking": 2,
        "gpt-5.5": 3,
        "balanced": 2,
        "general": 1,
    },
    "lightweight": {
        "composer": 4,
        "fast": 2,
        "mini": 2,
        "codex": 1,
        "boilerplate": 1,
    },
}

SCRIPT_DIR = Path(__file__).resolve().parent
CATALOG_PATH = SCRIPT_DIR.parent / "models-catalog.json"


def _slug_aliases(slug: str) -> list[str]:
    """Search terms derived from a Cursor slug."""
    parts = slug.replace(".", "-").split("-")
    aliases = [slug, slug.replace("-medium-thinking", ""), slug.replace("-thinking-high", "")]
    if "claude" in slug:
        if "opus" in slug:
            aliases.extend(["opus", "claude opus"])
        if "sonnet" in slug:
            aliases.extend(["sonnet", "claude sonnet"])
        if "fable" in slug:
            aliases.extend(["fable"])
    if "composer" in slug:
        aliases.extend(["composer", "cursor composer"])
    if "gpt" in slug:
        aliases.extend(["gpt-5", "codex", "openai"])
    return list(dict.fromkeys(a for a in aliases if a))


def fetch_url(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "cursor-usage-templates/1.0 (model-catalog-update)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def score_slug_in_text(slug: str, text: str) -> dict[str, int]:
    lowered = text.lower()
    scores: dict[str, int] = {tier: 0 for tier in TIER_KEYWORDS}
    for alias in _slug_aliases(slug):
        count = len(re.findall(re.escape(alias.lower()), lowered))
        if count == 0:
            continue
        for tier, keywords in TIER_KEYWORDS.items():
            for kw, weight in keywords.items():
                if kw in alias.lower() or kw in slug.lower():
                    scores[tier] += count * weight
    return scores


def aggregate_scores(corpus: str) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for slug in CURSOR_ALLOWLIST:
        result[slug] = score_slug_in_text(slug, corpus)
    return result


def pick_tier_winners(
    scores: dict[str, dict[str, int]],
) -> dict[str, list[str]]:
    """Return ordered slug lists per tier (best first)."""
    tier_slugs: dict[str, list[tuple[int, str]]] = {
        tier: [] for tier in TIER_KEYWORDS
    }
    for slug, tier_scores in scores.items():
        best_tier = max(tier_scores, key=lambda t: tier_scores[t])
        tier_slugs[best_tier].append((tier_scores[best_tier], slug))

    ordered: dict[str, list[str]] = {}
    for tier, pairs in tier_slugs.items():
        pairs.sort(key=lambda x: (-x[0], x[1]))
        ordered[tier] = [slug for score, slug in pairs if score > 0]
        if not ordered[tier]:
            # Fallback: static defaults when web fetch yields no signal
            ordered[tier] = _static_tier_defaults(tier)
    return ordered


def _static_tier_defaults(tier: str) -> list[str]:
    defaults = {
        "frontier": ["claude-opus-4-8-thinking-high", "claude-fable-5-thinking-high"],
        "mid_tier": [
            "claude-4.6-sonnet-medium-thinking",
            "gpt-5.5-medium",
            "gpt-5.3-codex",
        ],
        "lightweight": ["composer-2.5-fast", "gpt-5.3-codex"],
    }
    return [s for s in defaults.get(tier, []) if s in CURSOR_ALLOWLIST]


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowlist = catalog.get("cursor_allowlist", [])
    if set(allowlist) - set(CURSOR_ALLOWLIST):
        errors.append("cursor_allowlist contains unknown slugs")
    if set(CURSOR_ALLOWLIST) - set(allowlist):
        errors.append("cursor_allowlist missing required Cursor slugs")
    for tier_key, tier in catalog.get("tiers", {}).items():
        primary = tier.get("primary")
        if primary not in CURSOR_ALLOWLIST:
            errors.append(f"tiers.{tier_key}.primary not in allowlist: {primary}")
        for alt in tier.get("alternates", []):
            if alt not in CURSOR_ALLOWLIST:
                errors.append(f"tiers.{tier_key} alternate not in allowlist: {alt}")
    return errors


def propose_updates(
    catalog: dict[str, Any],
    sources: tuple[str, ...],
) -> tuple[dict[str, Any], str]:
    corpus_parts: list[str] = []
    source_meta: list[dict[str, str]] = []
    today = date.today().isoformat()

    for url in sources:
        try:
            body = fetch_url(url)
            corpus_parts.append(body)
            source_meta.append(
                {"url": url, "checked_at": today, "notes": f"Fetched OK ({len(body)} bytes)"}
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            source_meta.append(
                {
                    "url": url,
                    "checked_at": today,
                    "notes": f"Fetch failed: {exc}",
                }
            )

    corpus = "\n".join(corpus_parts)
    scores = aggregate_scores(corpus)
    winners = pick_tier_winners(scores)

    updated = json.loads(json.dumps(catalog))  # deep copy
    updated["last_updated"] = today
    updated["cursor_allowlist"] = list(CURSOR_ALLOWLIST)

    report_lines = ["Model catalog update proposal", "=" * 40, ""]

    for tier_key in ("frontier", "mid_tier", "lightweight"):
        slugs = winners.get(tier_key, [])
        if not slugs:
            slugs = _static_tier_defaults(tier_key)
        primary = slugs[0]
        alternates = [s for s in slugs[1:] if s in CURSOR_ALLOWLIST]
        old = catalog["tiers"][tier_key]
        updated["tiers"][tier_key]["primary"] = primary
        updated["tiers"][tier_key]["alternates"] = alternates
        report_lines.append(
            f"{tier_key}: {old.get('primary')} -> {primary} "
            f"(alternates: {alternates})"
        )

    updated["sources"] = source_meta
    report_lines.append("")
    report_lines.append("Per-slug tier scores (top signal):")
    for slug in CURSOR_ALLOWLIST:
        tier_scores = scores[slug]
        best = max(tier_scores, key=lambda t: tier_scores[t])
        report_lines.append(f"  {slug}: {best}={tier_scores[best]}")

    return updated, "\n".join(report_lines)


def apply_catalog(path: Path, catalog: dict[str, Any], summary: str) -> None:
    changelog = catalog.setdefault("changelog", [])
    changelog.append(
        {
            "date": date.today().isoformat(),
            "summary": f"Web refresh: {summary[:200]}",
        }
    )
    with path.open("w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
        f.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=CATALOG_PATH,
        help="Path to models-catalog.json",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        default=[],
        help="URL to fetch (repeatable). Defaults to Cursor docs + changelog.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Print proposal only")
    group.add_argument("--apply", action="store_true", help="Write catalog")
    args = parser.parse_args(argv)

    sources = tuple(args.sources) if args.sources else DEFAULT_SOURCES
    catalog = load_catalog(args.catalog)
    errors = validate_catalog(catalog)
    if errors:
        print("Catalog validation warnings:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    updated, report = propose_updates(catalog, sources)
    print(report)

    post_errors = validate_catalog(updated)
    if post_errors:
        print("\nRefusing to apply; post-update validation failed:", file=sys.stderr)
        for err in post_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.apply:
        apply_catalog(args.catalog, updated, report.split("\n")[0])
        print(f"\nApplied -> {args.catalog}")
    else:
        print("\nDry run only. Re-run with --apply to write.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
