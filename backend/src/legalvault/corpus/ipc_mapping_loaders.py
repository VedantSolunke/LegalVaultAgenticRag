"""Load IPC→BNS mapping rows from curated Hugging Face CSV exports."""

from __future__ import annotations

import ast
import csv
import re
from collections import defaultdict
from pathlib import Path

from legalvault.models.mapping import MappingRecord, MappingSource

_BNS_SECTION_RE = re.compile(r"section\s*(\d+)", re.IGNORECASE)
_IPC_SECTION_RE = re.compile(r"S\.?\s*(\d+)", re.IGNORECASE)


def parse_bns_section_number(raw: str) -> int | None:
    cleaned = raw.strip()
    if not cleaned or "repealed" in cleaned.lower():
        return None
    match = re.match(r"^(\d+)", cleaned)
    if match:
        return int(match.group(1))
    section_match = _BNS_SECTION_RE.search(cleaned)
    if section_match:
        return int(section_match.group(1))
    return None


def _dedupe_ordered(values: list[int]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def load_jbp123_bns_csv(path: Path) -> list[MappingRecord]:
    """Parse jbp123/bns comparative table CSV into IPC-keyed mapping records."""
    ipc_to_bns: dict[int, set[int]] = defaultdict(set)
    ipc_meta: dict[int, tuple[str | None, str | None]] = {}

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 8:
                continue
            bns_raw = row[2].strip()
            title = row[5].strip() if len(row) > 5 else ""
            ipc_cell = row[7].strip()
            if not ipc_cell or ipc_cell in {"–*", "-*"}:
                continue
            bns_match = _BNS_SECTION_RE.search(bns_raw)
            if not bns_match:
                continue
            bns_number = int(bns_match.group(1))
            ipc_numbers = [int(m.group(1)) for m in _IPC_SECTION_RE.finditer(ipc_cell)]
            if not ipc_numbers:
                continue
            for ipc_number in ipc_numbers:
                ipc_to_bns[ipc_number].add(bns_number)
                if ipc_number not in ipc_meta:
                    ipc_meta[ipc_number] = (title or None, title or None)

    records: list[MappingRecord] = []
    for ipc_number in sorted(ipc_to_bns):
        bns_title, ipc_title = ipc_meta.get(ipc_number, (None, None))
        records.append(
            MappingRecord(
                ipc_section_number=ipc_number,
                bns_section_numbers=_dedupe_ordered(sorted(ipc_to_bns[ipc_number])),
                source="jbp123_bns",
                ipc_title=ipc_title,
                bns_title=bns_title,
            )
        )
    return records


def _parse_nandhakumarg_response(cell: str) -> dict[str, str]:
    try:
        parsed = ast.literal_eval(cell)
    except (SyntaxError, ValueError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): str(value) for key, value in parsed.items()}


def load_nandhakumarg_csv(path: Path) -> list[MappingRecord]:
    """Parse nandhakumarg/IPC_and_BNS_transformation CSV."""
    records: list[MappingRecord] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            payload = _parse_nandhakumarg_response(row.get("response", ""))
            ipc_raw = payload.get("IPC Section", "").strip()
            bns_raw = payload.get("BNS Section", "").strip()
            if not ipc_raw.isdigit():
                continue
            bns_number = parse_bns_section_number(bns_raw)
            if bns_number is None:
                continue
            records.append(
                MappingRecord(
                    ipc_section_number=int(ipc_raw),
                    bns_section_numbers=[bns_number],
                    source="nandhakumarg_ipc_bns_transformation",
                    ipc_title=payload.get("IPC Heading") or None,
                    bns_title=payload.get("BNS Heading") or None,
                )
            )
    return records


def merge_mapping_records(
    primary: list[MappingRecord],
    supplemental: list[MappingRecord],
) -> list[MappingRecord]:
    """Primary wins per IPC section; supplemental fills gaps only."""
    by_ipc: dict[int, MappingRecord] = {r.ipc_section_number: r for r in primary}
    for record in supplemental:
        if record.ipc_section_number not in by_ipc:
            by_ipc[record.ipc_section_number] = record
    return [by_ipc[key] for key in sorted(by_ipc)]


def load_merged_mapping_csvs(
    *,
    primary_csv: Path,
    supplemental_csv: Path | None = None,
) -> list[MappingRecord]:
    primary = load_jbp123_bns_csv(primary_csv)
    supplemental = (
        load_nandhakumarg_csv(supplemental_csv)
        if supplemental_csv is not None
        else []
    )
    return merge_mapping_records(primary, supplemental)
