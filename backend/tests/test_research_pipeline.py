"""Issue #6: modes, verification, traces, guardrails."""

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


postgres_required = pytest.mark.skipif(
    not _postgres_available(_database_url()),
    reason="Postgres test database not available",
)


def test_out_of_corpus_bnss_refusal(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "What does BNSS say about bail procedures?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "out_of_corpus"
    assert payload["citations"] == []
    assert "out of corpus" in payload["lead"].lower() or "outside" in payload["lead"].lower()
    assert "bnss" in payload["body"].lower()


def test_out_of_corpus_bsa_refusal(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "Under BSA 2023, what is admissible electronic evidence?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "out_of_corpus"
    assert payload["citations"] == []


def test_fact_pattern_returns_sections_with_uncertainty_when_thin(
    client, auth_headers
) -> None:
    response = client.post(
        "/research",
        json={"query": "Someone hurt me. What BNS sections could apply?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "fact_pattern_analysis"
    assert payload["confidence"] in ("low", "medium")
    assert "uncertain" in payload["body"].lower() or "insufficient" in payload["body"].lower()


def test_fact_pattern_with_rich_facts_can_be_high_confidence(
    client, auth_headers
) -> None:
    response = client.post(
        "/research",
        json={
            "query": (
                "A person threatened me repeatedly, damaged my property, "
                "and then assaulted me. Which BNS sections could apply?"
            )
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "fact_pattern_analysis"
    assert len(payload["citations"]) >= 1


def test_section_comparison_mode(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={
            "query": "What is the difference between BNS section 101 and section 103?"
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "section_comparison"
    cited = {c["section_number"] for c in payload["citations"]}
    assert 101 in cited and 103 in cited


@postgres_required
def test_trace_persisted_and_admin_only_fetch(monkeypatch) -> None:
    url = _database_url()
    monkeypatch.setenv("LEGALVAULT_DATABASE_URL", url)
    get_settings = __import__("legalvault.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with psycopg.connect(url) as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE request_traces, messages, chat_sessions, profiles "
                "RESTART IDENTITY CASCADE"
            )
            cur.execute(
                "INSERT INTO profiles (user_id, is_admin) VALUES (%s, %s), (%s, %s)",
                ("test-user", False, "test-admin", True),
            )
        conn.commit()

    client = TestClient(create_app())
    research = client.post(
        "/research",
        json={"query": "What does BNSS say about arrest?"},
        headers={"Authorization": "Bearer test-user-token"},
    )
    assert research.status_code == 200
    trace_id = research.json()["trace_id"]
    assert trace_id is not None

    denied = client.get(
        f"/traces/{trace_id}",
        headers={"Authorization": "Bearer test-user-token"},
    )
    assert denied.status_code == 403

    allowed = client.get(
        f"/traces/{trace_id}",
        headers={"Authorization": "Bearer test-admin-token"},
    )
    assert allowed.status_code == 200
    trace = allowed.json()
    assert trace["query_mode"] == "out_of_corpus"
    assert "retrieval_snapshot" in trace
    assert trace["verification_outcome"]
    assert trace["latency_ms"] >= 0

    get_settings.cache_clear()


@postgres_required
def test_trace_rls_denies_standard_user_direct_select(monkeypatch) -> None:
    url = _database_url()
    with psycopg.connect(url) as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM pg_policies WHERE tablename = 'request_traces'"
            )
            if cur.fetchone()[0] == 0:
                pytest.skip("request_traces RLS policies require Supabase auth schema")

    url = _database_url()
    monkeypatch.setenv("LEGALVAULT_DATABASE_URL", url)
    get_settings = __import__("legalvault.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    with psycopg.connect(url) as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE request_traces, messages, chat_sessions, profiles "
                "RESTART IDENTITY CASCADE"
            )
            cur.execute(
                "INSERT INTO profiles (user_id, is_admin) VALUES (%s, %s)",
                ("test-user", False),
            )
            cur.execute(
                """
                INSERT INTO request_traces (user_id, trace)
                VALUES ('test-user', '{"query_mode": "section_lookup"}'::jsonb)
                RETURNING id
                """
            )
            trace_id = cur.fetchone()[0]
        conn.commit()

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL role TO authenticated")
            cur.execute("SET LOCAL request.jwt.claim.sub TO 'test-user'")
            cur.execute("SELECT COUNT(*) FROM request_traces WHERE id = %s", (trace_id,))
            count = cur.fetchone()[0]

    assert count == 0
    get_settings.cache_clear()


def test_research_without_database_has_no_trace_id(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "What is BNS section 101?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json().get("trace_id") is None
