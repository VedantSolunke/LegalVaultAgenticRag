# Public email signup (resume deployment)

Status: accepted

Supersedes the registration policy in ADR-0007 for the deployed resume instance: users may self-register with email and password via Supabase Auth. Email confirmation is required in production; local Supabase projects may use auto-confirm for developer convenience.

Operator responsibilities:

- Apply `backend/sql/003_chat_sessions.sql` and `backend/sql/005_auth_profile_on_signup.sql` on the Supabase Postgres project.
- Configure Supabase URL settings (`Site URL`, redirect allowlist for `/auth/callback` and `/reset-password`).
- Set `NEXT_PUBLIC_SITE_URL` on the web app to match the deployed origin.

Invite-only operation described in ADR-0007 remains valid for a private operator-only deployment if registration is disabled in the Supabase dashboard.
