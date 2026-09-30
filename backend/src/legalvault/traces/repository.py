from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json


@dataclass
class TraceStore:
    database_url: str

    @classmethod
    def connect(cls, database_url: str) -> TraceStore:
        return cls(database_url=database_url)

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def insert_trace(
        self,
        user_id: str,
        trace: dict[str, Any],
        *,
        session_id: UUID | None = None,
    ) -> UUID:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO request_traces (user_id, session_id, trace)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, session_id, Json(trace)),
                )
                row = cur.fetchone()
            conn.commit()
        return row["id"]

    def get_trace(self, trace_id: UUID) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT trace FROM request_traces WHERE id = %s
                    """,
                    (trace_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return row["trace"]
