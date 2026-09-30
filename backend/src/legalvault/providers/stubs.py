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

    def compose_ipc_mapping(
        self,
        *,
        ipc_section_number: int,
        ipc_title: str | None,
        mapping_source: str,
        bns_sections: list,
    ) -> StubLLMResult:
        ipc_label = ipc_title or f"IPC section {ipc_section_number}"
        if bns_sections:
            bns_summary = ", ".join(
                f"BNS {s.section_number} ({s.title})" for s in bns_sections
            )
        else:
            bns_summary = "the mapped BNS section record(s) (not found in corpus)"
        lead = (
            f"{ipc_label} maps to {bns_summary} per ingested mapping data "
            f"({mapping_source}); verify statutory text in citations."
        )
        body = (
            f"The structured IPC→BNS mapping store links IPC section "
            f"{ipc_section_number} to the BNS target(s) above. "
            "Statutory excerpts below come from retrieved BNS section records only."
        )
        return StubLLMResult(lead=lead, body=body)
