from __future__ import annotations

import json
from pathlib import Path

from legalvault.eval.models import EvalQuestion


def _question_from_dict(raw: dict[str, object], *, source: str) -> EvalQuestion:
    expect = raw.get("expect")
    expect_dict = expect if isinstance(expect, dict) else {}

    required_sections = expect_dict.get("required_section_numbers") or raw.get(
        "required_section_numbers"
    )
    required_ipc = expect_dict.get("required_ipc_section_numbers") or raw.get(
        "required_ipc_section_numbers"
    )

    def _int_tuple(value: object) -> tuple[int, ...]:
        if value is None:
            return ()
        if not isinstance(value, list):
            raise ValueError("expected list of section numbers")
        return tuple(int(item) for item in value)

    question_id = str(raw.get("id") or raw.get("question_id") or "")
    query = str(raw.get("query") or raw.get("question") or "")
    if not question_id or not query:
        raise ValueError("eval question requires id and query")

    return EvalQuestion(
        id=question_id,
        query=query,
        expect_query_mode=(
            str(expect_dict["query_mode"])
            if expect_dict.get("query_mode") is not None
            else None
        ),
        min_citations=(
            int(expect_dict["min_citations"])
            if expect_dict.get("min_citations") is not None
            else None
        ),
        max_citations=(
            int(expect_dict["max_citations"])
            if expect_dict.get("max_citations") is not None
            else None
        ),
        required_section_numbers=_int_tuple(required_sections),
        required_ipc_section_numbers=_int_tuple(required_ipc),
        min_confidence=(
            str(expect_dict["min_confidence"])
            if expect_dict.get("min_confidence") is not None
            else None
        ),
        source=source,
    )


def load_questions_json(path: Path) -> list[EvalQuestion]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected JSON array in {path}")
    return [
        _question_from_dict(item, source="handwritten")
        for item in raw
        if isinstance(item, dict)
    ]


def load_questions_jsonl(path: Path, *, id_prefix: str = "qa") -> list[EvalQuestion]:
    questions: list[EvalQuestion] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        row = json.loads(stripped)
        if not isinstance(row, dict):
            raise ValueError(f"Expected JSON object on line {line_number} in {path}")
        question_id = str(row.get("id") or f"{id_prefix}-{line_number}")
        row = {**row, "id": question_id}
        questions.append(_question_from_dict(row, source="qa_jsonl"))
    return questions


def merge_questions(*groups: list[EvalQuestion]) -> list[EvalQuestion]:
    seen: set[str] = set()
    merged: list[EvalQuestion] = []
    for group in groups:
        for question in group:
            if question.id in seen:
                continue
            seen.add(question.id)
            merged.append(question)
    return merged
