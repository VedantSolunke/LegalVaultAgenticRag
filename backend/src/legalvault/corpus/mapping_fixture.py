from legalvault.models.mapping import MappingRecord

FIXTURE_MAPPINGS: tuple[MappingRecord, ...] = (
    MappingRecord(
        ipc_section_number=302,
        bns_section_numbers=[101],
        source="jbp123_bns",
        ipc_title="Punishment for murder",
        bns_title="Murder",
    ),
)

FIXTURE_IPC_SECTIONS: list[int] = [
    record.ipc_section_number for record in FIXTURE_MAPPINGS
]
