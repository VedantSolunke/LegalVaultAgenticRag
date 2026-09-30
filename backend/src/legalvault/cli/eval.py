"""CLI: run offline eval question set against in-process app or live API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from legalvault.eval.load_questions import (
    load_questions_json,
    load_questions_jsonl,
    merge_questions,
)
from legalvault.eval.runner import HttpResearchClient, run_eval, run_eval_in_process
from legalvault.eval.thresholds import DEFAULT_THRESHOLDS_PATH, load_thresholds

DEFAULT_QUESTIONS_PATH = Path(__file__).resolve().parents[3] / "eval" / "questions.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the offline eval question set (never indexed) and print "
            "citation/retrieval pass metrics."
        )
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_QUESTIONS_PATH,
        help="Handwritten eval questions JSON (default: backend/eval/questions.json)",
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        help="Optional QA JSONL path (questions only; never ingested)",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=DEFAULT_THRESHOLDS_PATH,
        help="Invite-gate threshold config JSON",
    )
    parser.add_argument(
        "--api-url",
        help="Run against a live API base URL instead of in-process fixture corpus",
    )
    parser.add_argument(
        "--token",
        default="test-user-token",
        help="Bearer token for API mode (default: test-user-token)",
    )
    parser.add_argument(
        "--check-invite-gate",
        action="store_true",
        help="Exit non-zero when ADR-0013 invite-gate thresholds are not met",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.questions.is_file():
        print(f"Missing questions file: {args.questions}", file=sys.stderr)
        return 1

    handwritten = load_questions_json(args.questions)
    jsonl_questions = (
        load_questions_jsonl(args.jsonl) if args.jsonl is not None else []
    )
    questions = merge_questions(handwritten, jsonl_questions)
    if not questions:
        print("No eval questions loaded", file=sys.stderr)
        return 1

    if args.api_url:
        client = HttpResearchClient(args.api_url, args.token)
        report = run_eval(client, questions)
    else:
        report = run_eval_in_process(questions, token=args.token)

    thresholds = load_thresholds(args.thresholds)
    gate = report.check_invite_gate(thresholds)

    payload = {
        "total": report.total,
        "passed": report.passed,
        "pass_rate": round(report.pass_rate, 4),
        "invite_gate": {
            "passed": gate.passed,
            "thresholds_file": str(args.thresholds),
            "failures": list(gate.failures),
        },
        "results": [
            {
                "id": result.question_id,
                "passed": result.passed,
                "query_mode": result.query_mode,
                "failure_reason": result.failure_reason,
                "metrics": result.metrics,
            }
            for result in report.results
        ],
    }
    print(json.dumps(payload, indent=2))

    if args.check_invite_gate and not gate.passed:
        return 2
    if report.passed != report.total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
