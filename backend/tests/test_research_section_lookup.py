"""API integration tests for BNS section lookup (fixture corpus, stub providers)."""

from legalvault.corpus.fixture import FIXTURE_SECTION_NUMBERS


def test_research_requires_authentication(client) -> None:
    response = client.post("/research", json={"query": "What is BNS section 101?"})
    assert response.status_code == 401


def test_section_lookup_returns_title_excerpt_and_citation(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "What is BNS section 101?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["query_mode"] == "section_lookup"
    assert len(payload["citations"]) >= 1

    citation = next(c for c in payload["citations"] if c["section_number"] == 101)
    assert citation["title"]
    assert citation["excerpt"]
    assert citation["act"] == "BNS"
    assert "101" in payload["lead"] or "101" in payload["body"]


def test_bns_section_phrase_resolves_without_live_llm(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "BNS section 103"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["query_mode"] == "section_lookup"
    section_numbers = {c["section_number"] for c in payload["citations"]}
    assert 103 in section_numbers


def test_citations_only_reference_fixture_corpus(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "Tell me about BNS 101 and also section 99999"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    cited = {c["section_number"] for c in response.json()["citations"]}
    assert cited.issubset(set(FIXTURE_SECTION_NUMBERS))
    assert 99999 not in cited
