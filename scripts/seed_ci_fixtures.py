"""Apply CI seed fixtures to raw.recentchange (idempotent)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg


def connect_dsn() -> str:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "wiki")
    password = os.environ.get("POSTGRES_PASSWORD", "wiki")
    db = os.environ.get("POSTGRES_DB", "wiki")
    return f"host={host} port={port} user={user} password={password} dbname={db}"


def main() -> int:
    fixture = Path(__file__).resolve().parents[1] / "sql" / "fixtures" / "ci_seed.sql"
    if not fixture.exists():
        print(f"Fixture not found: {fixture}", file=sys.stderr)
        return 1

    sql = fixture.read_text(encoding="utf-8")
    with psycopg.connect(connect_dsn(), autocommit=True) as conn:
        conn.execute(sql)
    print(f"Applied {fixture.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
