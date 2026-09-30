from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from legalvault.models.research import ResearchResponse
from legalvault.models.sessions import ChatSession, SessionMessage
from legalvault.privacy.redaction import redact_message

MAX_CONTEXT_TURNS = 10


@dataclass
class SessionStore:
    database_url: str

    @classmethod
    def connect(cls, database_url: str) -> SessionStore:
        return cls(database_url=database_url)

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def create_session(self, user_id: str, *, title: str | None = None) -> ChatSession:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (user_id, title)
                    VALUES (%s, %s)
                    RETURNING id, user_id, title, created_at, updated_at
                    """,
                    (user_id, title),
                )
                row = cur.fetchone()
            conn.commit()
        return ChatSession.model_validate(row)

    def list_sessions(self, user_id: str) -> list[ChatSession]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM chat_sessions
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
        return [ChatSession.model_validate(row) for row in rows]

    def get_session_for_user(self, user_id: str, session_id: UUID) -> ChatSession | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM chat_sessions
                    WHERE id = %s AND user_id = %s
                    """,
                    (session_id, user_id),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return ChatSession.model_validate(row)

    def load_recent_messages(self, session_id: UUID, limit: int = MAX_CONTEXT_TURNS) -> list[SessionMessage]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, role, body, created_at
                    FROM (
                        SELECT id, session_id, role, body, created_at
                        FROM messages
                        WHERE session_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    ) recent
                    ORDER BY created_at ASC
                    """,
                    (session_id, limit),
                )
                rows = cur.fetchall()
        return [SessionMessage.model_validate(row) for row in rows]

    def append_message(
        self,
        session_id: UUID,
        *,
        role: str,
        live_body: str,
        research: ResearchResponse | None = None,
    ) -> SessionMessage:
        stored_body = redact_message(live_body)
        research_param: Json | None = None
        if research is not None:
            research_param = Json(research.model_dump(mode="json"))

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (session_id, role, body, research_response)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, session_id, role, body, created_at
                    """,
                    (session_id, role, stored_body, research_param),
                )
                row = cur.fetchone()
                cur.execute(
                    """
                    UPDATE chat_sessions
                    SET updated_at = now()
                    WHERE id = %s
                    """,
                    (session_id,),
                )
            conn.commit()
        return SessionMessage.model_validate(row)

    def get_message_bodies(self, session_id: UUID) -> list[tuple[str, str]]:
        messages = self.load_recent_messages(session_id, limit=MAX_CONTEXT_TURNS)
        return [(m.role, m.body) for m in messages]
