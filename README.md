# LegalVault Agentic RAG

Agentic legal research assistant focused on the Bharatiya Nyaya Sanhita (BNS). See `Requirement.md`, `GLOSSARY.md`, and `docs/adr/` for product and architecture decisions.

## Components

| Path | Role |
|------|------|
| `backend/` | FastAPI research API, LangGraph pipeline, Postgres/pgvector corpus |
| `web/` | Next.js UI for trusted users (chat sessions, citations, disclaimer) |
| `datasets/` | BNS PDF, IPC mapping CSVs, GSMS-B JSON (when present) |

## Quick start (local UI + API)

```bash
# Full stack (Postgres + API + web)
docker compose up --build

# Or run services individually:
# Database
docker compose up -d postgres

# API (from backend/README.md for corpus ingest)
cd backend
export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
uv sync --extra dev
uv run legalvault-api

# Web UI
cd ../web
cp .env.example .env.local
npm install
npm run dev
```

Use `NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN=test-user-token` in `web/.env.local` when the API runs without Supabase JWT verification (local only). For Supabase Auth, configure `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `NEXT_PUBLIC_SITE_URL` on the web app; set `LEGALVAULT_SUPABASE_URL` in `backend/.env` (the API verifies access tokens via JWKS). Apply `backend/sql/005_auth_profile_on_signup.sql` on Supabase after `003_chat_sessions.sql`. See `web/README.md` and ADR-0014.

More detail: `backend/README.md`, `web/README.md`.
