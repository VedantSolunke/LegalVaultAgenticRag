# Supabase persistence for sessions and traces

Status: accepted

One Supabase Postgres project holds chat sessions, messages (redacted per ADR-0012), and per-request trace JSON for debugging. Session history stays short (roughly five to ten turns) with TTL-based purge of stale sessions. Admin users can read full traces; standard users cannot.
