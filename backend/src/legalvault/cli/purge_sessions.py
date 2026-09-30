"""CLI: purge chat sessions past TTL (ADR-0008)."""

from __future__ import annotations

import argparse
import sys

from legalvault.config import get_settings
from legalvault.sessions.purge import purge_stale_sessions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Delete chat sessions (and messages) inactive longer than the TTL. "
            "Schedule via cron or a container sidecar."
        )
    )
    parser.add_argument(
        "--database-url",
        help="Postgres URL (default: LEGALVAULT_DATABASE_URL)",
    )
    parser.add_argument(
        "--ttl-days",
        type=int,
        help="Inactive session TTL in days (default: LEGALVAULT_SESSION_TTL_DAYS or 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many sessions would be deleted without deleting",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = get_settings()
    database_url = args.database_url or settings.database_url
    if database_url is None:
        print("Missing --database-url or LEGALVAULT_DATABASE_URL", file=sys.stderr)
        return 1

    ttl_days = args.ttl_days if args.ttl_days is not None else settings.session_ttl_days
    deleted = purge_stale_sessions(
        database_url,
        ttl_days=ttl_days,
        dry_run=args.dry_run,
    )
    action = "would delete" if args.dry_run else "deleted"
    print(f"{action} {deleted} stale chat session(s) (ttl_days={ttl_days})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
