from __future__ import annotations

import psycopg

from legalvault.models.mapping import MappingRecord


def _row_to_mapping(row: tuple) -> MappingRecord:
    ipc_section_number, bns_section_numbers, mapping_source, ipc_title, bns_title = row
    return MappingRecord(
        ipc_section_number=ipc_section_number,
        bns_section_numbers=list(bns_section_numbers),
        source=mapping_source,
        ipc_title=ipc_title,
        bns_title=bns_title,
    )


class PostgresMappingStore:
    """Postgres-backed structured IPC mapping store (no vector index)."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn
        self._known_cache: frozenset[int] | None = None

    @classmethod
    def connect(cls, conninfo: str) -> PostgresMappingStore:
        return cls(psycopg.connect(conninfo))

    def close(self) -> None:
        self._conn.close()

    def lookup_by_ipc_numbers(self, numbers: list[int]) -> list[MappingRecord]:
        if not numbers:
            return []
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT ipc_section_number, bns_section_numbers, mapping_source,
                       ipc_title, bns_title
                FROM ipc_mappings
                WHERE ipc_section_number = ANY(%s)
                ORDER BY ipc_section_number
                """,
                (numbers,),
            )
            rows = cur.fetchall()
        by_ipc = {row[0]: _row_to_mapping(row) for row in rows}
        return [by_ipc[n] for n in numbers if n in by_ipc]

    def get_mapping(self, ipc_section_number: int) -> MappingRecord | None:
        results = self.lookup_by_ipc_numbers([ipc_section_number])
        return results[0] if results else None

    @property
    def known_ipc_sections(self) -> frozenset[int]:
        if self._known_cache is None:
            with self._conn.cursor() as cur:
                cur.execute("SELECT ipc_section_number FROM ipc_mappings")
                self._known_cache = frozenset(row[0] for row in cur.fetchall())
        return self._known_cache


def ingest_mapping_records(
    conn: psycopg.Connection, records: list[MappingRecord]
) -> int:
    written = 0
    with conn.cursor() as cur:
        for record in records:
            cur.execute(
                """
                INSERT INTO ipc_mappings (
                    ipc_section_number, bns_section_numbers, mapping_source,
                    ipc_title, bns_title
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ipc_section_number) DO UPDATE SET
                    bns_section_numbers = EXCLUDED.bns_section_numbers,
                    mapping_source = EXCLUDED.mapping_source,
                    ipc_title = EXCLUDED.ipc_title,
                    bns_title = EXCLUDED.bns_title
                """,
                (
                    record.ipc_section_number,
                    record.bns_section_numbers,
                    record.source,
                    record.ipc_title,
                    record.bns_title,
                ),
            )
            written += 1
    conn.commit()
    return written


def ingest_mapping_csv_files(
    conn: psycopg.Connection,
    *,
    primary_csv: str,
    supplemental_csv: str | None = None,
) -> int:
    from pathlib import Path

    from legalvault.corpus.ipc_mapping_loaders import load_merged_mapping_csvs

    records = load_merged_mapping_csvs(
        primary_csv=Path(primary_csv),
        supplemental_csv=Path(supplemental_csv) if supplemental_csv else None,
    )
    return ingest_mapping_records(conn, records)
