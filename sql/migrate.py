"""Apply numbered SQL migrations from sql/init/ idempotently."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql


def migrations_dir() -> Path:
    return Path(__file__).resolve().parent / "init"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def connect_dsn(dbname: str | None = None) -> str:
    host = _env("POSTGRES_HOST", "localhost")
    port = _env("POSTGRES_PORT", "5432")
    user = _env("POSTGRES_USER", "wiki")
    password = _env("POSTGRES_PASSWORD", "wiki")
    db = dbname or _env("POSTGRES_DB", "wiki")
    return f"host={host} port={port} user={user} password={password} dbname={db}"


def ensure_airflow_database() -> None:
    """Create airflow_meta DB if missing (idempotent)."""
    meta_db = _env("AIRFLOW_META_DB", "airflow_meta")
    with psycopg.connect(connect_dsn(dbname="postgres"), autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (meta_db,)).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(meta_db)))
            print(f"Created database {meta_db}")


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
    ensure_airflow_database()

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
            if path.name == "002_airflow_meta.sql":
                ensure_airflow_database()
            apply_file(conn, path)
            conn.commit()
            print(f"Applied {path.name}")

    print("Migrations up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
