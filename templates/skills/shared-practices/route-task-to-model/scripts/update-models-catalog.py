#!/usr/bin/env python3
"""Refresh model tier picks in models-catalog.json from web evidence.

Only ranks models inside the Cursor Task-tool allowlist. Never adds new slugs.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
CATALOG_PATH = SCRIPT_DIR.parent / "models-catalog.json"
MAX_FETCH_BYTES = 5 * 1024 * 1024  # 5 MiB

# Last-resort bootstrap when models-catalog.json lacks cursor_allowlist (corrupt or new file).
BOOTSTRAP_CURSOR_ALLOWLIST: tuple[str, ...] = (
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


def cursor_allowlist_from_catalog(catalog: dict[str, Any]) -> tuple[str, ...]:
    """Canonical allowlist lives in models-catalog.json; bootstrap is fallback only."""
    raw = catalog.get("cursor_allowlist")
    if isinstance(raw, list) and raw and all(isinstance(s, str) and s.strip() for s in raw):
        return tuple(dict.fromkeys(s.strip() for s in raw))
    return BOOTSTRAP_CURSOR_ALLOWLIST


def _slug_aliases(slug: str) -> list[str]:
    """Search terms derived from a Cursor slug."""
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


def fetch_url(url: str, timeout: int = 15, max_bytes: int = MAX_FETCH_BYTES) -> str:
    logger.info("fetch_url_enter", extra={"url": url, "timeout": timeout, "max_bytes": max_bytes})
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "cursor-usage-templates/1.0 (model-catalog-update)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = resp.read(min(65536, max_bytes - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"response exceeds {max_bytes} bytes")
                chunks.append(chunk)
            body = b"".join(chunks).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.error("fetch_url_failed", extra={"url": url, "error_type": type(exc).__name__})
        raise
    logger.info("fetch_url_exit", extra={"url": url, "body_length": len(body)})
    return body


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


def aggregate_scores(corpus: str, allowlist: tuple[str, ...]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for slug in allowlist:
        result[slug] = score_slug_in_text(slug, corpus)
    return result


def pick_tier_winners(
    scores: dict[str, dict[str, int]],
    allowlist: tuple[str, ...],
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
            ordered[tier] = _static_tier_defaults(tier, allowlist)
    return ordered


def _static_tier_defaults(tier: str, allowlist: tuple[str, ...]) -> list[str]:
    defaults = {
        "frontier": ["claude-opus-4-8-thinking-high", "claude-fable-5-thinking-high"],
        "mid_tier": [
            "claude-4.6-sonnet-medium-thinking",
            "gpt-5.5-medium",
            "gpt-5.3-codex",
        ],
        "lightweight": ["composer-2.5-fast", "gpt-5.3-codex"],
    }
    return [s for s in defaults.get(tier, []) if s in allowlist]


def load_catalog(path: Path) -> dict[str, Any]:
    logger.info("load_catalog_enter", extra={"path": str(path)})
    try:
        with path.open(encoding="utf-8") as f:
            catalog = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("load_catalog_failed", extra={"path": str(path), "error_type": type(exc).__name__})
        raise
    logger.info("load_catalog_exit", extra={"path": str(path), "tier_count": len(catalog.get("tiers", {}))})
    return catalog


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    logger.info("validate_catalog_enter", extra={})
    errors: list[str] = []
    allowlist = cursor_allowlist_from_catalog(catalog)
    if not allowlist:
        errors.append("cursor_allowlist is empty or missing")
    allowset = set(allowlist)
    if len(allowset) != len(allowlist):
        errors.append("cursor_allowlist contains duplicate slugs")
    for tier_key, tier in catalog.get("tiers", {}).items():
        primary = tier.get("primary")
        if primary not in allowset:
            errors.append(f"tiers.{tier_key}.primary not in allowlist: {primary}")
        for alt in tier.get("alternates", []):
            if alt not in allowset:
                errors.append(f"tiers.{tier_key} alternate not in allowlist: {alt}")
    logger.info("validate_catalog_exit", extra={"error_count": len(errors)})
    return errors


def propose_updates(
    catalog: dict[str, Any],
    sources: tuple[str, ...],
) -> tuple[dict[str, Any], str]:
    logger.info("propose_updates_enter", extra={"source_count": len(sources)})
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
            logger.warning(
                "propose_updates_fetch_failed",
                extra={"url": url, "error_type": type(exc).__name__},
            )
            source_meta.append(
                {
                    "url": url,
                    "checked_at": today,
                    "notes": f"Fetch failed: {exc}",
                }
            )

    corpus = "\n".join(corpus_parts)
    allowlist = cursor_allowlist_from_catalog(catalog)
    scores = aggregate_scores(corpus, allowlist)
    winners = pick_tier_winners(scores, allowlist)

    updated = json.loads(json.dumps(catalog))  # deep copy
    updated["last_updated"] = today
    updated["cursor_allowlist"] = list(allowlist)

    report_lines = ["Model catalog update proposal", "=" * 40, ""]
    allowset = set(allowlist)

    for tier_key in ("frontier", "mid_tier", "lightweight"):
        slugs = winners.get(tier_key, [])
        if not slugs:
            slugs = _static_tier_defaults(tier_key, allowlist)
        primary = slugs[0]
        alternates = [s for s in slugs[1:] if s in allowset]
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
    for slug in allowlist:
        tier_scores = scores[slug]
        best = max(tier_scores, key=lambda t: tier_scores[t])
        report_lines.append(f"  {slug}: {best}={tier_scores[best]}")

    logger.info(
        "propose_updates_exit",
        extra={"corpus_length": len(corpus), "source_count": len(source_meta)},
    )
    return updated, "\n".join(report_lines)


def apply_catalog(path: Path, catalog: dict[str, Any], summary: str) -> None:
    logger.info("apply_catalog_enter", extra={"path": str(path)})
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
    logger.info("apply_catalog_exit", extra={"path": str(path)})


def main(argv: list[str] | None = None) -> int:
    logger.info("main_enter", extra={"argv_length": len(argv) if argv is not None else 0})
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
    logger.info(
        "main_config",
        extra={"catalog": str(args.catalog), "dry_run": args.dry_run, "source_count": len(sources)},
    )
    catalog = load_catalog(args.catalog)
    errors = validate_catalog(catalog)
    if errors:
        logger.warning("main_catalog_validation_warnings", extra={"warning_count": len(errors)})
        print("Catalog validation warnings:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    updated, report = propose_updates(catalog, sources)
    print(report)

    post_errors = validate_catalog(updated)
    if post_errors:
        logger.error("main_post_validation_failed", extra={"error_count": len(post_errors)})
        print("\nRefusing to apply; post-update validation failed:", file=sys.stderr)
        for err in post_errors:
            print(f"  - {err}", file=sys.stderr)
        logger.info("main_exit", extra={"apply": args.apply, "exit_code": 1})
        return 1

    if args.apply:
        apply_catalog(args.catalog, updated, report.split("\n")[0])
        print(f"\nApplied -> {args.catalog}")
    else:
        print("\nDry run only. Re-run with --apply to write.")

    logger.info("main_exit", extra={"apply": args.apply, "exit_code": 0})
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
