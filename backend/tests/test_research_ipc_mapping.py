"""API integration tests for IPC-to-BNS mapping query mode (fixture mapping store)."""

from legalvault.corpus.mapping_fixture import FIXTURE_IPC_SECTIONS


def test_research_ipc_mapping_requires_authentication(client) -> None:
    response = client.post(
        "/research", json={"query": "What happened to IPC section 302?"}
    )
    assert response.status_code == 401


def test_ipc_mapping_returns_bns_targets_from_fixture_not_invented(
    client, auth_headers
) -> None:
    response = client.post(
        "/research",
        json={"query": "What happened to IPC section 302?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["query_mode"] == "ipc_to_bns_mapping"
    assert payload["confidence"] == "high"

    bns_citations = [
        c for c in payload["citations"] if c["act"] == "BNS"
    ]
    assert bns_citations
    bns_numbers = {c["section_number"] for c in bns_citations}
    assert 101 in bns_numbers

    provenance = next(
        c for c in payload["citations"] if c.get("mapping_source") is not None
    )
    assert provenance["mapping_source"] == "jbp123_bns"
    assert provenance["ipc_section_number"] == 302
    assert "302" in payload["lead"] or "302" in payload["body"]


def test_unknown_ipc_mapping_returns_low_confidence_without_invented_bns(
    client, auth_headers
) -> None:
    unknown_ipc = max(FIXTURE_IPC_SECTIONS) + 50_000
    response = client.post(
        "/research",
        json={"query": f"What happened to IPC {unknown_ipc}?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["query_mode"] == "ipc_to_bns_mapping"
    assert payload["confidence"] == "low"
    assert payload["citations"] == []
