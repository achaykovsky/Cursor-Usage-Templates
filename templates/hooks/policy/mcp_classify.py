"""Shared MCP tool-name risk heuristics for hook_policy and sync_mcp_policy."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

Risk = Literal["read", "write", "unknown"]

logger = logging.getLogger(__name__)

_DEFAULT_READ_PREFIXES = (
    "get_",
    "list_",
    "fetch_",
    "search_",
    "describe_",
    "show_",
    "view_",
)
_DEFAULT_READ_CONTAINS = (
    "_get_",
    "_list_",
    "_read_",
    "_fetch_",
    "_search_",
    "_describe_",
    "_show_",
)
_DEFAULT_WRITE_PREFIXES = (
    "create_",
    "update_",
    "delete_",
    "insert_",
    "drop_",
    "upsert_",
    "publish_",
    "deploy_",
)
_DEFAULT_WRITE_EXACT = (
    "git_push",
    "git_add_or_commit",
    "issues_create",
    "issues_add_comment",
    "pull_request_create",
    "pull_request_create_review",
)
_DEFAULT_WRITE_NAME_PATTERN = r"(^|[_-])(push|merge|close|assign|comment|tag)($|[_-])"
_READ_SPECIALS = frozenset({"mcp_auth"})


@dataclass(frozen=True)
class McpHeuristics:
    read_prefixes: tuple[str, ...] = _DEFAULT_READ_PREFIXES
    read_contains: tuple[str, ...] = _DEFAULT_READ_CONTAINS
    write_prefixes: tuple[str, ...] = _DEFAULT_WRITE_PREFIXES
    write_exact: tuple[str, ...] = _DEFAULT_WRITE_EXACT
    write_name_pattern: str = _DEFAULT_WRITE_NAME_PATTERN
    read_specials: frozenset[str] = _READ_SPECIALS


def load_mcp_heuristics(policy: dict[str, Any] | None) -> McpHeuristics:
    """Load MCP heuristics from a policy fragment (typically policy['mcp'])."""
    logger.info("load_mcp_heuristics_enter", extra={"has_policy": policy is not None})
    mcp_cfg = (policy or {}).get("mcp") or {}
    heuristics = McpHeuristics(
        read_prefixes=tuple(mcp_cfg.get("global_read_prefixes") or _DEFAULT_READ_PREFIXES),
        read_contains=tuple(mcp_cfg.get("global_read_contains") or _DEFAULT_READ_CONTAINS),
        write_prefixes=tuple(mcp_cfg.get("global_write_prefixes") or _DEFAULT_WRITE_PREFIXES),
        write_exact=tuple(mcp_cfg.get("global_write_exact") or _DEFAULT_WRITE_EXACT),
        write_name_pattern=str(
            mcp_cfg.get("global_write_name_pattern") or _DEFAULT_WRITE_NAME_PATTERN
        ),
    )
    logger.info("load_mcp_heuristics_exit", extra={"read_prefix_count": len(heuristics.read_prefixes)})
    return heuristics


def classify_tool_name(name: str, heuristics: McpHeuristics | None = None) -> Risk:
    """Classify an MCP tool name using shared prefix/fragment heuristics."""
    logger.info("classify_tool_name_enter", extra={"tool_name": name})
    rules = heuristics or McpHeuristics()
    if name in rules.read_specials:
        logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "read", "match": "read_special"})
        return "read"
    for prefix in rules.read_prefixes:
        if name.startswith(prefix):
            logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "read", "match": "read_prefix"})
            return "read"
    for frag in rules.read_contains:
        if frag in name:
            logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "read", "match": "read_contains"})
            return "read"
    for exact in rules.write_exact:
        if name == exact:
            logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "write", "match": "write_exact"})
            return "write"
    for prefix in rules.write_prefixes:
        if name.startswith(prefix):
            logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "write", "match": "write_prefix"})
            return "write"
    if rules.write_name_pattern and re.search(rules.write_name_pattern, name):
        logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "write", "match": "write_pattern"})
        return "write"
    logger.info("classify_tool_name_exit", extra={"tool_name": name, "risk": "unknown"})
    return "unknown"
