"""Operator CLI: ingest GSMS-B BNS JSON into Postgres with embeddings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg

from legalvault.config import get_settings
from legalvault.corpus.postgres import ingest_bns_json_file
from legalvault.db.schema import apply_schema
from legalvault.providers.embeddings import StubEmbeddingProvider


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest GSMS-B bns_sections.json into Postgres (pgvector)."
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        help="Path to GSMS-B bns_sections.json (default: LEGALVAULT_BNS_SECTIONS_JSON_PATH)",
    )
    parser.add_argument(
        "--database-url",
        help="Postgres URL (default: LEGALVAULT_DATABASE_URL)",
    )
    parser.add_argument(
        "--apply-schema",
        action="store_true",
        help="Apply sql/001_bns_sections.sql before ingest",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = get_settings()
    json_path = args.json_path or settings.bns_sections_json_path
    database_url = args.database_url or settings.database_url
    if json_path is None:
        print("Missing --json-path or LEGALVAULT_BNS_SECTIONS_JSON_PATH", file=sys.stderr)
        return 1
    if database_url is None:
        print("Missing --database-url or LEGALVAULT_DATABASE_URL", file=sys.stderr)
        return 1

    embedder = StubEmbeddingProvider()
    with psycopg.connect(database_url) as conn:
        if args.apply_schema:
            apply_schema(conn)
        count = ingest_bns_json_file(conn, str(json_path), embedder=embedder)
    print(f"Ingested {count} BNS section records from {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
