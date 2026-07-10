#!/usr/bin/env python3
"""Validate bot manifests, RAG corpus, and runtime policy JSON for templates/ai-runtime.

CLI:
  python validate_bot_runtime.py manifest <path.json>
  python validate_bot_runtime.py policy <path.json>
  python validate_bot_runtime.py audit-event <path.json>
  python validate_bot_runtime.py corpus <path.json>
  python validate_bot_runtime.py golden <path.json>
  python validate_bot_runtime.py prompt-eval <path.json>
  python validate_bot_runtime.py eval-baseline <path.json>
  python validate_bot_runtime.py judge-calibration <path.json>
"""

from __future__ import annotations

import json
import logging
import re
import sys
import functools
import importlib.util
from pathlib import Path
from typing import Any

_POLICY_REQUIRED_MODES = frozenset(
    {
        "tool_read",
        "tool_write",
        "tool_destructive",
        "tool_unknown",
    }
)
_POLICY_MODE_VALUES = frozenset({"deny", "ask", "allow", "advisory", "log", "off"})
_BOT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_VALID_CHANNELS = frozenset({"slack", "web", "api"})
_VALID_RISKS = frozenset({"read", "write", "destructive"})
_VALID_AUDIT_ACTIONS = frozenset(
    {
        "message_received",
        "message_sent",
        "tool_invoked",
        "policy_blocked",
        "handoff_initiated",
        "handoff_completed",
        "rate_limited",
        "error",
    }
)
_VALID_OUTCOMES = frozenset({"success", "failure", "blocked", "escalated"})
_CORPUS_ID_RE = _BOT_ID_RE
_VALID_CHUNK_STRATEGIES = frozenset({"fixed", "semantic", "structure_aware"})
_VALID_SOURCE_TYPES = frozenset({"markdown", "html", "pdf", "confluence", "api"})
_VALID_INDEX_BACKENDS = frozenset(
    {"pgvector", "pinecone", "weaviate", "opensearch", "chroma"}
)
_VALID_CASE_CATEGORIES = frozenset(
    {"happy_path", "edge_case", "refusal", "adversarial", "tool_use", "multi_turn"}
)
_VALID_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
_VALID_MESSAGE_ROLES = frozenset({"system", "user", "assistant", "tool"})
_VALID_ASSERTION_TYPES = frozenset(
    {
        "must_contain",
        "must_not_contain",
        "regex",
        "max_length",
        "json_schema",
        "tool_call",
        "refusal",
        "no_pii_patterns",
        "llm_judge",
    }
)
_SUITE_ID_RE = _CORPUS_ID_RE


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def validate_manifest(data: Any, *, path: str = "<manifest>") -> list[str]:
    """Return list of validation errors (empty if valid)."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    required = (
        "schema_version",
        "id",
        "channels",
        "persona",
        "model",
        "tools",
        "escalation",
    )
    for key in required:
        if key not in data:
            errors.append(f"{path}: missing required field '{key}'")

    schema_version = data.get("schema_version")
    if schema_version is not None and (
        not isinstance(schema_version, int) or schema_version < 1
    ):
        errors.append(f"{path}: schema_version must be integer >= 1")

    bot_id = data.get("id")
    if bot_id is not None and (
        not isinstance(bot_id, str) or not _BOT_ID_RE.match(bot_id)
    ):
        errors.append(f"{path}: id must match ^[a-z][a-z0-9-]{{2,63}}$")

    channels = data.get("channels")
    if channels is not None:
        if not isinstance(channels, list) or not channels:
            errors.append(f"{path}: channels must be a non-empty array")
        else:
            for ch in channels:
                if ch not in _VALID_CHANNELS:
                    errors.append(f"{path}: invalid channel '{ch}'")

    persona = data.get("persona")
    if isinstance(persona, dict):
        for key in ("tone", "disclosure"):
            if key not in persona:
                errors.append(f"{path}: persona missing '{key}'")
        sys_ref = persona.get("system_prompt_ref")
        if sys_ref is not None and (not isinstance(sys_ref, str) or len(sys_ref) > 256):
            errors.append(
                f"{path}: persona.system_prompt_ref must be string <= 256 chars"
            )
    elif persona is not None:
        errors.append(f"{path}: persona must be an object")

    model = data.get("model")
    if isinstance(model, dict):
        for key in ("provider", "name"):
            if key not in model:
                errors.append(f"{path}: model missing '{key}'")
        max_tokens = model.get("max_tokens_per_turn")
        if max_tokens is not None and (
            isinstance(max_tokens, bool)
            or not isinstance(max_tokens, int)
            or max_tokens < 1
            or max_tokens > 128000
        ):
            errors.append(
                f"{path}: model.max_tokens_per_turn must be integer between 1 and 128000"
            )
    elif model is not None:
        errors.append(f"{path}: model must be an object")

    tools = data.get("tools")
    if isinstance(tools, list):
        for idx, tool in enumerate(tools):
            if not isinstance(tool, dict):
                errors.append(f"{path}: tools[{idx}] must be an object")
                continue
            name = tool.get("name")
            risk = tool.get("risk")
            if not isinstance(name, str) or not _TOOL_NAME_RE.match(name):
                errors.append(f"{path}: tools[{idx}].name invalid")
            if risk not in _VALID_RISKS:
                errors.append(
                    f"{path}: tools[{idx}].risk must be read|write|destructive"
                )
    elif tools is not None:
        errors.append(f"{path}: tools must be an array")

    escalation = data.get("escalation")
    if isinstance(escalation, dict):
        enabled = escalation.get("enabled")
        if "enabled" not in escalation:
            errors.append(f"{path}: escalation missing 'enabled'")
        elif not isinstance(enabled, bool):
            errors.append(f"{path}: escalation.enabled must be a boolean")

        if "sla_minutes" not in escalation:
            errors.append(f"{path}: escalation missing 'sla_minutes'")
        elif (
            not isinstance(escalation["sla_minutes"], int)
            or escalation["sla_minutes"] < 1
        ):
            errors.append(f"{path}: escalation.sla_minutes must be positive integer")

        esc_channel = escalation.get("channel")
        if esc_channel is not None and esc_channel not in {
            "slack",
            "email",
            "ticket",
            "api",
        }:
            errors.append(f"{path}: escalation.channel must be slack|email|ticket|api")
    elif escalation is not None:
        errors.append(f"{path}: escalation must be an object")

    return errors


def validate_policy(data: Any, *, path: str = "<policy>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    if data.get("version") != 1:
        errors.append(f"{path}: version must be 1")

    modes = data.get("modes")
    if not isinstance(modes, dict):
        errors.append(f"{path}: modes must be an object")
    else:
        for mode_key in _POLICY_REQUIRED_MODES:
            if mode_key not in modes:
                errors.append(f"{path}: modes missing '{mode_key}'")
        for key, value in modes.items():
            if value not in _POLICY_MODE_VALUES:
                errors.append(f"{path}: modes.{key} invalid value '{value}'")

    return errors


def validate_corpus(data: Any, *, path: str = "<corpus>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    for key in (
        "schema_version",
        "id",
        "sources",
        "chunking",
        "embedding",
        "retrieval",
    ):
        if key not in data:
            errors.append(f"{path}: missing required field '{key}'")

    schema_version = data.get("schema_version")
    if schema_version is not None and (
        not isinstance(schema_version, int) or schema_version < 1
    ):
        errors.append(f"{path}: schema_version must be integer >= 1")

    corpus_id = data.get("id")
    if corpus_id is not None and (
        not isinstance(corpus_id, str) or not _CORPUS_ID_RE.match(corpus_id)
    ):
        errors.append(f"{path}: id must match ^[a-z][a-z0-9-]{{2,63}}$")

    sources = data.get("sources")
    if isinstance(sources, list):
        if not sources:
            errors.append(f"{path}: sources must be non-empty")
        for idx, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(f"{path}: sources[{idx}] must be an object")
                continue
            if "source_id" not in src or "type" not in src:
                errors.append(f"{path}: sources[{idx}] missing source_id or type")
            elif src.get("type") not in _VALID_SOURCE_TYPES:
                errors.append(f"{path}: sources[{idx}].type invalid")
    elif sources is not None:
        errors.append(f"{path}: sources must be an array")

    chunking = data.get("chunking")
    if isinstance(chunking, dict):
        if chunking.get("strategy") not in _VALID_CHUNK_STRATEGIES:
            errors.append(f"{path}: chunking.strategy invalid")
        max_tokens = chunking.get("max_tokens")
        if (
            isinstance(max_tokens, bool)
            or not isinstance(max_tokens, int)
            or max_tokens < 64
        ):
            errors.append(f"{path}: chunking.max_tokens must be integer >= 64")
        overlap_tokens = chunking.get("overlap_tokens")
        if overlap_tokens is not None and (
            isinstance(overlap_tokens, bool)
            or not isinstance(overlap_tokens, int)
            or overlap_tokens < 0
            or overlap_tokens > 1024
        ):
            errors.append(
                f"{path}: chunking.overlap_tokens must be integer between 0 and 1024"
            )
    elif chunking is not None:
        errors.append(f"{path}: chunking must be an object")

    embedding = data.get("embedding")
    if isinstance(embedding, dict):
        for key in ("provider", "model", "dimensions"):
            if key not in embedding:
                errors.append(f"{path}: embedding missing '{key}'")
        dimensions = embedding.get("dimensions")
        if dimensions is not None and (
            isinstance(dimensions, bool)
            or not isinstance(dimensions, int)
            or dimensions < 1
            or dimensions > 4096
        ):
            errors.append(
                f"{path}: embedding.dimensions must be integer between 1 and 4096"
            )
    elif embedding is not None:
        errors.append(f"{path}: embedding must be an object")

    retrieval = data.get("retrieval")
    if isinstance(retrieval, dict):
        top_k = retrieval.get("top_k")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            errors.append(f"{path}: retrieval.top_k must be positive integer")
        min_score = retrieval.get("min_score")
        if (
            isinstance(min_score, bool)
            or not isinstance(min_score, (int, float))
            or min_score < 0
            or min_score > 1
        ):
            errors.append(f"{path}: retrieval.min_score must be 0-1")
    elif retrieval is not None:
        errors.append(f"{path}: retrieval must be an object")

    index = data.get("index")
    if isinstance(index, dict) and index.get("backend") not in _VALID_INDEX_BACKENDS:
        if "backend" in index:
            errors.append(f"{path}: index.backend invalid")

    return errors


def validate_golden(data: Any, *, path: str = "<golden>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    for key in ("schema_version", "corpus_id", "questions"):
        if key not in data:
            errors.append(f"{path}: missing required field '{key}'")

    schema_version = data.get("schema_version")
    if schema_version is not None and (
        not isinstance(schema_version, int) or schema_version < 1
    ):
        errors.append(f"{path}: schema_version must be integer >= 1")

    corpus_id = data.get("corpus_id")
    if corpus_id is not None and (
        not isinstance(corpus_id, str) or not _CORPUS_ID_RE.match(corpus_id)
    ):
        errors.append(f"{path}: corpus_id invalid")

    questions = data.get("questions")
    if isinstance(questions, list):
        if not questions:
            errors.append(f"{path}: questions must be non-empty")
        for idx, q in enumerate(questions):
            if not isinstance(q, dict):
                errors.append(f"{path}: questions[{idx}] must be an object")
                continue
            if "id" not in q or "question" not in q:
                errors.append(f"{path}: questions[{idx}] missing id or question")
    elif questions is not None:
        errors.append(f"{path}: questions must be an array")

    return errors


def _validate_string_list(
    values: Any,
    *,
    path: str,
    field: str,
    min_items: int = 1,
    max_item_len: int = 256,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(values, list) or len(values) < min_items:
        errors.append(f"{path}: {field} must be a non-empty array")
        return errors
    for idx, item in enumerate(values):
        if not isinstance(item, str) or not item or len(item) > max_item_len:
            errors.append(f"{path}: {field}[{idx}] invalid string")
    return errors


def _validate_assertion(
    assertion: Any, *, path: str, case_idx: int, assertion_idx: int
) -> list[str]:
    prefix = f"{path}: cases[{case_idx}].assertions[{assertion_idx}]"
    errors: list[str] = []
    if not isinstance(assertion, dict):
        return [f"{prefix} must be an object"]

    atype = assertion.get("type")
    if atype not in _VALID_ASSERTION_TYPES:
        errors.append(f"{prefix}.type invalid")
        return errors

    if atype == "must_contain" or atype == "must_not_contain":
        errors.extend(
            _validate_string_list(assertion.get("values"), path=prefix, field="values")
        )
    elif atype == "regex":
        pattern = assertion.get("pattern")
        if not isinstance(pattern, str) or not pattern or len(pattern) > 512:
            errors.append(f"{prefix}.pattern invalid")
        must_match = assertion.get("must_match", True)
        if must_match is not None and not isinstance(must_match, bool):
            errors.append(f"{prefix}.must_match must be boolean")
    elif atype == "max_length":
        chars = assertion.get("chars")
        if (
            isinstance(chars, bool)
            or not isinstance(chars, int)
            or chars < 1
            or chars > 100000
        ):
            errors.append(f"{prefix}.chars must be integer between 1 and 100000")
    elif atype == "json_schema":
        if not isinstance(assertion.get("schema"), dict):
            errors.append(f"{prefix}.schema must be an object")
    elif atype == "tool_call":
        name = assertion.get("name")
        if not isinstance(name, str) or not name or len(name) > 128:
            errors.append(f"{prefix}.name invalid")
        args_schema = assertion.get("args_schema")
        if args_schema is not None and not isinstance(args_schema, dict):
            errors.append(f"{prefix}.args_schema must be an object")
    elif atype == "refusal":
        if not isinstance(assertion.get("expected"), bool):
            errors.append(f"{prefix}.expected must be boolean")
    elif atype == "no_pii_patterns":
        patterns = assertion.get("patterns")
        if patterns is not None:
            if not isinstance(patterns, list):
                errors.append(f"{prefix}.patterns must be an array")
            else:
                for idx, item in enumerate(patterns):
                    if not isinstance(item, str) or len(item) > 128:
                        errors.append(f"{prefix}.patterns[{idx}] invalid")
    elif atype == "llm_judge":
        rubric = assertion.get("rubric")
        if not isinstance(rubric, str) or not rubric or len(rubric) > 2048:
            errors.append(f"{prefix}.rubric invalid")
        min_score = assertion.get("min_score")
        if not isinstance(min_score, (int, float)) or min_score < 0 or min_score > 1:
            errors.append(f"{prefix}.min_score must be number between 0 and 1")
        judge_model = assertion.get("judge_model")
        if judge_model is not None and (
            not isinstance(judge_model, str) or len(judge_model) > 128
        ):
            errors.append(f"{prefix}.judge_model invalid")

    return errors


def _validate_prompt_eval_case(case: Any, *, path: str, case_idx: int) -> list[str]:
    prefix = f"{path}: cases[{case_idx}]"
    errors: list[str] = []
    if not isinstance(case, dict):
        return [f"{prefix} must be an object"]

    for key in ("id", "category", "input", "assertions"):
        if key not in case:
            errors.append(f"{prefix} missing '{key}'")

    case_id = case.get("id")
    if case_id is not None and (
        not isinstance(case_id, str) or not case_id or len(case_id) > 64
    ):
        errors.append(f"{prefix}.id invalid")

    category = case.get("category")
    if category is not None and category not in _VALID_CASE_CATEGORIES:
        errors.append(f"{prefix}.category invalid")

    severity = case.get("severity")
    if severity is not None and severity not in _VALID_SEVERITIES:
        errors.append(f"{prefix}.severity invalid")

    tags = case.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or len(tags) > 16:
            errors.append(f"{prefix}.tags must be array with at most 16 items")
        else:
            for idx, tag in enumerate(tags):
                if not isinstance(tag, str) or len(tag) > 64:
                    errors.append(f"{prefix}.tags[{idx}] invalid")

    prompt_version = case.get("prompt_version")
    if prompt_version is not None and (
        not isinstance(prompt_version, str) or len(prompt_version) > 64
    ):
        errors.append(f"{prefix}.prompt_version invalid")

    notes = case.get("notes")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 512):
        errors.append(f"{prefix}.notes invalid")

    inp = case.get("input")
    if isinstance(inp, dict):
        messages = inp.get("messages")
        if not isinstance(messages, list) or not messages:
            errors.append(f"{prefix}.input.messages must be non-empty array")
        else:
            for msg_idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    errors.append(
                        f"{prefix}.input.messages[{msg_idx}] must be an object"
                    )
                    continue
                role = msg.get("role")
                content = msg.get("content")
                if role not in _VALID_MESSAGE_ROLES:
                    errors.append(f"{prefix}.input.messages[{msg_idx}].role invalid")
                if not isinstance(content, str) or not content or len(content) > 8192:
                    errors.append(f"{prefix}.input.messages[{msg_idx}].content invalid")
        context = inp.get("context")
        if context is not None and not isinstance(context, dict):
            errors.append(f"{prefix}.input.context must be an object")
    elif inp is not None:
        errors.append(f"{prefix}.input must be an object")

    assertions = case.get("assertions")
    if isinstance(assertions, list):
        if not assertions:
            errors.append(f"{prefix}.assertions must be non-empty")
        for assertion_idx, assertion in enumerate(assertions):
            errors.extend(
                _validate_assertion(
                    assertion, path=path, case_idx=case_idx, assertion_idx=assertion_idx
                )
            )
    elif assertions is not None:
        errors.append(f"{prefix}.assertions must be an array")

    return errors


def validate_prompt_eval(data: Any, *, path: str = "<prompt-eval>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    for key in ("schema_version", "suite_id", "prompt_id", "cases"):
        if key not in data:
            errors.append(f"{path}: missing required field '{key}'")

    schema_version = data.get("schema_version")
    if schema_version is not None and (
        not isinstance(schema_version, int) or schema_version < 1
    ):
        errors.append(f"{path}: schema_version must be integer >= 1")

    suite_id = data.get("suite_id")
    if suite_id is not None and (
        not isinstance(suite_id, str) or not _SUITE_ID_RE.match(suite_id)
    ):
        errors.append(f"{path}: suite_id invalid")

    prompt_id = data.get("prompt_id")
    if prompt_id is not None and (
        not isinstance(prompt_id, str) or not prompt_id or len(prompt_id) > 128
    ):
        errors.append(f"{path}: prompt_id invalid")

    prompt_version = data.get("prompt_version")
    if prompt_version is not None and (
        not isinstance(prompt_version, str) or len(prompt_version) > 64
    ):
        errors.append(f"{path}: prompt_version invalid")

    description = data.get("description")
    if description is not None and (
        not isinstance(description, str) or len(description) > 512
    ):
        errors.append(f"{path}: description invalid")

    model = data.get("model")
    if model is not None and (not isinstance(model, str) or len(model) > 128):
        errors.append(f"{path}: model invalid")

    temperature = data.get("temperature")
    if temperature is not None and (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or temperature < 0
        or temperature > 2
    ):
        errors.append(f"{path}: temperature must be number between 0 and 2")

    corpus_version = data.get("corpus_version")
    if corpus_version is not None and (
        not isinstance(corpus_version, str) or len(corpus_version) > 64
    ):
        errors.append(f"{path}: corpus_version invalid")

    pass_threshold = data.get("pass_threshold")
    if pass_threshold is not None and (
        isinstance(pass_threshold, bool)
        or not isinstance(pass_threshold, (int, float))
        or pass_threshold < 0
        or pass_threshold > 1
    ):
        errors.append(f"{path}: pass_threshold must be number between 0 and 1")

    cases = data.get("cases")
    if isinstance(cases, list):
        if not cases:
            errors.append(f"{path}: cases must be non-empty")
        for case_idx, case in enumerate(cases):
            errors.extend(
                _validate_prompt_eval_case(case, path=path, case_idx=case_idx)
            )
    elif cases is not None:
        errors.append(f"{path}: cases must be an array")

    return errors


def validate_eval_baseline(data: Any, *, path: str = "<eval-baseline>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    for key in (
        "schema_version",
        "suite_id",
        "prompt_id",
        "recorded_at",
        "pass_rate",
        "case_results",
    ):
        if key not in data:
            errors.append(f"{path}: missing required field '{key}'")

    schema_version = data.get("schema_version")
    if schema_version is not None and (
        not isinstance(schema_version, int) or schema_version < 1
    ):
        errors.append(f"{path}: schema_version must be integer >= 1")

    suite_id = data.get("suite_id")
    if suite_id is not None and (
        not isinstance(suite_id, str) or not _SUITE_ID_RE.match(suite_id)
    ):
        errors.append(f"{path}: suite_id invalid")

    prompt_id = data.get("prompt_id")
    if prompt_id is not None and (
        not isinstance(prompt_id, str) or not prompt_id or len(prompt_id) > 128
    ):
        errors.append(f"{path}: prompt_id invalid")

    prompt_version = data.get("prompt_version")
    if prompt_version is not None and (
        not isinstance(prompt_version, str) or len(prompt_version) > 64
    ):
        errors.append(f"{path}: prompt_version invalid")

    model = data.get("model")
    if model is not None and (not isinstance(model, str) or len(model) > 128):
        errors.append(f"{path}: model invalid")

    recorded_at = data.get("recorded_at")
    if recorded_at is not None and (
        not isinstance(recorded_at, str) or not recorded_at or len(recorded_at) > 64
    ):
        errors.append(f"{path}: recorded_at invalid")

    pass_rate = data.get("pass_rate")
    if pass_rate is not None and (
        isinstance(pass_rate, bool)
        or not isinstance(pass_rate, (int, float))
        or pass_rate < 0
        or pass_rate > 1
    ):
        errors.append(f"{path}: pass_rate must be number between 0 and 1")

    case_results = data.get("case_results")
    if isinstance(case_results, list):
        if not case_results:
            errors.append(f"{path}: case_results must be non-empty")
        for idx, row in enumerate(case_results):
            if not isinstance(row, dict):
                errors.append(f"{path}: case_results[{idx}] must be an object")
                continue
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id or len(row_id) > 64:
                errors.append(f"{path}: case_results[{idx}].id invalid")
            if "passed" not in row or not isinstance(row.get("passed"), bool):
                errors.append(f"{path}: case_results[{idx}].passed must be boolean")
            grader_type = row.get("grader_type")
            if grader_type is not None and (
                not isinstance(grader_type, str) or len(grader_type) > 64
            ):
                errors.append(f"{path}: case_results[{idx}].grader_type invalid")
    elif case_results is not None:
        errors.append(f"{path}: case_results must be an array")

    return errors


@functools.lru_cache(maxsize=1)
def _judge_calibration_validator():
    module_path = Path(__file__).parent / "eval" / "llm_judge_calibration.py"
    spec = importlib.util.spec_from_file_location("llm_judge_calibration", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load judge calibration module from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate_judge_calibration(
    data: Any, *, path: str = "<judge-calibration>"
) -> list[str]:
    return _judge_calibration_validator().validate_judge_calibration(data, path=path)


def validate_audit_event(data: Any, *, path: str = "<audit>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    for key in (
        "timestamp",
        "conversation_id",
        "turn_id",
        "actor",
        "action",
        "outcome",
    ):
        if key not in data:
            errors.append(f"{path}: missing '{key}'")

    action = data.get("action")
    if action is not None and action not in _VALID_AUDIT_ACTIONS:
        errors.append(f"{path}: invalid action '{action}'")

    outcome = data.get("outcome")
    if outcome is not None and outcome not in _VALID_OUTCOMES:
        errors.append(f"{path}: invalid outcome '{outcome}'")

    channel = data.get("channel")
    if channel is not None and channel not in _VALID_CHANNELS:
        errors.append(f"{path}: invalid channel '{channel}'")

    actor = data.get("actor")
    if isinstance(actor, dict):
        actor_type = actor.get("type")
        if "type" not in actor:
            errors.append(f"{path}: actor missing 'type'")
        elif actor_type not in {"user", "bot", "system", "human_agent"}:
            errors.append(f"{path}: actor.type invalid")
    elif actor is not None:
        errors.append(f"{path}: actor must be an object")

    return errors


def validate_manifest_file(path: Path) -> list[str]:
    return validate_manifest(_load_json(path), path=str(path))


def validate_policy_file(path: Path) -> list[str]:
    return validate_policy(_load_json(path), path=str(path))


def validate_audit_file(path: Path) -> list[str]:
    return validate_audit_event(_load_json(path), path=str(path))


def validate_corpus_file(path: Path) -> list[str]:
    return validate_corpus(_load_json(path), path=str(path))


def validate_golden_file(path: Path) -> list[str]:
    return validate_golden(_load_json(path), path=str(path))


def validate_prompt_eval_file(path: Path) -> list[str]:
    return validate_prompt_eval(_load_json(path), path=str(path))


def validate_eval_baseline_file(path: Path) -> list[str]:
    return validate_eval_baseline(_load_json(path), path=str(path))


def validate_judge_calibration_file(path: Path) -> list[str]:
    return validate_judge_calibration(_load_json(path), path=str(path))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(
            "usage: validate_bot_runtime.py "
            "<manifest|policy|audit-event|corpus|golden|prompt-eval|eval-baseline|judge-calibration> <file.json>",
            file=sys.stderr,
        )
        return 2

    kind, file_arg = args[0], args[1]
    path = Path(file_arg)
    if not path.is_file():
        print(f"file not found: {path}", file=sys.stderr)
        return 2

    if kind == "manifest":
        errors = validate_manifest_file(path)
    elif kind == "policy":
        errors = validate_policy_file(path)
    elif kind == "audit-event":
        errors = validate_audit_file(path)
    elif kind == "corpus":
        errors = validate_corpus_file(path)
    elif kind == "golden":
        errors = validate_golden_file(path)
    elif kind == "prompt-eval":
        errors = validate_prompt_eval_file(path)
    elif kind == "eval-baseline":
        errors = validate_eval_baseline_file(path)
    elif kind == "judge-calibration":
        errors = validate_judge_calibration_file(path)
    else:
        print(f"unknown kind: {kind}", file=sys.stderr)
        return 2

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
