"""TTL purge for stale chat sessions (ADR-0008)."""

import os
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from legalvault.db.schema import apply_schema
from legalvault.sessions.purge import purge_stale_sessions

DEFAULT_TEST_DATABASE_URL = (
    "postgresql://postgres:postgres@localhost:5432/legalvault_test"
)


def _database_url() -> str:
    return os.environ.get("LEGALVAULT_TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


def _postgres_available(url: str) -> bool:
    try:
        with psycopg.connect(url, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False


postgres_required = pytest.mark.skipif(
    not _postgres_available(_database_url()),
    reason="Postgres test database not available",
)


@postgres_required
def test_purge_removes_sessions_older_than_ttl() -> None:
    url = _database_url()
    with psycopg.connect(url) as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE messages, chat_sessions RESTART IDENTITY CASCADE"
            )
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, title, updated_at)
                VALUES ('u1', 'stale', %s)
                RETURNING id
                """,
                (datetime.now(timezone.utc) - timedelta(days=40),),
            )
            stale_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, title, updated_at)
                VALUES ('u1', 'fresh', now())
                RETURNING id
                """
            )
            fresh_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO messages (session_id, role, body)
                VALUES (%s, 'user', 'hello')
                """,
                (stale_id,),
            )
        conn.commit()

    deleted = purge_stale_sessions(url, ttl_days=30, dry_run=False)
    assert deleted == 1

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM chat_sessions ORDER BY title")
            remaining = {str(row[0]) for row in cur.fetchall()}
    assert str(fresh_id) in remaining
    assert str(stale_id) not in remaining
