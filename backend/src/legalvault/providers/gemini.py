"""Gemini-backed composition with stub fallback on errors."""

from __future__ import annotations

import logging
from collections.abc import Callable

from google import genai

from legalvault.providers.stubs import StubLLMProvider, StubLLMResult

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are LegalVault, a BNS legal research assistant (not legal advice). "
    "Ground every statutory claim in the retrieved excerpts provided. "
    "Use plain English. If facts are incomplete, state uncertainty clearly. "
    "Format: first line is a short lead summary; remaining paragraphs are detail."
)


class GeminiLLMProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        fallback: StubLLMProvider,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._fallback = fallback

    def _generate(self, user_prompt: str) -> StubLLMResult | None:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=f"{_SYSTEM}\n\n{user_prompt}",
            )
            text = (response.text or "").strip()
            if not text:
                return None
            parts = text.split("\n\n", 1)
            lead = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else text
            return StubLLMResult(lead=lead, body=body)
        except Exception:
            logger.exception("Gemini generate_content failed; using stub fallback")
            return None

    def _with_fallback(
        self, user_prompt: str, fallback_fn: Callable[[], StubLLMResult]
    ) -> StubLLMResult:
        draft = self._generate(user_prompt)
        if draft is not None:
            return draft
        return fallback_fn()

    def compose_section_lookup(
        self, *, section_number: int, title: str, excerpt: str
    ) -> StubLLMResult:
        prompt = (
            f"Explain BNS section {section_number} ({title}) using only this text:\n"
            f"{excerpt}"
        )
        return self._with_fallback(
            prompt,
            lambda: self._fallback.compose_section_lookup(
                section_number=section_number, title=title, excerpt=excerpt
            ),
        )

    def compose_legal_concept_lookup(
        self, *, query: str, sections: list
    ) -> StubLLMResult:
        blocks = "\n".join(
            f"Section {s.section_number} ({s.title}): {s.text[:400]}…"
            for s in sections
        )
        prompt = (
            f"User question: {query}\nRetrieved BNS sections:\n{blocks}\n"
            "Include a best-effort disclaimer that this is not applicability analysis."
        )
        return self._with_fallback(
            prompt,
            lambda: self._fallback.compose_legal_concept_lookup(
                query=query, sections=sections
            ),
        )

    def compose_ipc_mapping(
        self,
        *,
        ipc_section_number: int,
        ipc_title: str | None,
        mapping_source: str,
        bns_sections: list,
    ) -> StubLLMResult:
        bns = "\n".join(
            f"BNS {s.section_number} ({s.title}): {s.text[:300]}…" for s in bns_sections
        )
        prompt = (
            f"IPC section {ipc_section_number} ({ipc_title or 'IPC'}) maps per "
            f"{mapping_source}. BNS targets:\n{bns}"
        )
        return self._with_fallback(
            prompt,
            lambda: self._fallback.compose_ipc_mapping(
                ipc_section_number=ipc_section_number,
                ipc_title=ipc_title,
                mapping_source=mapping_source,
                bns_sections=bns_sections,
            ),
        )

    def compose_fact_pattern(
        self, *, query: str, sections: list, thin_facts: bool
    ) -> StubLLMResult:
        blocks = "\n".join(
            f"Section {s.section_number} ({s.title}): {s.text[:300]}…"
            for s in sections
        )
        prompt = (
            f"Fact pattern: {query}\n"
            f"Retrieved sections:\n{blocks or '(none)'}\n"
            f"Facts thin: {thin_facts}. List candidate sections with uncertainty."
        )
        return self._with_fallback(
            prompt,
            lambda: self._fallback.compose_fact_pattern(
                query=query, sections=sections, thin_facts=thin_facts
            ),
        )

    def compose_section_comparison(self, *, sections: list) -> StubLLMResult:
        return self._with_fallback(
            "Compare these BNS sections side by side with a best-effort disclaimer.\n"
            + "\n".join(
                f"Section {s.section_number} — {s.title}\n{s.text[:500]}…"
                for s in sections
            ),
            lambda: self._fallback.compose_section_comparison(sections=sections),
        )

    def compose_general_bns_information(self) -> StubLLMResult:
        return self._with_fallback(
            "Briefly orient the user to what LegalVault covers (BNS v1, IPC mapping, "
            "out of corpus: BNSS, BSA, case law). Best-effort disclaimer required.",
            self._fallback.compose_general_bns_information,
        )

    def compose_out_of_corpus(self, *, query: str) -> StubLLMResult:
        return self._with_fallback(
            f"Refuse this out-of-corpus query politely: {query}",
            lambda: self._fallback.compose_out_of_corpus(query=query),
        )

    def check_faithfulness(
        self,
        *,
        lead: str,
        body: str,
        allowed_section_numbers: frozenset[int],
    ) -> bool:
        return self._fallback.check_faithfulness(
            lead=lead,
            body=body,
            allowed_section_numbers=allowed_section_numbers,
        )
