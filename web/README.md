# LegalVault web UI

Next.js chat UI for trusted users: Supabase sign-in (or dev bearer token), session list, BNS research responses with expandable citations, confidence labels, and the legal research disclaimer.

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

   Open [http://localhost:3000](http://localhost:3000). Use **Continue with dev API token** when `NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN` is set, or sign in with Supabase email/password when URL and anon key are configured.

4. Ensure the API allows the UI origin (default `http://localhost:3000` via `LEGALVAULT_CORS_ORIGINS`).

## Scripts

- `npm run dev` — development server
- `npm run build` / `npm start` — production build
- `npm run lint` — ESLint
- `npm run test` — Vitest unit tests
- `npm run typecheck` — TypeScript without emit

## Supabase

Create invite-only users in your Supabase project (ADR-0007). Set the API `LEGALVAULT_SUPABASE_JWT_SECRET` to your project JWT secret so the backend accepts Supabase access tokens. Apply `backend/sql/003_chat_sessions.sql` on the same Postgres used by the API.

Debug trace UI is intentionally omitted for standard users (ADR-0009).
