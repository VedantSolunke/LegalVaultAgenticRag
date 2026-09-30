"""Stub providers for tests and local development without live Gemini."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StubLLMResult:
    lead: str
    body: str


class StubLLMProvider:
    def compose_section_lookup(
        self, *, section_number: int, title: str, excerpt: str
    ) -> StubLLMResult:
        lead = (
            f"BNS Section {section_number} ({title}) sets out the statutory rule "
            "below; verify against the cited text."
        )
        body = (
            f"Section {section_number} — {title}\n\n"
            f"{excerpt}\n\n"
            "This summary is grounded in the retrieved section record only."
        )
        return StubLLMResult(lead=lead, body=body)

    def compose_legal_concept_lookup(
        self,
        *,
        query: str,
        sections: list,
    ) -> StubLLMResult:
        titles = ", ".join(f"Section {s.section_number} ({s.title})" for s in sections)
        lead = (
            f"Retrieved BNS section records that may relate to your question about "
            f"“{query.strip()}”; verify citations below."
        )
        body = (
            f"The hybrid retrieval pipeline returned: {titles}.\n\n"
            "Each citation excerpt is taken from the indexed GSMS-B section record only."
        )
        return StubLLMResult(lead=lead, body=body)
