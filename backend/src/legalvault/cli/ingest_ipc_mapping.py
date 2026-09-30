"""Operator CLI: ingest IPC→BNS mapping CSVs into Postgres (structured lookup)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg

from legalvault.config import get_settings
from legalvault.corpus.postgres_mapping import ingest_mapping_csv_files
from legalvault.db.schema import apply_schema

_HF_PRIMARY_URL = (
    "https://huggingface.co/datasets/jbp123/bns/resolve/main/"
    "Comparative%20Table%20of%20IPC%20and%20Bharatiya%20Nyaya%20Sanhita.csv"
)
_HF_SUPPLEMENTAL_URL = (
    "https://huggingface.co/datasets/nandhakumarg/IPC_and_BNS_transformation/"
    "resolve/main/IPC%20and%20BNS%20transformation%20.csv"
)
_PRIMARY_FILENAME = "jbp123_comparative_table.csv"
_SUPPLEMENTAL_FILENAME = "nandhakumarg_ipc_bns_transformation.csv"


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[3]


def _repo_root() -> Path:
    return _backend_dir().parent


def _standard_mapping_paths(filename: str) -> tuple[Path, ...]:
    backend = _backend_dir()
    repo = _repo_root()
    return (
        repo / "datasets" / "ipc-mapping" / filename,
        backend / "datasets" / "ipc-mapping" / filename,
    )


def _resolve_existing_csv(
    path: Path | None,
    *,
    label: str,
    standard_filename: str,
    required: bool,
) -> Path | None:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(path.expanduser())
    candidates.extend(_standard_mapping_paths(standard_filename))

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved

    if not required:
        return None

    tried = "\n".join(f"  - {p.resolve()}" for p in seen)
    print(f"{label} not found. Tried:\n{tried}", file=sys.stderr)
    print(
        "Download from the repo root (so paths match the README), or pass an "
        "explicit --primary-csv / --supplemental-csv.",
        file=sys.stderr,
    )
    if label.startswith("Primary"):
        print(
            f"From repo root:\n  curl -L '{_HF_PRIMARY_URL}' "
            f"-o datasets/ipc-mapping/{_PRIMARY_FILENAME}",
            file=sys.stderr,
        )
    elif label.startswith("Supplemental"):
        print(
            f"From repo root:\n  curl -L '{_HF_SUPPLEMENTAL_URL}' "
            f"-o datasets/ipc-mapping/{_SUPPLEMENTAL_FILENAME}",
            file=sys.stderr,
        )
    raise SystemExit(1)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest jbp123/bns (primary) and optional nandhakumarg supplemental "
            "IPC mapping CSVs into Postgres."
        )
    )
    parser.add_argument(
        "--primary-csv",
        type=Path,
        help="Path to jbp123/bns comparative table CSV",
    )
    parser.add_argument(
        "--supplemental-csv",
        type=Path,
        help="Optional nandhakumarg IPC_and_BNS_transformation CSV",
    )
    parser.add_argument(
        "--database-url",
        help="Postgres URL (default: LEGALVAULT_DATABASE_URL)",
    )
    parser.add_argument(
        "--apply-schema",
        action="store_true",
        help="Apply sql/*.sql before ingest",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = get_settings()
    primary_csv = args.primary_csv or settings.ipc_mapping_primary_csv
    supplemental_csv = args.supplemental_csv or settings.ipc_mapping_supplemental_csv
    database_url = args.database_url or settings.database_url
    if database_url is None:
        print("Missing --database-url or LEGALVAULT_DATABASE_URL", file=sys.stderr)
        return 1

    primary_resolved = _resolve_existing_csv(
        Path(primary_csv) if primary_csv is not None else None,
        label="Primary CSV (jbp123/bns)",
        standard_filename=_PRIMARY_FILENAME,
        required=True,
    )
    assert primary_resolved is not None
    primary_csv = primary_resolved

    supplemental_resolved = _resolve_existing_csv(
        Path(supplemental_csv) if supplemental_csv is not None else None,
        label="Supplemental CSV (nandhakumarg)",
        standard_filename=_SUPPLEMENTAL_FILENAME,
        required=supplemental_csv is not None,
    )
    supplemental_csv = supplemental_resolved

    with psycopg.connect(database_url) as conn:
        if args.apply_schema:
            apply_schema(conn)
        count = ingest_mapping_csv_files(
            conn,
            primary_csv=str(primary_csv),
            supplemental_csv=str(supplemental_csv) if supplemental_csv else None,
        )
    print(f"Ingested {count} IPC mapping records from {primary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
