from __future__ import annotations

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from legalvault.models.research import SectionRecord
from legalvault.providers.embeddings import EmbeddingProvider, StubEmbeddingProvider
from legalvault.retrieval.hybrid import reciprocal_rank_fusion


def _pgvector(value: list[float]) -> Vector:
    return Vector(value)


def _row_to_section(row: tuple) -> SectionRecord:
    chunk_id, section_number, title, chapter, body_text, act = row[:6]
    return SectionRecord(
        chunk_id=chunk_id,
        section_number=section_number,
        title=title,
        chapter=chapter,
        text=body_text,
        act=act,
    )


class PostgresSectionCorpus:
    """BNS section store backed by Postgres + pgvector hybrid retrieval."""

    def __init__(
        self,
        conn: psycopg.Connection,
        *,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._conn = conn
        register_vector(conn)
        self._embedder = embedder or StubEmbeddingProvider()
        self._known_cache: frozenset[int] | None = None

    @classmethod
    def connect(
        cls,
        conninfo: str,
        *,
        embedder: EmbeddingProvider | None = None,
    ) -> PostgresSectionCorpus:
        conn = psycopg.connect(conninfo)
        return cls(conn, embedder=embedder)

    def close(self) -> None:
        self._conn.close()

    def get_section(self, section_number: int) -> SectionRecord | None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, section_number, title, chapter, body_text, act
                FROM bns_sections
                WHERE section_number = %s
                """,
                (section_number,),
            )
            row = cur.fetchone()
        return _row_to_section(row) if row else None

    def lookup_by_section_numbers(self, numbers: list[int]) -> list[SectionRecord]:
        if not numbers:
            return []
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, section_number, title, chapter, body_text, act
                FROM bns_sections
                WHERE section_number = ANY(%s)
                ORDER BY section_number
                """,
                (numbers,),
            )
            rows = cur.fetchall()
        by_number = {row[1]: _row_to_section(row) for row in rows}
        return [by_number[n] for n in numbers if n in by_number]

    def _keyword_search(self, query: str, limit: int) -> list[SectionRecord]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, section_number, title, chapter, body_text, act
                FROM bns_sections
                WHERE search_text @@ plainto_tsquery('english', %s)
                ORDER BY ts_rank_cd(search_text, plainto_tsquery('english', %s)) DESC
                LIMIT %s
                """,
                (query, query, limit),
            )
            rows = cur.fetchall()
        return [_row_to_section(row) for row in rows]

    def _semantic_search(self, query: str, limit: int) -> list[SectionRecord]:
        query_vec = _pgvector(self._embedder.embed_query(query))
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, section_number, title, chapter, body_text, act
                FROM bns_sections
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_vec, limit),
            )
            rows = cur.fetchall()
        return [_row_to_section(row) for row in rows]

    def hybrid_retrieve(
        self,
        query: str,
        *,
        section_numbers: list[int] | None = None,
        limit: int = 5,
    ) -> list[SectionRecord]:
        per_channel_limit = max(limit, 5)
        exact = self.lookup_by_section_numbers(section_numbers or [])
        keyword = self._keyword_search(query, per_channel_limit)
        semantic = self._semantic_search(query, per_channel_limit)
        return reciprocal_rank_fusion([exact, keyword, semantic], limit=limit)

    @property
    def known_section_numbers(self) -> frozenset[int]:
        if self._known_cache is None:
            with self._conn.cursor() as cur:
                cur.execute("SELECT section_number FROM bns_sections")
                self._known_cache = frozenset(row[0] for row in cur.fetchall())
        return self._known_cache


def ingest_section_records(
    conn: psycopg.Connection,
    records: list[SectionRecord],
    *,
    embedder: EmbeddingProvider,
) -> int:
    register_vector(conn)
    written = 0
    with conn.cursor() as cur:
        for record in records:
            chunk_id = record.chunk_id or f"BNS_{record.section_number}"
            embedding = _pgvector(embedder.embed_text(record.text))
            search_document = f"{record.title} {record.text}"
            cur.execute(
                """
                INSERT INTO bns_sections (
                    chunk_id, section_number, title, chapter, body_text, act,
                    search_text, embedding
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    to_tsvector('english', %s),
                    %s::vector
                )
                ON CONFLICT (section_number) DO UPDATE SET
                    chunk_id = EXCLUDED.chunk_id,
                    title = EXCLUDED.title,
                    chapter = EXCLUDED.chapter,
                    body_text = EXCLUDED.body_text,
                    act = EXCLUDED.act,
                    search_text = EXCLUDED.search_text,
                    embedding = EXCLUDED.embedding
                """,
                (
                    chunk_id,
                    record.section_number,
                    record.title,
                    record.chapter,
                    record.text,
                    record.act,
                    search_document,
                    embedding,
                ),
            )
            written += 1
    conn.commit()
    return written


def ingest_bns_json_file(
    conn: psycopg.Connection,
    json_path: str,
    *,
    embedder: EmbeddingProvider,
) -> int:
    from pathlib import Path

    from legalvault.corpus.gsms_b import load_bns_sections_json

    records = load_bns_sections_json(Path(json_path))
    return ingest_section_records(conn, records, embedder=embedder)
