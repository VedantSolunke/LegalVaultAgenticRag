"""Operator CLI: ingest IPC→BNS mapping CSVs into Postgres (structured lookup)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg

from legalvault.config import get_settings
from legalvault.corpus.postgres_mapping import ingest_mapping_csv_files
from legalvault.db.schema import apply_schema


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
    if primary_csv is None:
        print(
            "Missing --primary-csv or LEGALVAULT_IPC_MAPPING_PRIMARY_CSV",
            file=sys.stderr,
        )
        return 1
    if database_url is None:
        print("Missing --database-url or LEGALVAULT_DATABASE_URL", file=sys.stderr)
        return 1

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
