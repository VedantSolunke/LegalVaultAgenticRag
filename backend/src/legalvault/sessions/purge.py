from __future__ import annotations


def purge_stale_sessions(
    database_url: str,
    *,
    ttl_days: int,
    dry_run: bool = False,
) -> int:
    if ttl_days < 1:
        raise ValueError("ttl_days must be at least 1")

    import psycopg

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM chat_sessions
                WHERE updated_at < now() - make_interval(days => %s)
                """,
                (ttl_days,),
            )
            count = int(cur.fetchone()[0])
            if dry_run or count == 0:
                conn.rollback()
                return count
            cur.execute(
                """
                DELETE FROM chat_sessions
                WHERE updated_at < now() - make_interval(days => %s)
                """,
                (ttl_days,),
            )
        conn.commit()
    return count
