from legalvault.corpus.fixture import FIXTURE_SECTIONS
from legalvault.models.research import SectionRecord


class SectionCorpus:
    """In-memory BNS section store. Replace with Supabase/pgvector for production."""

    def __init__(self, sections: tuple[SectionRecord, ...] = FIXTURE_SECTIONS) -> None:
        self._by_number = {s.section_number: s for s in sections}

    def get_section(self, section_number: int) -> SectionRecord | None:
        return self._by_number.get(section_number)

    def lookup_by_section_numbers(self, numbers: list[int]) -> list[SectionRecord]:
        found: list[SectionRecord] = []
        for number in numbers:
            section = self._by_number.get(number)
            if section is not None:
                found.append(section)
        return found

    @property
    def known_section_numbers(self) -> frozenset[int]:
        return frozenset(self._by_number.keys())


DEFAULT_CORPUS = SectionCorpus()
