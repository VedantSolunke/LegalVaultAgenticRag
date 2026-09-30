"""Stub providers for tests and local development without live Gemini."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StubLLMResult:
    lead: str
    body: str


_BEST_EFFORT_NOTE = (
    "\n\nBest-effort summary from retrieved BNS text only—not reliable "
    "applicability analysis or legal advice."
)


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
            f"{_BEST_EFFORT_NOTE}"
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

    def compose_fact_pattern(
        self,
        *,
        query: str,
        sections: list,
        thin_facts: bool,
    ) -> StubLLMResult:
        if sections:
            labels = ", ".join(f"Section {s.section_number} ({s.title})" for s in sections)
            lead = (
                "Retrieved BNS sections that may relate to the described facts; "
                "verify each citation and whether the facts satisfy the statutory elements."
            )
            body = (
                f"Candidate provisions from the corpus: {labels}.\n\n"
                "This is a preliminary mapping from your narrative to indexed BNS text only."
            )
        else:
            lead = "No matching BNS sections were retrieved for this fact pattern."
            body = (
                "Try naming specific conduct or requesting a direct section lookup "
                "once you know a section number."
            )
        if thin_facts:
            body += (
                "\n\nThe facts provided are limited; applicability is uncertain and "
                "additional detail would be needed for a stronger tie to any section."
            )
        return StubLLMResult(lead=lead, body=body)

    def compose_section_comparison(
        self,
        *,
        sections: list,
    ) -> StubLLMResult:
        if len(sections) < 2:
            primary = sections[0] if sections else None
            if primary is None:
                return StubLLMResult(
                    lead="Could not compare sections without retrieved records.",
                    body="Name two BNS section numbers to compare.",
                )
            return StubLLMResult(
                lead=f"Only one section record was retrieved (BNS {primary.section_number}).",
                body=(
                    f"Section {primary.section_number} — {primary.title}\n\n"
                    "Add another section number to compare statutory text side by side."
                ),
            )
        left, right = sections[0], sections[1]
        lead = (
            f"Comparison of BNS sections {left.section_number} and {right.section_number} "
            "based on retrieved statutory text only."
        )
        body = (
            f"Section {left.section_number} — {left.title}\n{left.text}\n\n"
            f"Section {right.section_number} — {right.title}\n{right.text}\n\n"
            "Differences and overlap should be verified against the full section text."
            f"{_BEST_EFFORT_NOTE}"
        )
        return StubLLMResult(lead=lead, body=body)

    def compose_general_bns_information(self) -> StubLLMResult:
        lead = (
            "The Bharatiya Nyaya Sanhita (BNS), 2023 is the substantive criminal code "
            "indexed in LegalVault v1."
        )
        body = (
            "LegalVault answers substantive BNS questions using retrieved section records. "
            "Procedural law (BNSS), evidence law (BSA), and case law are out of corpus. "
            "This note is general orientation only—not legal advice."
            f"{_BEST_EFFORT_NOTE}"
        )
        return StubLLMResult(lead=lead, body=body)

    def compose_out_of_corpus(self, *, query: str) -> StubLLMResult:
        lead = "This question is outside the current LegalVault corpus."
        body = (
            "LegalVault v1 covers substantive BNS criminal law with IPC→BNS mapping. "
            "BNSS (procedure), BSA (evidence), case law, and non-Indian law are not indexed. "
            "Rephrase as a BNS section lookup or in-corpus concept question, or consult "
            "the appropriate procedural/evidence sources separately."
        )
        return StubLLMResult(lead=lead, body=body)

    def check_faithfulness(
        self,
        *,
        lead: str,
        body: str,
        allowed_section_numbers: frozenset[int],
    ) -> bool:
        from legalvault.verification.evidence import (
            prose_references_only_retrieved_sections,
        )

        combined = f"{lead}\n{body}"
        return prose_references_only_retrieved_sections(
            combined,
            allowed_section_numbers=allowed_section_numbers,
        )
