-- IPC→BNS mapping records (structured lookup only; no embeddings).
CREATE TABLE IF NOT EXISTS ipc_mappings (
    ipc_section_number INTEGER PRIMARY KEY,
    bns_section_numbers INTEGER[] NOT NULL,
    mapping_source TEXT NOT NULL,
    ipc_title TEXT,
    bns_title TEXT
);

CREATE INDEX IF NOT EXISTS ipc_mappings_bns_gin_idx
    ON ipc_mappings USING gin (bns_section_numbers);
