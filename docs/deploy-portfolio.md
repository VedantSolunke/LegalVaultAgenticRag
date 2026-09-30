# Portfolio deploy runbook

End-to-end checklist for the public demo (ADR-0015). Local development stays on Docker Compose Postgres plus host-run API/web—see root `README.md`.

## Local machine (your `.env` setup)

1. **Web:** `NEXT_PUBLIC_SITE_URL=http://localhost:3000` in `web/.env.local` (done for email redirects).
2. **Backend:** `LEGALVAULT_CORPUS_BACKEND=postgres`, `LEGALVAULT_DATABASE_URL`, `LEGALVAULT_SUPABASE_URL`, and `GEMINI_API_KEY` (read by the API). Restart the API after changing `.env`.
3. **One-time on Supabase:** apply schema (ingest CLIs run `apply_schema`, including `005_auth_profile_on_signup.sql`).
4. **Ingest:** `legalvault-ingest-bns` + `legalvault-ingest-ipc-mapping` (358 BNS sections + IPC mappings when using GSMS-B JSON under `datasets/`).
5. **Supabase Auth → URL configuration:** Site URL `http://localhost:3000`; redirect allowlist `http://localhost:3000/auth/callback`, `http://localhost:3000/reset-password`.
6. Run `uv run legalvault-api` (backend) and `npm run dev` (web). Sign up via Supabase—not the dev bearer token while `LEGALVAULT_SUPABASE_URL` is set.

Embeddings for ingest still use the deterministic stub (768-dim pgvector schema). `GEMINI_EMBEDDING_*` in `.env` is not wired yet; live Gemini is used for answer composition when `GEMINI_API_KEY` is set.

## 1. Supabase project

1. Create a Supabase project with **pgvector** enabled.
2. Run SQL migrations in order:
   - `backend/sql/003_chat_sessions.sql`
   - `backend/sql/004_request_traces.sql` (if using admin traces)
   - `backend/sql/005_auth_profile_on_signup.sql`
3. Auth settings:
   - Enable email signup; require email confirmation in production.
   - **Site URL** and redirect allowlist: your Vercel origin, `/auth/callback`, `/reset-password`.
4. Set your account’s `profiles.is_admin = true` if you need **debug trace** access in interviews.

## 2. Corpus ingest (production)

On a machine with network access and Google AI credentials:

```bash
cd backend
export LEGALVAULT_DATABASE_URL="postgresql://..."  # Supabase direct connection
uv run legalvault-ingest-bns --apply-schema \
  --json-path /path/to/GSMS-B/bns_sections.json
uv run legalvault-ingest-ipc-mapping --apply-schema
```

Use live embedding provider env vars (not stubs) before ingest. See `backend/README.md` for IPC CSV download paths.

## 3. API (Railway, Fly, etc.)

Deploy the `backend/Dockerfile` or run `uv run legalvault-api` on your host.

| Variable | Purpose |
|----------|---------|
| `LEGALVAULT_DATABASE_URL` | Supabase Postgres |
| `LEGALVAULT_CORPUS_BACKEND` | `postgres` |
| `LEGALVAULT_SUPABASE_URL` | JWT verification (JWKS) |
| `LEGALVAULT_CORS_ORIGINS` | `https://your-app.vercel.app` |
| Google / Gemini keys | Per your provider module config |

Health: `GET /health` (if exposed) or smoke `POST /research` with a user JWT.

## 4. Web (Vercel)

Deploy `web/` as a Next.js project.

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key |
| `NEXT_PUBLIC_SITE_URL` | `https://your-app.vercel.app` |
| `NEXT_PUBLIC_LEGALVAULT_API_URL` | Hosted API origin |

Do not set `NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN` in production.

## 5. Recruiter demo script

1. Sign up with email on the live site.
2. “What is BNS section 101?” — section lookup + citations.
3. “What happened to IPC section 302?” — IPC→BNS mapping.
4. Short fact pattern with concrete conduct — expect citations and uncertainty copy when facts are thin.

Optional: screenshot of **admin user** debug trace panel in README (not shown to normal users).

## 6. Pre-demo quality

```bash
cd backend
uv run legalvault-eval --check-invite-gate
```

Against staging API:

```bash
uv run legalvault-eval --api-url https://api.example.com --token "<user-jwt>"
```

CI runs `legalvault-eval` without `--check-invite-gate`; see `docs/eval-quality-gate.md`.
