"""Normalize Cursor activity hook payloads and query JSONL logs."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SENSITIVE_PATH_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"\.pem$",
    r"\.key$",
    r"secrets\.",
    r"credentials\.",
    r"config\.local\.",
    r"\.secret",
    r"id_rsa",
    r"id_ed25519",
]

PREVIEW_CHARS = 80
PROMPT_MAX = 50_000
FULL_EDITS_MAX_BYTES = 2048
LOG_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_log_date(date: str) -> str:
    """Reject path traversal and malformed dates for log file selection."""
    if not LOG_DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid date {date!r}: expected YYYY-MM-DD")
    return date


def is_sensitive_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(re.search(pat, normalized, re.IGNORECASE) for pat in SENSITIVE_PATH_PATTERNS)


def infer_event(payload: dict[str, Any]) -> str:
    event = payload.get("hook_event_name") or payload.get("event")
    if event:
        return str(event)
    if payload.get("file_path") is not None and payload.get("edits") is not None:
        return "afterFileEdit"
    if payload.get("prompt") is not None:
        return "beforeSubmitPrompt"
    if payload.get("command") is not None:
        return "beforeShellExecution"
    if payload.get("status") is not None:
        return "stop"
    return "unknown"


def _iso_ts(ts: str | None = None) -> str:
    if ts:
        return ts
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _preview(text: str | None, max_len: int = PREVIEW_CHARS) -> str | None:
    if text is None:
        return None
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "...[truncated]"


def _lines_changed(old: str, new: str) -> str | None:
    old_lines = old.splitlines() if old else []
    new_lines = new.splitlines() if new else []
    added = max(0, len(new_lines) - len(old_lines))
    removed = max(0, len(old_lines) - len(new_lines))
    if added == 0 and removed == 0:
        return None
    return f"+{added},-{removed}"


def summarize_attachments(attachments: Any) -> list[dict[str, str]]:
    if not attachments:
        return []
    items: list[dict[str, str]] = []
    if not isinstance(attachments, list):
        attachments = [attachments]
    for item in attachments:
        if isinstance(item, dict):
            entry: dict[str, str] = {}
            for key in ("type", "file_path", "name"):
                if item.get(key):
                    entry[key] = str(item[key])
            if entry:
                items.append(entry)
        elif isinstance(item, str) and item.strip():
            items.append({"type": "file", "file_path": item.strip()})
    return items


def build_edit_summary(edits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for edit in edits:
        old_s = edit.get("old_string") or ""
        new_s = edit.get("new_string") or ""
        row: dict[str, Any] = {
            "old_preview": _preview(old_s),
            "new_preview": _preview(new_s),
        }
        lc = _lines_changed(old_s, new_s)
        if lc:
            row["lines_changed"] = lc
        summary.append(row)
    return summary


def _edits_total_bytes(edits: list[dict[str, Any]]) -> int:
    total = 0
    for edit in edits:
        total += len(str(edit.get("old_string") or ""))
        total += len(str(edit.get("new_string") or ""))
    return total


def normalize_activity_entry(payload: dict[str, Any], ts: str | None = None) -> dict[str, Any]:
    event = infer_event(payload)
    logger.info(
        "normalize_activity_entry_enter",
        extra={"event": event, "has_timestamp": ts is not None},
    )
    entry: dict[str, Any] = {"ts": _iso_ts(ts), "event": event}

    for key in ("conversation_id", "generation_id"):
        if payload.get(key):
            entry[key] = payload[key]

    if event == "beforeSubmitPrompt":
        prompt = str(payload.get("prompt") or "")
        entry["prompt"] = _truncate(prompt, PROMPT_MAX)
        entry["prompt_length"] = len(prompt)
        attachments = summarize_attachments(payload.get("attachments"))
        if attachments:
            entry["attachments"] = attachments
        logger.info(
            "normalize_activity_entry_exit",
            extra={"event": event, "prompt_length": entry.get("prompt_length", 0)},
        )
        return entry

    if event == "afterFileEdit":
        file_path = str(payload.get("file_path") or "")
        entry["file_path"] = file_path
        if is_sensitive_path(file_path):
            entry["redacted"] = True
            entry["edit_count"] = len(payload.get("edits") or [])
            entry["edit_summary"] = [{"note": "sensitive path — content omitted"}]
            logger.info(
                "normalize_activity_entry_exit",
                extra={"event": event, "redacted": True, "edit_count": entry["edit_count"]},
            )
            return entry

        edits = payload.get("edits") or []
        if not isinstance(edits, list):
            edits = []
        entry["edit_count"] = len(edits)
        entry["edit_summary"] = build_edit_summary(edits)
        if edits and _edits_total_bytes(edits) < FULL_EDITS_MAX_BYTES:
            entry["edits_full"] = edits
        logger.info(
            "normalize_activity_entry_exit",
            extra={"event": event, "edit_count": entry["edit_count"], "redacted": False},
        )
        return entry

    if event == "beforeShellExecution":
        entry["command"] = str(payload.get("command") or "")
        if payload.get("cwd"):
            entry["cwd"] = str(payload["cwd"])
        logger.info("normalize_activity_entry_exit", extra={"event": event, "has_cwd": "cwd" in entry})
        return entry

    if event == "stop":
        entry["status"] = str(payload.get("status") or "")
        logger.info("normalize_activity_entry_exit", extra={"event": event, "status": entry["status"]})
        return entry

    logger.info("normalize_activity_entry_exit", extra={"event": event})
    return entry


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    logger.info("read_jsonl_enter", extra={"path": str(path)})
    if not path.is_file():
        logger.info("read_jsonl_exit", extra={"path": str(path), "row_count": 0, "missing": True})
        return []
    rows: list[dict[str, Any]] = []
    decode_errors = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            decode_errors += 1
            continue
    logger.info(
        "read_jsonl_exit",
        extra={"path": str(path), "row_count": len(rows), "decode_errors": decode_errors},
    )
    return rows


def group_by_generation(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        gen = entry.get("generation_id") or "(no-generation-id)"
        grouped[str(gen)].append(entry)
    return grouped


def format_generation_summary(gen_id: str, events: list[dict[str, Any]]) -> str:
    events = sorted(events, key=lambda e: e.get("ts", ""))
    prompt_event = next((e for e in events if e.get("event") == "beforeSubmitPrompt"), None)
    ts = prompt_event.get("ts", events[0].get("ts", "")) if events else ""
    ts_display = ts.replace("T", " ")[:19] if ts else ""

    lines = [f"Generation {gen_id} ({ts_display})"]
    if prompt_event:
        prompt = prompt_event.get("prompt", "")
        if len(prompt) > 120:
            prompt = prompt[:120] + "..."
        lines.append(f"  Prompt: {prompt}")
    else:
        lines.append("  Prompt: (not logged)")

    files = sorted(
        {
            str(e.get("file_path"))
            for e in events
            if e.get("event") == "afterFileEdit" and e.get("file_path")
        }
    )
    if files:
        lines.append(f"  Files changed: {', '.join(files)}")
    else:
        lines.append("  Files changed: (none)")

    commands = [str(e.get("command")) for e in events if e.get("event") == "beforeShellExecution" and e.get("command")]
    if commands:
        lines.append(f"  Commands: {', '.join(commands)}")

    stop_event = next((e for e in reversed(events) if e.get("event") == "stop"), None)
    status = stop_event.get("status", "(unknown)") if stop_event else "(unknown)"
    lines.append(f"  Status: {status}")
    return "\n".join(lines)


def query_logs(
    project_root: Path,
    date: str | None = None,
    generation_id: str | None = None,
) -> str:
    logger.info(
        "query_logs_enter",
        extra={
            "project_root": str(project_root),
            "date": date or "(all)",
            "has_generation_filter": generation_id is not None,
        },
    )
    log_dir = project_root / ".cursor" / "logs"
    if date:
        safe_date = validate_log_date(date)
        log_files = [log_dir / f"cursor-activity-{safe_date}.jsonl"]
    else:
        log_files = sorted(log_dir.glob("cursor-activity-*.jsonl"))

    entries: list[dict[str, Any]] = []
    for path in log_files:
        entries.extend(read_jsonl(path))

    if generation_id:
        entries = [e for e in entries if str(e.get("generation_id", "")) == generation_id]

    if not entries:
        logger.info("query_logs_exit", extra={"entry_count": 0, "generation_count": 0})
        return "No activity log entries found."

    grouped = group_by_generation(entries)
    blocks = [format_generation_summary(gen_id, evts) for gen_id, evts in sorted(grouped.items())]
    logger.info(
        "query_logs_exit",
        extra={"entry_count": len(entries), "generation_count": len(grouped)},
    )
    return "\n\n".join(blocks)


def cmd_normalize() -> int:
    logger.info("cmd_normalize_enter", extra={})
    raw = sys.stdin.read()
    if not raw.strip():
        logger.info("cmd_normalize_exit", extra={"empty_input": True})
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(
            "cmd_normalize_failed",
            extra={"error_type": type(exc).__name__},
        )
        sys.stdout.write('{"event":"unknown","error":"invalid_json"}\n')
        return 1
    line = json.dumps(normalize_activity_entry(payload), ensure_ascii=False)
    sys.stdout.write(line + "\n")
    logger.info("cmd_normalize_exit", extra={"empty_input": False})
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    logger.info("cmd_query_enter", extra={"command": "query"})
    project_root = Path(args.project_root).resolve()
    if args.date:
        try:
            validate_log_date(args.date)
        except ValueError as exc:
            logger.error("cmd_query_failed", extra={"error": str(exc)})
            sys.stderr.write(f"error: {exc}\n")
            return 1
    output = query_logs(project_root, date=args.date, generation_id=args.generation_id)
    sys.stdout.write(output + "\n")
    logger.info("cmd_query_exit", extra={"output_length": len(output)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cursor activity log utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("normalize", help="Read hook JSON from stdin; write normalized JSON line to stdout")

    query_p = sub.add_parser("query", help="Query cursor-activity JSONL logs")
    query_p.add_argument("--date", help="Log date yyyy-MM-dd")
    query_p.add_argument("--generation-id", dest="generation_id", help="Filter by generation_id")
    query_p.add_argument("--project-root", default=".", help="Project root containing .cursor/logs")
    return parser


def main(argv: list[str] | None = None) -> int:
    logger.info("main_enter", extra={"argv_length": len(argv) if argv is not None else 0})
    parser = build_parser()
    args = parser.parse_args(argv)
    logger.info("main_command", extra={"command": args.command})
    if args.command == "normalize":
        result = cmd_normalize()
    elif args.command == "query":
        result = cmd_query(args)
    else:
        parser.error(f"unknown command: {args.command}")
        return 2
    logger.info("main_exit", extra={"command": args.command, "exit_code": result})
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
