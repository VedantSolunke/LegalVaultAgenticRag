from __future__ import annotations

from pathlib import Path

import psycopg

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "sql" / "001_bns_sections.sql"


def apply_schema(conn: psycopg.Connection) -> None:
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
