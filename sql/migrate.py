"""Apply numbered SQL migrations from sql/init/ idempotently."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg


def migrations_dir() -> Path:
    return Path(__file__).resolve().parent / "init"


def connect_dsn() -> str:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "wiki")
    password = os.environ.get("POSTGRES_PASSWORD", "wiki")
    db = os.environ.get("POSTGRES_DB", "wiki")
    return f"host={host} port={port} user={user} password={password} dbname={db}"


def pending_migrations(conn: psycopg.Connection) -> list[Path]:
    applied = {
        row[0] for row in conn.execute("SELECT version FROM public.schema_migrations").fetchall()
    }
    files = sorted(migrations_dir().glob("*.sql"))
    return [f for f in files if f.name not in applied]


def apply_file(conn: psycopg.Connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    conn.execute(sql)
    conn.execute(
        "INSERT INTO public.schema_migrations (version) VALUES (%s)",
        (path.name,),
    )


def main() -> int:
    files = sorted(migrations_dir().glob("*.sql"))
    if not files:
        print("No migrations found", file=sys.stderr)
        return 1

    with psycopg.connect(connect_dsn(), autocommit=False) as conn:
        # schema_migrations is created by 001_raw.sql; ensure table exists for first run
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                version text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()

        for path in pending_migrations(conn):
            print(f"Applying {path.name}...")
            apply_file(conn, path)
            conn.commit()
            print(f"Applied {path.name}")

    print("Migrations up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
