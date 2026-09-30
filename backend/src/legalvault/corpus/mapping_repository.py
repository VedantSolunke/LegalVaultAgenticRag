from legalvault.corpus.mapping_fixture import FIXTURE_MAPPINGS
from legalvault.models.mapping import MappingRecord


class MappingStore:
    """Structured IPC→BNS mapping lookup (not vector-indexed)."""

    def __init__(
        self, records: tuple[MappingRecord, ...] = FIXTURE_MAPPINGS
    ) -> None:
        self._by_ipc = {r.ipc_section_number: r for r in records}

    def lookup_by_ipc_numbers(self, numbers: list[int]) -> list[MappingRecord]:
        found: list[MappingRecord] = []
        for number in numbers:
            record = self._by_ipc.get(number)
            if record is not None:
                found.append(record)
        return found

    def get_mapping(self, ipc_section_number: int) -> MappingRecord | None:
        return self._by_ipc.get(ipc_section_number)

    @property
    def known_ipc_sections(self) -> frozenset[int]:
        return frozenset(self._by_ipc.keys())


DEFAULT_MAPPING_STORE = MappingStore()
