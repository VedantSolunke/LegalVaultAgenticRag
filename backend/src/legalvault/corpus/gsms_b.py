"""Load BNS section records from GSMS-B structured JSON (eval QA corpora excluded)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from legalvault.models.research import SectionRecord

_BLOCKED_PATH_MARKERS = (
    "indian-legal-qa",
    "legal-qa",
    "qa.jsonl",
    ".jsonl",
)


def assert_ingestible_bns_json_path(path: Path) -> None:
    """Refuse paths that look like the eval-only QA JSONL corpus (ADR-0003)."""
    normalized = str(path).lower()
    for marker in _BLOCKED_PATH_MARKERS:
        if marker in normalized:
            raise ValueError(
                f"Refusing to ingest {path}: QA or JSONL eval corpora must not be embedded."
            )
    if path.suffix.lower() == ".jsonl":
        raise ValueError(
            f"Refusing to ingest {path}: expected GSMS-B BNS sections JSON, not JSONL."
        )


def _normalize_act(raw: str) -> str:
    if raw.upper().startswith("BNS"):
        return "BNS"
    return raw


def _parse_section_number(raw: str | int) -> int:
    if isinstance(raw, int):
        return raw
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValueError(f"Invalid section_number: {raw!r}")
    return int(digits)


def section_record_from_gsms_row(row: dict[str, object]) -> SectionRecord:
    section_number = _parse_section_number(row["section_number"])  # type: ignore[arg-type]
    title = str(row.get("section_title") or row.get("title") or "").strip()
    chapter = str(row.get("chapter") or "").strip()
    text = str(row.get("text") or "").strip()
    act = _normalize_act(str(row.get("act") or "BNS"))
    if not title or not text:
        raise ValueError(f"Incomplete GSMS-B row for section {section_number}")
    return SectionRecord(
        section_number=section_number,
        title=title,
        chapter=chapter,
        text=text,
        act=act,
        chunk_id=str(row.get("chunk_id") or f"BNS_{section_number}"),
    )


def load_bns_sections_json(path: Path) -> list[SectionRecord]:
    assert_ingestible_bns_json_path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected JSON array in {path}")
    records: list[SectionRecord] = []
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError(f"Expected object rows in {path}")
        act = str(row.get("act") or "").upper()
        if act and not act.startswith("BNS"):
            continue
        records.append(section_record_from_gsms_row(row))
    return records
