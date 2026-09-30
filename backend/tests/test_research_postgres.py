"""API integration tests against Postgres + pgvector (sample GSMS-B ingest)."""

import os
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from legalvault.api.research import _corpus_dependency
from legalvault.corpus.postgres import PostgresSectionCorpus, ingest_bns_json_file
from legalvault.db.schema import apply_schema
from legalvault.main import create_app
from legalvault.providers.embeddings import StubEmbeddingProvider

FIXTURE_JSON = Path(__file__).parent / "fixtures" / "bns_sections_sample.json"
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
def postgres_corpus() -> PostgresSectionCorpus:
    url = _database_url()
    with psycopg.connect(url) as conn:
        apply_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE bns_sections")
        conn.commit()
        ingest_bns_json_file(
            conn,
            str(FIXTURE_JSON),
            embedder=StubEmbeddingProvider(),
        )
    corpus = PostgresSectionCorpus.connect(url)
    yield corpus
    corpus.close()


@pytest.fixture
def postgres_client(postgres_corpus: PostgresSectionCorpus) -> TestClient:
    app = create_app()
    app.dependency_overrides[_corpus_dependency] = lambda: postgres_corpus
    return TestClient(app)


def test_postgres_section_lookup_returns_ingested_citation(
    postgres_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = postgres_client.post(
        "/research",
        json={"query": "What is BNS section 101?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "section_lookup"
    citation = next(c for c in payload["citations"] if c["section_number"] == 101)
    assert citation["title"] == "Murder"
    assert citation["act"] == "BNS"
    assert citation["excerpt"]


def test_postgres_legal_concept_lookup_uses_hybrid_retrieval(
    postgres_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = postgres_client.post(
        "/research",
        json={"query": "statutory provision for murder under BNS"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "legal_concept_lookup"
    cited = {c["section_number"] for c in payload["citations"]}
    assert 101 in cited
