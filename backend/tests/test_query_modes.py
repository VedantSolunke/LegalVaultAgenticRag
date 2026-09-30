"""Query-mode heuristics (classification boundaries)."""

from legalvault.retrieval.query_modes import classify_query_mode, is_general_bns_information_query


def test_robbery_section_question_is_not_general_bns_meta() -> None:
    query = "what is the bns section for robbery?"
    assert not is_general_bns_information_query(query)
    assert classify_query_mode(query) == "legal_concept_lookup"


def test_pure_what_is_the_bns_stays_meta() -> None:
    for query in ("What is the BNS?", "what is the bns"):
        assert is_general_bns_information_query(query)
        assert classify_query_mode(query) == "general_bns_information"
