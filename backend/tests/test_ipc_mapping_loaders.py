from pathlib import Path

from legalvault.corpus.ipc_mapping_loaders import (
    load_jbp123_bns_csv,
    load_merged_mapping_csvs,
    load_nandhakumarg_csv,
    merge_mapping_records,
)
from legalvault.models.mapping import MappingRecord

FIXTURES = Path(__file__).parent / "fixtures"


def test_jbp123_fixture_maps_ipc_302_to_bns_101() -> None:
    records = load_jbp123_bns_csv(FIXTURES / "jbp123_bns_sample.csv")
    match = next(r for r in records if r.ipc_section_number == 302)
    assert match.bns_section_numbers == [101]
    assert match.source == "jbp123_bns"


def test_nandhakumarg_fixture_parses_response_dict() -> None:
    records = load_nandhakumarg_csv(
        FIXTURES / "nandhakumarg_ipc_bns_sample.csv"
    )
    match = next(r for r in records if r.ipc_section_number == 7)
    assert match.bns_section_numbers == [3]
    assert match.source == "nandhakumarg_ipc_bns_transformation"


def test_merge_prefers_primary_over_supplemental_for_same_ipc() -> None:
    primary = [
        MappingRecord(
            ipc_section_number=7,
            bns_section_numbers=[99],
            source="jbp123_bns",
        )
    ]
    supplemental = [
        MappingRecord(
            ipc_section_number=7,
            bns_section_numbers=[3],
            source="nandhakumarg_ipc_bns_transformation",
        )
    ]
    merged = merge_mapping_records(primary, supplemental)
    assert merged[0].bns_section_numbers == [99]


def test_merged_csv_fixture_fills_gap_from_supplemental() -> None:
    records = load_merged_mapping_csvs(
        primary_csv=FIXTURES / "jbp123_bns_sample.csv",
        supplemental_csv=FIXTURES / "nandhakumarg_ipc_bns_sample.csv",
    )
    assert any(r.ipc_section_number == 302 for r in records)
    assert any(r.ipc_section_number == 7 for r in records)
