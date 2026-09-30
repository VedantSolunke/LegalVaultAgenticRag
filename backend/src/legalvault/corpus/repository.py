import re

from legalvault.corpus.fixture import FIXTURE_SECTIONS
from legalvault.models.research import SectionRecord
from legalvault.retrieval.hybrid import reciprocal_rank_fusion


class SectionCorpus:
    """In-memory BNS section store for tests and local tracer mode."""

    def __init__(self, sections: tuple[SectionRecord, ...] = FIXTURE_SECTIONS) -> None:
        self._by_number = {s.section_number: s for s in sections}
        self._sections = sections

    def get_section(self, section_number: int) -> SectionRecord | None:
        return self._by_number.get(section_number)

    def lookup_by_section_numbers(self, numbers: list[int]) -> list[SectionRecord]:
        found: list[SectionRecord] = []
        for number in numbers:
            section = self._by_number.get(number)
            if section is not None:
                found.append(section)
        return found

    def _keyword_search(self, query: str, limit: int) -> list[SectionRecord]:
        tokens = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2}
        if not tokens:
            return []
        scored: list[tuple[int, SectionRecord]] = []
        for section in self._sections:
            hay = f"{section.title} {section.text}".lower()
            score = sum(1 for t in tokens if t in hay)
            if score:
                scored.append((score, section))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def hybrid_retrieve(
        self,
        query: str,
        *,
        section_numbers: list[int] | None = None,
        limit: int = 5,
    ) -> list[SectionRecord]:
        exact = self.lookup_by_section_numbers(section_numbers or [])
        keyword = self._keyword_search(query, max(limit, 5))
        return reciprocal_rank_fusion([exact, keyword], limit=limit)

    @property
    def known_section_numbers(self) -> frozenset[int]:
        return frozenset(self._by_number.keys())


DEFAULT_CORPUS = SectionCorpus()
