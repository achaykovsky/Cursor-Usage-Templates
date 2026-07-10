#!/usr/bin/env python3
"""LLM-judge calibration — agreement metrics and threshold recommendations.

CLI:
  python llm_judge_calibration.py validate <calibration.json>
  python llm_judge_calibration.py analyze <calibration.json> [--threshold 0.8] [--json]
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

_CALIBRATION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


@dataclass(frozen=True)
class CalibrationMetrics:
    calibration_id: str
    sample_count: int
    labeled_count: int
    agreement_rate: float
    precision: float
    recall: float
    recommended_threshold: float
    false_positives: int
    false_negatives: int


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def validate_judge_calibration(data: Any, *, path: str = "<judge-calibration>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: root must be an object"]

    for key in ("schema_version", "calibration_id", "judge_model", "rubric", "samples"):
        if key not in data:
            errors.append(f"{path}: missing required field '{key}'")

    schema_version = data.get("schema_version")
    if schema_version is not None and (not isinstance(schema_version, int) or schema_version < 1):
        errors.append(f"{path}: schema_version must be integer >= 1")

    calibration_id = data.get("calibration_id")
    if calibration_id is not None and (
        not isinstance(calibration_id, str) or not _CALIBRATION_ID_RE.match(calibration_id)
    ):
        errors.append(f"{path}: calibration_id invalid")

    judge_model = data.get("judge_model")
    if judge_model is not None and (not isinstance(judge_model, str) or not judge_model or len(judge_model) > 128):
        errors.append(f"{path}: judge_model invalid")

    rubric = data.get("rubric")
    if rubric is not None and (not isinstance(rubric, str) or not rubric or len(rubric) > 2048):
        errors.append(f"{path}: rubric invalid")

    recommended = data.get("recommended_min_score")
    if recommended is not None and (
        isinstance(recommended, bool)
        or not isinstance(recommended, (int, float))
        or recommended < 0
        or recommended > 1
    ):
        errors.append(f"{path}: recommended_min_score must be number between 0 and 1")

    samples = data.get("samples")
    if isinstance(samples, list):
        if len(samples) < 3:
            errors.append(f"{path}: samples must have at least 3 items")
        for idx, row in enumerate(samples):
            if not isinstance(row, dict):
                errors.append(f"{path}: samples[{idx}] must be an object")
                continue
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id or len(row_id) > 64:
                errors.append(f"{path}: samples[{idx}].id invalid")
            response = row.get("response")
            if not isinstance(response, str) or not response or len(response) > 8192:
                errors.append(f"{path}: samples[{idx}].response invalid")
            if "human_pass" not in row or not isinstance(row.get("human_pass"), bool):
                errors.append(f"{path}: samples[{idx}].human_pass must be boolean")
            judge_score = row.get("judge_score")
            if judge_score is not None and (
                isinstance(judge_score, bool)
                or not isinstance(judge_score, (int, float))
                or judge_score < 0
                or judge_score > 1
            ):
                errors.append(f"{path}: samples[{idx}].judge_score invalid")
            notes = row.get("notes")
            if notes is not None and (not isinstance(notes, str) or len(notes) > 512):
                errors.append(f"{path}: samples[{idx}].notes invalid")
    elif samples is not None:
        errors.append(f"{path}: samples must be an array")

    return errors


def _predict_pass(judge_score: float, threshold: float) -> bool:
    return judge_score >= threshold


def compute_metrics(data: dict[str, Any], *, threshold: float) -> CalibrationMetrics:
    samples = [s for s in data.get("samples", []) if isinstance(s, dict)]
    labeled = [s for s in samples if isinstance(s.get("judge_score"), (int, float)) and not isinstance(s.get("judge_score"), bool)]

    tp = fp = tn = fn = 0
    for row in labeled:
        human = bool(row.get("human_pass"))
        predicted = _predict_pass(float(row["judge_score"]), threshold)
        if human and predicted:
            tp += 1
        elif not human and predicted:
            fp += 1
        elif human and not predicted:
            fn += 1
        else:
            tn += 1

    labeled_count = len(labeled)
    agreement = (tp + tn) / labeled_count if labeled_count else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return CalibrationMetrics(
        calibration_id=str(data.get("calibration_id", "<unknown>")),
        sample_count=len(samples),
        labeled_count=labeled_count,
        agreement_rate=agreement,
        precision=precision,
        recall=recall,
        recommended_threshold=threshold,
        false_positives=fp,
        false_negatives=fn,
    )


def recommend_threshold(data: dict[str, Any]) -> float:
    """Pick threshold maximizing agreement on labeled samples (0.05 step scan)."""
    samples = [
        s
        for s in data.get("samples", [])
        if isinstance(s, dict) and isinstance(s.get("judge_score"), (int, float)) and not isinstance(s.get("judge_score"), bool)
    ]
    if not samples:
        existing = data.get("recommended_min_score")
        if isinstance(existing, (int, float)) and not isinstance(existing, bool):
            return float(existing)
        return 0.8

    best_threshold = 0.8
    best_agreement = -1.0
    for step in range(0, 21):
        threshold = step / 20.0
        metrics = compute_metrics(data, threshold=threshold)
        if metrics.agreement_rate > best_agreement:
            best_agreement = metrics.agreement_rate
            best_threshold = threshold
    return best_threshold


def analyze_calibration(data: dict[str, Any], *, threshold: float | None = None) -> CalibrationMetrics:
    chosen = threshold if threshold is not None else recommend_threshold(data)
    metrics = compute_metrics(data, threshold=chosen)
    logger.info(
        "analyze_calibration_complete",
        extra={
            "calibration_id": metrics.calibration_id,
            "agreement_rate": metrics.agreement_rate,
            "threshold": chosen,
        },
    )
    return metrics


def metrics_to_dict(metrics: CalibrationMetrics) -> dict[str, Any]:
    return {
        "calibration_id": metrics.calibration_id,
        "sample_count": metrics.sample_count,
        "labeled_count": metrics.labeled_count,
        "agreement_rate": round(metrics.agreement_rate, 4),
        "precision": round(metrics.precision, 4),
        "recall": round(metrics.recall, 4),
        "recommended_threshold": metrics.recommended_threshold,
        "false_positives": metrics.false_positives,
        "false_negatives": metrics.false_negatives,
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="LLM judge calibration utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate", help="Validate calibration fixture schema")
    validate_p.add_argument("path", type=Path)

    analyze_p = sub.add_parser("analyze", help="Compute agreement metrics and threshold recommendation")
    analyze_p.add_argument("path", type=Path)
    analyze_p.add_argument("--threshold", type=float, default=None)
    analyze_p.add_argument("--json", action="store_true")
    analyze_p.add_argument("--min-agreement", type=float, default=0.8, help="Fail if agreement below this")

    args = parser.parse_args(argv)

    if args.command == "validate":
        data = _load_json(args.path)
        errors = validate_judge_calibration(data, path=str(args.path))
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print(f"ok: {args.path}")
        return 0

    if args.command == "analyze":
        data = _load_json(args.path)
        errors = validate_judge_calibration(data, path=str(args.path))
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1

        threshold = args.threshold if args.threshold is not None else recommend_threshold(data)
        metrics = analyze_calibration(data, threshold=threshold)

        if args.json:
            print(json.dumps(metrics_to_dict(metrics), indent=2))
        else:
            print(
                f"calibration={metrics.calibration_id} agreement={metrics.agreement_rate:.3f} "
                f"threshold={metrics.recommended_threshold:.2f} fp={metrics.false_positives} fn={metrics.false_negatives}"
            )

        if metrics.labeled_count < 3:
            print("warning: fewer than 3 labeled judge_score samples", file=sys.stderr)
        if metrics.agreement_rate < args.min_agreement:
            print(
                f"agreement {metrics.agreement_rate:.3f} below min {args.min_agreement}",
                file=sys.stderr,
            )
            return 1
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
