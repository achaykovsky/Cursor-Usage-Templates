#!/usr/bin/env python3
"""Offline graders for prompt eval suites (deterministic assertions only).

CLI:
  python prompt_eval_runner.py grade --suite <suite.json> --responses <responses.json>
  python prompt_eval_runner.py compare --suite <suite.json> --responses <responses.json> --baseline <baseline.json>

responses.json shape: {"case_id": "model output text", ...}
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_PII_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
)

REFUSAL_MARKERS: tuple[str, ...] = (
    "i can't",
    "i cannot",
    "unable to",
    "not able to",
    "won't help",
    "cannot help",
    "can't help",
    "i'm not able",
    "against policy",
    "not allowed",
)


@dataclass(frozen=True)
class AssertionResult:
    assertion_type: str
    passed: bool
    message: str
    skipped: bool = False


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    assertion_results: tuple[AssertionResult, ...]


@dataclass(frozen=True)
class SuiteResult:
    suite_id: str
    pass_rate: float
    case_results: tuple[CaseResult, ...]
    skipped_assertions: int


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def _norm(text: str) -> str:
    return text.lower().strip()


def _looks_like_refusal(text: str) -> bool:
    normalized = _norm(text)
    return any(marker in normalized for marker in REFUSAL_MARKERS)


def grade_assertion(
    assertion: dict[str, Any],
    response_text: str,
    *,
    tool_calls: list[dict[str, Any]] | None = None,
) -> AssertionResult:
    """Grade one assertion against model output. llm_judge is skipped offline."""
    atype = assertion.get("type")
    if atype == "llm_judge":
        return AssertionResult(
            assertion_type=atype,
            passed=False,
            message="llm_judge requires live judge integration — skipped offline",
            skipped=True,
        )

    if atype == "must_contain":
        values = assertion.get("values", [])
        missing = [v for v in values if _norm(v) not in _norm(response_text)]
        if missing:
            return AssertionResult(atype, False, f"missing required values: {missing}")
        return AssertionResult(atype, True, "ok")

    if atype == "must_not_contain":
        values = assertion.get("values", [])
        found = [v for v in values if _norm(v) in _norm(response_text)]
        if found:
            return AssertionResult(atype, False, f"forbidden values present: {found}")
        return AssertionResult(atype, True, "ok")

    if atype == "regex":
        pattern = assertion.get("pattern", "")
        must_match = assertion.get("must_match", True)
        try:
            matched = re.search(pattern, response_text) is not None
        except re.error as exc:
            return AssertionResult(atype, False, f"invalid regex: {exc}")
        if must_match and not matched:
            return AssertionResult(atype, False, f"pattern not found: {pattern}")
        if not must_match and matched:
            return AssertionResult(atype, False, f"pattern must not match: {pattern}")
        return AssertionResult(atype, True, "ok")

    if atype == "max_length":
        limit = assertion.get("chars", 0)
        if len(response_text) > limit:
            return AssertionResult(atype, False, f"length {len(response_text)} exceeds {limit}")
        return AssertionResult(atype, True, "ok")

    if atype == "refusal":
        expected = assertion.get("expected")
        is_refusal = _looks_like_refusal(response_text)
        if expected is True and not is_refusal:
            return AssertionResult(atype, False, "expected refusal but response appears compliant")
        if expected is False and is_refusal:
            return AssertionResult(atype, False, "expected answer but response looks like refusal")
        return AssertionResult(atype, True, "ok")

    if atype == "no_pii_patterns":
        custom = assertion.get("patterns") or []
        patterns = list(DEFAULT_PII_PATTERNS)
        for raw in custom:
            try:
                patterns.append(re.compile(raw))
            except re.error as exc:
                return AssertionResult(atype, False, f"invalid custom PII pattern: {exc}")
        for pattern in patterns:
            if pattern.search(response_text):
                return AssertionResult(atype, False, f"PII-like pattern matched: {pattern.pattern}")
        return AssertionResult(atype, True, "ok")

    if atype == "tool_call":
        name = assertion.get("name")
        calls = tool_calls or []
        matching = [c for c in calls if c.get("name") == name]
        if not matching:
            return AssertionResult(atype, False, f"tool call '{name}' not found")
        args_schema = assertion.get("args_schema")
        if args_schema and isinstance(args_schema, dict):
            required = args_schema.get("required", [])
            for call in matching:
                args = call.get("args") or {}
                missing = [k for k in required if k not in args]
                if missing:
                    return AssertionResult(atype, False, f"tool '{name}' missing args: {missing}")
        return AssertionResult(atype, True, "ok")

    if atype == "json_schema":
        # Minimal structural check without jsonschema dependency.
        schema = assertion.get("schema")
        if not isinstance(schema, dict):
            return AssertionResult(atype, False, "json_schema assertion missing schema object")
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            return AssertionResult(atype, False, "response is not valid JSON")
        if schema.get("type") == "object" and not isinstance(parsed, dict):
            return AssertionResult(atype, False, "expected JSON object")
        required = schema.get("required", [])
        if isinstance(parsed, dict):
            missing = [k for k in required if k not in parsed]
            if missing:
                return AssertionResult(atype, False, f"JSON missing required keys: {missing}")
        return AssertionResult(atype, True, "ok")

    return AssertionResult(str(atype), False, f"unknown assertion type: {atype}")


def grade_case(
    case: dict[str, Any],
    response_text: str,
    *,
    tool_calls: list[dict[str, Any]] | None = None,
) -> CaseResult:
    case_id = str(case.get("id", "<unknown>"))
    results: list[AssertionResult] = []
    for assertion in case.get("assertions", []):
        if not isinstance(assertion, dict):
            results.append(AssertionResult("invalid", False, "assertion must be an object"))
            continue
        results.append(grade_assertion(assertion, response_text, tool_calls=tool_calls))

    graded = [r for r in results if not r.skipped]
    passed = bool(graded) and all(r.passed for r in graded)
    if not graded:
        passed = False
    return CaseResult(case_id=case_id, passed=passed, assertion_results=tuple(results))


def grade_suite(suite: dict[str, Any], responses: dict[str, str]) -> SuiteResult:
    suite_id = str(suite.get("suite_id", "<unknown>"))
    case_results: list[CaseResult] = []
    skipped = 0

    for case in suite.get("cases", []):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id", ""))
        response_text = responses.get(case_id, "")
        if not response_text:
            case_results.append(
                CaseResult(
                    case_id=case_id,
                    passed=False,
                    assertion_results=(AssertionResult("missing_response", False, "no response provided"),),
                )
            )
            continue
        result = grade_case(case, response_text)
        skipped += sum(1 for r in result.assertion_results if r.skipped)
        case_results.append(result)

    graded_cases = [c for c in case_results if c.assertion_results and not all(a.skipped for a in c.assertion_results)]
    pass_count = sum(1 for c in graded_cases if c.passed)
    pass_rate = pass_count / len(graded_cases) if graded_cases else 0.0

    logger.info(
        "grade_suite_complete",
        extra={"suite_id": suite_id, "pass_rate": pass_rate, "case_count": len(case_results)},
    )
    return SuiteResult(
        suite_id=suite_id,
        pass_rate=pass_rate,
        case_results=tuple(case_results),
        skipped_assertions=skipped,
    )


def compare_to_baseline(
    suite_result: SuiteResult,
    baseline: dict[str, Any],
    *,
    regression_tolerance: float = 0.0,
) -> list[str]:
    """Return regression errors (empty if within tolerance)."""
    errors: list[str] = []
    baseline_rate = baseline.get("pass_rate")
    if isinstance(baseline_rate, (int, float)):
        delta = suite_result.pass_rate - float(baseline_rate)
        if delta < -regression_tolerance:
            errors.append(
                f"pass_rate regression: {suite_result.pass_rate:.3f} vs baseline {baseline_rate:.3f} "
                f"(tolerance {regression_tolerance})"
            )

    baseline_cases = {
        str(row.get("id")): bool(row.get("passed"))
        for row in baseline.get("case_results", [])
        if isinstance(row, dict) and "id" in row
    }
    for case in suite_result.case_results:
        expected = baseline_cases.get(case.case_id)
        if expected is True and not case.passed:
            errors.append(f"case '{case.case_id}' regressed (was passing in baseline)")
    return errors


def suite_meets_threshold(suite: dict[str, Any], suite_result: SuiteResult) -> bool:
    threshold = suite.get("pass_threshold", 1.0)
    if not isinstance(threshold, (int, float)):
        return suite_result.pass_rate >= 1.0
    return suite_result.pass_rate >= float(threshold)


def _suite_result_to_report(suite_result: SuiteResult) -> dict[str, Any]:
    return {
        "suite_id": suite_result.suite_id,
        "pass_rate": suite_result.pass_rate,
        "skipped_assertions": suite_result.skipped_assertions,
        "cases": [
            {
                "id": c.case_id,
                "passed": c.passed,
                "assertions": [
                    {
                        "type": a.assertion_type,
                        "passed": a.passed,
                        "skipped": a.skipped,
                        "message": a.message,
                    }
                    for a in c.assertion_results
                ],
            }
            for c in suite_result.case_results
        ],
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Grade prompt eval suites offline")
    sub = parser.add_subparsers(dest="command", required=True)

    grade_p = sub.add_parser("grade", help="Grade suite against canned responses")
    grade_p.add_argument("--suite", required=True, type=Path)
    grade_p.add_argument("--responses", required=True, type=Path)
    grade_p.add_argument("--baseline", type=Path, default=None)
    grade_p.add_argument("--regression-tolerance", type=float, default=0.0)
    grade_p.add_argument("--json", action="store_true", help="Emit JSON report on stdout")

    args = parser.parse_args(argv)

    if args.command == "grade":
        suite = _load_json(args.suite)
        responses = _load_json(args.responses)
        if not isinstance(responses, dict):
            print("responses file must be a JSON object mapping case id to output text", file=sys.stderr)
            return 2

        suite_result = grade_suite(suite, {str(k): str(v) for k, v in responses.items()})
        errors: list[str] = []

        if not suite_meets_threshold(suite, suite_result):
            threshold = suite.get("pass_threshold", 1.0)
            errors.append(f"pass_rate {suite_result.pass_rate:.3f} below threshold {threshold}")

        if args.baseline:
            baseline = _load_json(args.baseline)
            errors.extend(
                compare_to_baseline(
                    suite_result,
                    baseline,
                    regression_tolerance=args.regression_tolerance,
                )
            )

        if args.json:
            print(json.dumps(_suite_result_to_report(suite_result), indent=2))
        else:
            print(f"suite={suite_result.suite_id} pass_rate={suite_result.pass_rate:.3f}")

        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
