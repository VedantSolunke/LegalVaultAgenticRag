"""Legal concept lookup via in-memory hybrid retrieval (fixture corpus)."""


def test_legal_concept_lookup_retrieves_murder_section(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "Which BNS section covers murder?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "legal_concept_lookup"
    cited = {c["section_number"] for c in payload["citations"]}
    assert 101 in cited
    assert payload["confidence"] == "medium"
    assert "best-effort" in payload["body"].lower()


def test_robbery_phrasing_routes_to_legal_concept_not_meta(client, auth_headers) -> None:
    response = client.post(
        "/research",
        json={"query": "what is the bns section for robbery?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "legal_concept_lookup"
    assert payload["citations"]
    assert "general orientation only" not in payload["body"].lower()
