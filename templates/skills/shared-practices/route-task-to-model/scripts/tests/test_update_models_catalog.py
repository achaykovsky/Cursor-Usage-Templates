"""Tests for update-models-catalog.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

_spec = importlib.util.spec_from_file_location(
    "update_models_catalog",
    SCRIPT_DIR / "update-models-catalog.py",
)
assert _spec and _spec.loader
umc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(umc)


@pytest.fixture
def sample_catalog(tmpdir) -> Path:
    catalog_path = Path(str(tmpdir)) / "models-catalog.json"
    catalog_path.write_text(
        (SKILL_DIR / "models-catalog.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return catalog_path


def test_validate_catalog_ok(sample_catalog: Path) -> None:
    catalog = umc.load_catalog(sample_catalog)
    assert umc.validate_catalog(catalog) == []


def test_validate_rejects_unknown_slug(sample_catalog: Path) -> None:
    catalog = umc.load_catalog(sample_catalog)
    catalog["cursor_allowlist"] = list(umc.CURSOR_ALLOWLIST) + ["fake-model"]
    errors = umc.validate_catalog(catalog)
    assert any("unknown slugs" in e for e in errors)


def test_pick_tier_winners_from_corpus() -> None:
    corpus = """
    Claude Opus is best for complex architecture and deep reasoning.
    Sonnet and GPT-5.5 are balanced for daily development.
    Composer is fast for boilerplate and multi-file agentic edits.
    """
    scores = umc.aggregate_scores(corpus)
    winners = umc.pick_tier_winners(scores)
    assert "claude-opus-4-8-thinking-high" in winners["frontier"]
    assert winners["lightweight"][0] == "composer-2.5-fast"


def test_propose_updates_offline_uses_static_defaults(
    sample_catalog: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_fetch(_url: str, timeout: int = 15) -> str:
        raise OSError("offline")

    monkeypatch.setattr(umc, "fetch_url", fail_fetch)
    catalog = umc.load_catalog(sample_catalog)
    updated, report = umc.propose_updates(catalog, ("https://example.invalid",))
    assert "frontier:" in report
    assert updated["tiers"]["lightweight"]["primary"] == "composer-2.5-fast"
    assert umc.validate_catalog(updated) == []


def test_apply_writes_changelog(sample_catalog: Path) -> None:
    catalog = umc.load_catalog(sample_catalog)
    umc.apply_catalog(sample_catalog, catalog, "test apply")
    saved = json.loads(sample_catalog.read_text(encoding="utf-8"))
    assert saved["changelog"][-1]["summary"].startswith("Web refresh:")
