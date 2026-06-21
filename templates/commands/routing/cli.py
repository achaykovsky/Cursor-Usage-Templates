"""CLI entry for deterministic Cursor routing commands."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from routing.model import route_model
from routing.predict import match_skills_from_prompt, predict_prompt_context
from routing.routers import route_agent, route_session, route_skill
from routing.rules import match_rules_from_prompt, route_rules

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic Cursor routing CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    session_p = sub.add_parser("session", help="Session route map")
    session_p.add_argument("--task", required=True)
    session_p.add_argument("--files", nargs="*", default=[])

    agent_p = sub.add_parser("agent", help="Agent routing")
    agent_p.add_argument("--task", required=True)

    skill_p = sub.add_parser("skill", help="Skill routing")
    skill_p.add_argument("--task", required=True)
    skill_p.add_argument("--phase", default="")

    model_p = sub.add_parser("model", help="Model routing")
    model_p.add_argument("--task", required=True)

    rules_p = sub.add_parser("rules", help="Rules audit for paths")
    rules_p.add_argument("--files", nargs="*", default=[])

    skills_match_p = sub.add_parser("skills-match", help="Match skills from prompt keywords (JSON array)")
    skills_match_p.add_argument("--task", required=True)
    skills_match_p.add_argument("--min-score", type=int, default=1)

    rules_match_p = sub.add_parser("rules-match", help="Match rules from prompt keywords (JSON array)")
    rules_match_p.add_argument("--task", required=True)
    rules_match_p.add_argument("--min-score", type=int, default=1)

    predict_p = sub.add_parser("predict", help="Predict skills and rules from prompt (JSON object)")
    predict_p.add_argument("--task", required=True)
    predict_p.add_argument("--min-score", type=int, default=1)

    return parser


def main(argv: list[str] | None = None) -> int:
    logger.info("main_enter", extra={"argv_length": len(argv) if argv is not None else 0})
    parser = build_parser()
    args = parser.parse_args(argv)
    logger.info("main_command", extra={"command": args.command})

    if args.command == "session":
        sys.stdout.write(route_session(args.task, args.files) + "\n")
    elif args.command == "agent":
        sys.stdout.write(route_agent(args.task) + "\n")
    elif args.command == "skill":
        sys.stdout.write(route_skill(args.task, args.phase) + "\n")
    elif args.command == "model":
        sys.stdout.write(route_model(args.task) + "\n")
    elif args.command == "rules":
        sys.stdout.write(route_rules(args.files) + "\n")
    elif args.command == "skills-match":
        sys.stdout.write(json.dumps(match_skills_from_prompt(args.task, args.min_score)) + "\n")
    elif args.command == "rules-match":
        sys.stdout.write(json.dumps(match_rules_from_prompt(args.task, args.min_score)) + "\n")
    elif args.command == "predict":
        sys.stdout.write(json.dumps(predict_prompt_context(args.task, args.min_score)) + "\n")
    else:
        parser.error(f"unknown command: {args.command}")
        return 2
    logger.info("main_exit", extra={"command": args.command, "exit_code": 0})
    return 0


def run_cli() -> None:
    """Configure logging and exit with ``main()`` status (script and ``python -m routing`` entry)."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
