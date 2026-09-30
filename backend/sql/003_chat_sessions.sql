-- Chat sessions and messages (ADR-0006, ADR-0008). Apply on Supabase or app Postgres.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS chat_sessions_user_id_idx ON chat_sessions (user_id);
CREATE INDEX IF NOT EXISTS chat_sessions_updated_at_idx ON chat_sessions (updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions (id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    body TEXT NOT NULL,
    research_response JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_session_id_created_at_idx
    ON messages (session_id, created_at);

-- RLS for Supabase client access (API enforces user_id when using service credentials).
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
        EXECUTE 'DROP POLICY IF EXISTS chat_sessions_owner ON chat_sessions';
        EXECUTE 'DROP POLICY IF EXISTS messages_owner ON messages';
        EXECUTE 'DROP POLICY IF EXISTS profiles_self ON profiles';
        EXECUTE $policy$
            CREATE POLICY chat_sessions_owner ON chat_sessions
            FOR ALL
            USING (user_id = auth.uid()::text)
            WITH CHECK (user_id = auth.uid()::text)
        $policy$;
        EXECUTE $policy$
            CREATE POLICY messages_owner ON messages
            FOR ALL
            USING (
                session_id IN (
                    SELECT id FROM chat_sessions WHERE user_id = auth.uid()::text
                )
            )
            WITH CHECK (
                session_id IN (
                    SELECT id FROM chat_sessions WHERE user_id = auth.uid()::text
                )
            )
        $policy$;
        EXECUTE $policy$
            CREATE POLICY profiles_self ON profiles
            FOR ALL
            USING (user_id = auth.uid()::text)
            WITH CHECK (user_id = auth.uid()::text)
        $policy$;
    END IF;
END $$;
