"""Filesystem anchors for routing catalog resolution."""

from __future__ import annotations

from pathlib import Path

COMMANDS_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = COMMANDS_DIR.parent
