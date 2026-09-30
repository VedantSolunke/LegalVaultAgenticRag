# LegalVault web UI

Next.js chat UI: Supabase email/password signup and sign-in (or dev bearer token), session list, BNS research responses with expandable citations, confidence labels, and the legal research disclaimer.

## Local development

1. Start Postgres and the API (see repository `README.md` and `backend/README.md`). For quick UI testing without Supabase, run the API with fixture corpus and dev tokens only:

   ```bash
   cd backend
   export LEGALVAULT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legalvault
   uv run legalvault-api
   ```

2. Copy environment variables:

   ```bash
   cd web
   cp .env.example .env.local
   ```

3. Install and run the UI:

   ```bash
   npm install
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000). Use **Continue with dev API token** when `NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN` is set, or use **Create one** on the login page to sign up with Supabase when URL and anon key are configured.

4. Ensure the API allows the UI origin (default `http://localhost:3000` via `LEGALVAULT_CORS_ORIGINS`).

## Scripts

- `npm run dev` — development server
- `npm run build` / `npm start` — production build
- `npm run lint` — ESLint
- `npm run test` — Vitest unit tests
- `npm run typecheck` — TypeScript without emit

## Supabase

See ADR-0014 for the public signup policy on the resume deployment.

1. In the Supabase SQL editor, apply `backend/sql/003_chat_sessions.sql` then `backend/sql/005_auth_profile_on_signup.sql` on the project database.
2. **Authentication → URL configuration**: set **Site URL** to your web origin (e.g. `http://localhost:3000` or your production URL). Add redirect URLs for `{origin}/auth/callback` and `{origin}/reset-password`.
3. **Authentication → Providers → Email**: enable email signup; turn **Confirm email** on for production. For local testing, you may enable auto-confirm so you are not clicking confirmation links on every signup.
4. Web env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `NEXT_PUBLIC_SITE_URL` (same origin as step 2, no trailing slash).
5. API env: `LEGALVAULT_SUPABASE_URL` so the backend verifies access tokens via JWKS (legacy HS256 projects may use `LEGALVAULT_SUPABASE_JWT_SECRET`).

Do not set `NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN` in production.

Debug trace UI is intentionally omitted for standard users (ADR-0009).
