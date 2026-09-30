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

Download the CSV exports once (**from the repository root**, not `backend/`):

```bash
cd /path/to/LegalVaultAgenticRag
mkdir -p datasets/ipc-mapping
curl -L 'https://huggingface.co/datasets/jbp123/bns/resolve/main/Comparative%20Table%20of%20IPC%20and%20Bharatiya%20Nyaya%20Sanhita.csv' \
  -o datasets/ipc-mapping/jbp123_comparative_table.csv
curl -L 'https://huggingface.co/datasets/nandhakumarg/IPC_and_BNS_transformation/resolve/main/IPC%20and%20BNS%20transformation%20.csv' \
  -o datasets/ipc-mapping/nandhakumarg_ipc_bns_transformation.csv
```

Ingest (from `backend/`; CSV paths are optional if files are in the standard `datasets/ipc-mapping/` location):

```bash
cd backend
export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
uv run legalvault-ingest-ipc-mapping --apply-schema
```

If you already downloaded into `backend/datasets/ipc-mapping/` by mistake, the CLI will still find them. To pass paths explicitly:

```bash
uv run legalvault-ingest-ipc-mapping --apply-schema \
  --primary-csv datasets/ipc-mapping/jbp123_comparative_table.csv
```

## Chat sessions (Supabase / Postgres)

Apply schema (`003_chat_sessions.sql` is included when you run `--apply-schema` on ingest CLIs or `apply_schema` in tests). Set `LEGALVAULT_DATABASE_URL` and use a Supabase JWT or the dev test bearer tokens.

- `POST /sessions` — create a **chat session**
- `GET /sessions` — list sessions for the authenticated user
- `GET /sessions/{id}/messages` — list messages (assistant rows include structured `research` with citations)
- `POST /sessions/{id}/messages` — send a message, run research, persist **redacted** user/assistant rows

The API sets CORS for `http://localhost:3000` by default (`LEGALVAULT_CORS_ORIGINS`, comma-separated).

## Debug traces

When `LEGALVAULT_DATABASE_URL` is set, each `/research` and session message call stores a `request_traces` row. Responses include a `trace_id`. Only **admin** users may fetch `GET /traces/{trace_id}` (enforced in the API; Supabase RLS limits direct reads to admins).

Dev bearer tokens: `test-admin-token` (admin), `test-user-token` (standard).

## Tests

Integration tests hit the HTTP API with fixture corpus and stub providers (no live Gemini). Postgres tests use `LEGALVAULT_TEST_DATABASE_URL` when a database is available (CI provides one):

```bash
cd backend
uv sync --extra dev
uv run pytest
```
