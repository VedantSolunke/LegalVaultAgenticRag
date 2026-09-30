# LegalVault Agentic RAG

Agentic legal research assistant focused on the Bharatiya Nyaya Sanhita (BNS)—built as an **AI engineering portfolio** project (deployable demo + clean repo). See `docs/portfolio-v1.md`, `GLOSSARY.md`, and `docs/adr/` for scope and decisions.

## Components

| Path | Role |
|------|------|
| `backend/` | FastAPI research API, LangGraph pipeline, Postgres/pgvector corpus |
| `web/` | Next.js UI for registered users (chat sessions, citations, disclaimer) |
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

### Authentication

**Deployed demo:** public email signup via Supabase Auth (ADR-0014). Configure `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `NEXT_PUBLIC_SITE_URL` on the web app; set `LEGALVAULT_SUPABASE_URL` in `backend/.env` (JWT verification via JWKS). Apply `backend/sql/003_chat_sessions.sql` and `005_auth_profile_on_signup.sql` on Supabase.

**Local without Supabase:** set `NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN=test-user-token` in `web/.env.local` when the API accepts the dev test token (local only).

Set `is_admin` on your profile to view debug traces (interview demos only).

### Deployment shape (portfolio V1)

- **Web:** Vercel (Next.js)
- **API:** container host (Railway, Fly, etc.) for FastAPI + LangGraph
- **Data / auth:** Supabase (Postgres, pgvector, Auth)
- **Local:** `docker compose` for Postgres; run API and web on the host

More detail: `docs/portfolio-v1.md`, `backend/README.md`, `web/README.md`.
