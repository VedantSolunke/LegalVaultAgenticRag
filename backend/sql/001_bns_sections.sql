-- BNS section records with pgvector embeddings (GSMS-B ingest only; no QA JSONL).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS bns_sections (
    chunk_id TEXT PRIMARY KEY,
    section_number INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    chapter TEXT NOT NULL,
    body_text TEXT NOT NULL,
    act TEXT NOT NULL DEFAULT 'BNS',
    search_text TSVECTOR,
    embedding vector(768)
);

CREATE INDEX IF NOT EXISTS bns_sections_section_number_idx ON bns_sections (section_number);
CREATE INDEX IF NOT EXISTS bns_sections_search_text_idx ON bns_sections USING gin (search_text);
