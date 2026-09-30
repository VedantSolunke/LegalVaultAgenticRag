"""Layered evidence verification helpers."""

from legalvault.retrieval.section_lookup import extract_section_numbers


def citations_supported(
    citations: list,
    *,
    allowed_section_numbers: frozenset[int],
) -> bool:
    return all(c.section_number in allowed_section_numbers for c in citations)


def prose_references_only_retrieved_sections(
    text: str,
    *,
    allowed_section_numbers: frozenset[int],
) -> bool:
    for number in extract_section_numbers(text):
        if number not in allowed_section_numbers:
            return False
    return True
