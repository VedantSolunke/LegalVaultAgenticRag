from pathlib import Path

import pytest

from legalvault.cli.ingest_ipc_mapping import (
    _resolve_existing_csv,
    _standard_mapping_paths,
)


def test_standard_mapping_paths_include_repo_and_backend_locations() -> None:
    paths = _standard_mapping_paths("jbp123_comparative_table.csv")
    assert any("datasets" in str(p) and "ipc-mapping" in str(p) for p in paths)
    assert any(str(p).endswith("backend/datasets/ipc-mapping/jbp123_comparative_table.csv") for p in paths)


def test_resolve_falls_back_to_backend_datasets(tmp_path, monkeypatch) -> None:
    backend = tmp_path / "backend"
    backend.mkdir()
    mapping_dir = backend / "datasets" / "ipc-mapping"
    mapping_dir.mkdir(parents=True)
    csv_path = mapping_dir / "jbp123_comparative_table.csv"
    csv_path.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        "legalvault.cli.ingest_ipc_mapping._backend_dir",
        lambda: backend,
    )
    monkeypatch.setattr(
        "legalvault.cli.ingest_ipc_mapping._repo_root",
        lambda: tmp_path,
    )

    wrong = tmp_path / "datasets" / "ipc-mapping" / "jbp123_comparative_table.csv"
    resolved = _resolve_existing_csv(
        wrong,
        label="Primary CSV (jbp123/bns)",
        standard_filename="jbp123_comparative_table.csv",
        required=True,
    )
    assert resolved == csv_path.resolve()


def test_resolve_exits_when_missing(tmp_path, monkeypatch) -> None:
    backend = tmp_path / "backend"
    backend.mkdir()
    monkeypatch.setattr(
        "legalvault.cli.ingest_ipc_mapping._backend_dir",
        lambda: backend,
    )
    monkeypatch.setattr(
        "legalvault.cli.ingest_ipc_mapping._repo_root",
        lambda: tmp_path,
    )
    with pytest.raises(SystemExit) as exc:
        _resolve_existing_csv(
            Path("missing.csv"),
            label="Primary CSV (jbp123/bns)",
            standard_filename="jbp123_comparative_table.csv",
            required=True,
        )
    assert exc.value.code == 1
