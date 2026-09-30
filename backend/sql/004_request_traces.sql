-- Per-request debug traces (ADR-0008, ADR-0009).

CREATE TABLE IF NOT EXISTS request_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    session_id UUID REFERENCES chat_sessions (id) ON DELETE SET NULL,
    trace JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS request_traces_user_id_idx ON request_traces (user_id);
CREATE INDEX IF NOT EXISTS request_traces_created_at_idx ON request_traces (created_at DESC);

ALTER TABLE request_traces ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
        EXECUTE 'DROP POLICY IF EXISTS request_traces_admin_read ON request_traces';
        EXECUTE $policy$
            CREATE POLICY request_traces_admin_read ON request_traces
            FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM profiles
                    WHERE profiles.user_id = auth.uid()::text
                      AND profiles.is_admin = TRUE
                )
            )
        $policy$;
    END IF;
END $$;
