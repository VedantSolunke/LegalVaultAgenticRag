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


class StubEmbeddingProvider:
    def embed_query(self, text: str) -> list[float]:
        _ = text
        return [0.0]
