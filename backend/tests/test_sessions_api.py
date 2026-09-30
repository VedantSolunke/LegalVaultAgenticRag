"""API tests for chat sessions, persistence, redaction, and isolation."""

import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from legalvault.db.schema import apply_schema
from legalvault.main import create_app

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


pytestmark = pytest.mark.skipif(
    not _postgres_available(_database_url()),
    reason="Postgres test database not available",
)


@pytest.fixture
def session_client(monkeypatch) -> TestClient:
    url = _database_url()
    monkeypatch.setenv("LEGALVAULT_DATABASE_URL", url)
    get_settings = __import__("legalvault.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with psycopg.connect(url) as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE messages, chat_sessions RESTART IDENTITY CASCADE")
        conn.commit()

    app = create_app()
    client = TestClient(app)
    yield client
    get_settings.cache_clear()


@pytest.fixture
def auth_headers_user_b() -> dict[str, str]:
    return {"Authorization": "Bearer test-user-b-token"}


def test_sessions_require_authentication(session_client: TestClient) -> None:
    response = session_client.post("/sessions")
    assert response.status_code == 401


def test_session_messages_require_authentication(session_client: TestClient) -> None:
    response = session_client.post(
        "/sessions/00000000-0000-0000-0000-000000000001/messages",
        json={"query": "What is BNS section 101?"},
    )
    assert response.status_code == 401


def test_create_session_post_message_persists_research_response(
    session_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = session_client.post("/sessions", headers=auth_headers)
    assert created.status_code == 200
    session_id = created.json()["session"]["id"]

    response = session_client.post(
        f"/sessions/{session_id}/messages",
        json={"query": "What is BNS section 101?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["research"]["query_mode"] == "section_lookup"
    assert payload["message"]["role"] == "user"

    with psycopg.connect(_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = %s",
                (session_id,),
            )
            count = cur.fetchone()[0]
    assert count == 2


def test_stored_user_message_redacts_obvious_pii(
    session_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = session_client.post("/sessions", headers=auth_headers)
    session_id = created.json()["session"]["id"]

    session_client.post(
        f"/sessions/{session_id}/messages",
        json={"query": "Reach me at witness@example.com about BNS section 101"},
        headers=auth_headers,
    )

    with psycopg.connect(_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT body FROM messages
                WHERE session_id = %s AND role = 'user'
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (session_id,),
            )
            body = cur.fetchone()[0]

    assert "[REDACTED_EMAIL]" in body
    assert "witness@example.com" not in body


def test_session_isolation_returns_not_found_for_other_user(
    session_client: TestClient,
    auth_headers: dict[str, str],
    auth_headers_user_b: dict[str, str],
) -> None:
    created = session_client.post("/sessions", headers=auth_headers)
    session_id = created.json()["session"]["id"]

    response = session_client.post(
        f"/sessions/{session_id}/messages",
        json={"query": "What is BNS section 101?"},
        headers=auth_headers_user_b,
    )
    assert response.status_code == 404


def test_follow_up_in_session_can_reference_prior_section(
    session_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = session_client.post("/sessions", headers=auth_headers)
    session_id = created.json()["session"]["id"]

    first = session_client.post(
        f"/sessions/{session_id}/messages",
        json={"query": "What is BNS section 101?"},
        headers=auth_headers,
    )
    assert first.status_code == 200
    assert any(c["section_number"] == 101 for c in first.json()["research"]["citations"])

    follow_up = session_client.post(
        f"/sessions/{session_id}/messages",
        json={"query": "How does the murder section compare to section 103?"},
        headers=auth_headers,
    )
    assert follow_up.status_code == 200
    cited = {c["section_number"] for c in follow_up.json()["research"]["citations"]}
    assert 101 in cited or 103 in cited
    assert 103 in cited
