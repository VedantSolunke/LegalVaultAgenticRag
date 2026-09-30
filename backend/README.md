# LegalVault backend — BNS research API

## Run locally

```bash
cd backend
uv sync --extra dev
uv run legalvault-api
```

## BNS corpus ingest (Postgres + pgvector)

Start Postgres with pgvector (from repo root):

```bash
docker compose up -d postgres
```

Apply schema and ingest GSMS-B `bns_sections.json` (BNS rows only; QA JSONL is rejected):

```bash
cd backend
export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
uv run legalvault-ingest-bns --apply-schema \
  --json-path /path/to/GSMS-B/bns_sections.json
```

Run the API against the ingested corpus:

```bash
export LEGALVAULT_CORPUS_BACKEND=postgres
export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
uv run legalvault-api
```

Embeddings use the deterministic stub provider by default in the ingest CLI; swap in a live Google embedding provider before production ingest.

## IPC mapping ingest (structured lookup only)

Ingest curated IPC→BNS mapping CSVs (primary `jbp123/bns`, optional supplemental `nandhakumarg/IPC_and_BNS_transformation`). Mapping rows are stored for structured lookup only—no embeddings.

```bash
cd backend
export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
uv run legalvault-ingest-ipc-mapping --apply-schema \
  --primary-csv /path/to/jbp123/bns/Comparative\ Table\ of\ IPC\ and\ Bharatiya\ Nyaya\ Sanhita.csv \
  --supplemental-csv "/path/to/nandhakumarg/IPC and BNS transformation .csv"
```

## Tests

Integration tests hit the HTTP API with fixture corpus and stub providers (no live Gemini). Postgres tests use `LEGALVAULT_TEST_DATABASE_URL` when a database is available (CI provides one):

```bash
cd backend
uv sync --extra dev
uv run pytest
```
