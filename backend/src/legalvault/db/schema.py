from __future__ import annotations

from pathlib import Path

import psycopg

_SQL_DIR = Path(__file__).resolve().parents[3] / "sql"
_SCHEMA_FILES = (
    _SQL_DIR / "001_bns_sections.sql",
    _SQL_DIR / "002_ipc_mappings.sql",
)


def apply_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        for path in _SCHEMA_FILES:
            cur.execute(path.read_text(encoding="utf-8"))
    conn.commit()
