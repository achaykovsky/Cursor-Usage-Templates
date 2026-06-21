"""Tests for update-models-catalog.py.

The catalog drives route-model skill output; validation must reject slugs
outside Cursor's allowlist and offline refresh must fall back to static tiers.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

# Hyphenated filename requires explicit spec loading — not importable as a package
_spec = importlib.util.spec_from_file_location(
    "update_models_catalog",
    SCRIPT_DIR / "update-models-catalog.py",
)
assert _spec and _spec.loader
umc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(umc)


@pytest.fixture
def sample_catalog(tmpdir) -> Path:
    """Writable copy of the skill catalog so apply/validate tests do not mutate the repo."""
    catalog_path = Path(str(tmpdir)) / "models-catalog.json"
    catalog_path.write_text(
        (SKILL_DIR / "models-catalog.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return catalog_path


def test_validate_catalog_ok(sample_catalog: Path) -> None:
    """Shipped catalog must pass validation — baseline sanity for CI."""
    catalog = umc.load_catalog(sample_catalog)
    assert umc.validate_catalog(catalog) == []


def test_validate_rejects_tier_primary_not_in_allowlist(sample_catalog: Path) -> None:
    """Tier primaries must be members of cursor_allowlist."""
    catalog = umc.load_catalog(sample_catalog)
    catalog["tiers"]["lightweight"]["primary"] = "fake-model"
    errors = umc.validate_catalog(catalog)
    assert any("primary not in allowlist" in e for e in errors)


def test_cursor_allowlist_from_catalog_uses_json() -> None:
    """Canonical allowlist is read from the catalog file, not hardcoded Python."""
    catalog = {"cursor_allowlist": ["composer-2.5-fast", "gpt-5.5-medium"]}
    assert umc.cursor_allowlist_from_catalog(catalog) == (
        "composer-2.5-fast",
        "gpt-5.5-medium",
    )


def test_pick_tier_winners_from_corpus() -> None:
    """Keyword scoring maps marketing prose to tier primary slugs without network."""
    corpus = """
    Claude Opus is best for complex architecture and deep reasoning.
    Sonnet and GPT-5.5 are balanced for daily development.
    Composer is fast for boilerplate and multi-file agentic edits.
    """
    allowlist = umc.BOOTSTRAP_CURSOR_ALLOWLIST
    scores = umc.aggregate_scores(corpus, allowlist)
    winners = umc.pick_tier_winners(scores, allowlist)
    assert "claude-opus-4-8-thinking-high" in winners["frontier"]
    assert winners["lightweight"][0] == "composer-2.5-fast"


def test_propose_updates_offline_uses_static_defaults(
    sample_catalog: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When fetch fails, propose_updates must still emit valid tiers from static defaults."""
    def fail_fetch(_url: str, timeout: int = 15) -> str:
        raise OSError("offline")

    monkeypatch.setattr(umc, "fetch_url", fail_fetch)
    catalog = umc.load_catalog(sample_catalog)
    updated, report = umc.propose_updates(catalog, ("https://example.invalid",))
    assert "frontier:" in report
    assert updated["tiers"]["lightweight"]["primary"] == "composer-2.5-fast"
    assert umc.validate_catalog(updated) == []


def test_apply_writes_changelog(sample_catalog: Path) -> None:
    """apply_catalog appends changelog entries for audit trail of manual or web refreshes."""
    catalog = umc.load_catalog(sample_catalog)
    umc.apply_catalog(sample_catalog, catalog, "test apply")
    saved = json.loads(sample_catalog.read_text(encoding="utf-8"))
    assert saved["changelog"][-1]["summary"].startswith("Web refresh:")


def test_fetch_url_rejects_oversized_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP responses must be capped to prevent unbounded memory use on malicious URLs."""

    class FakeResp:
        def read(self, n: int = -1) -> bytes:
            return b"x" * (n if n > 0 else 128)

        def __enter__(self) -> "FakeResp":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_urlopen(_req: object, timeout: int = 15) -> FakeResp:
        return FakeResp()

    monkeypatch.setattr(umc.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ValueError, match="exceeds"):
        umc.fetch_url("https://example.com", max_bytes=64)
