# Local datasets

LegalVault v1 uses curated data under this directory. Large Hugging Face clones are **not** committed; fetch them locally when ingesting or running eval with JSONL samples.

## BNS section records (GSMS-B)

Clone or download [indian-legal-sections-bns-bnss-bsa-2023](https://huggingface.co/datasets/indian-legal-sections-bns-bnss-bsa-2023) into:

`datasets/indian-legal-sections-bns-bnss-bsa-2023/`

Ingest BNS rows only:

```bash
cd backend
export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
uv run legalvault-ingest-bns --apply-schema \
  --json-path ../datasets/indian-legal-sections-bns-bnss-bsa-2023/bns_sections.json
```

## IPC mapping CSVs

Primary and supplemental mapping exports live in `datasets/ipc-mapping/` (checked in). To refresh:

```bash
mkdir -p datasets/ipc-mapping
curl -L 'https://huggingface.co/datasets/jbp123/bns/resolve/main/Comparative%20Table%20of%20IPC%20and%20Bharatiya%20Nyaya%20Sanhita.csv' \
  -o datasets/ipc-mapping/jbp123_comparative_table.csv
curl -L 'https://huggingface.co/datasets/nandhakumarg/IPC_and_BNS_transformation/resolve/main/IPC%20and%20BNS%20transformation%20.csv' \
  -o datasets/ipc-mapping/nandhakumarg_ipc_bns_transformation.csv
```

See `backend/README.md` for `legalvault-ingest-ipc-mapping`.

## Eval QA JSONL (never ingested)

Optional offline eval samples: clone [Indian-Legal-QA-BNS-BNSS-BSA](https://huggingface.co/datasets/Indian-Legal-QA-BNS-BNSS-BSA) and pass `--jsonl` to `legalvault-eval`. QA text is **not** embedded or retrieved as evidence (ADR-0003).

## MHA BNS PDF (optional)

`datasets/BNS_File.pdf` may be kept locally for future statutory reconciliation; v1 display text comes from GSMS-B JSON (ADR-0002).
