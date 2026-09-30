from pathlib import Path

import pytest

from legalvault.corpus.gsms_b import (
    assert_ingestible_bns_json_path,
    load_bns_sections_json,
)

FIXTURE_JSON = Path(__file__).parent / "fixtures" / "bns_sections_sample.json"


def test_load_sample_bns_json() -> None:
    records = load_bns_sections_json(FIXTURE_JSON)
    numbers = {r.section_number for r in records}
    assert numbers == {101, 103, 115}
    murder = next(r for r in records if r.section_number == 101)
    assert murder.title == "Murder"
    assert murder.act == "BNS"


def test_refuses_qa_jsonl_paths() -> None:
    with pytest.raises(ValueError, match="QA or JSONL"):
        assert_ingestible_bns_json_path(Path("datasets/indian-legal-qa/train.jsonl"))
