"""Apply numbered SQL migrations from sql/init/ idempotently."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo


def migrations_dir() -> Path:
    return Path(__file__).resolve().parent / "init"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _database_url() -> str | None:
    return os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PRIVATE_URL")


def maintenance_dbname() -> str:
    """Database used for admin connections (CREATE DATABASE, etc.)."""
    url = _database_url()
    if url:
        info = conninfo_to_dict(url)
        dbname = info.get("dbname")
        if dbname:
            return str(dbname)
    return _env("POSTGRES_DB", "wiki")


def connect_dsn(dbname: str | None = None) -> str:
    """Build psycopg conninfo from DATABASE_URL (Railway) or POSTGRES_* vars."""
    url = _database_url()
    if url:
        info = conninfo_to_dict(url)
        if dbname is not None:
            info["dbname"] = dbname
        return make_conninfo(**info)

    return make_conninfo(
        host=_env("POSTGRES_HOST", "localhost"),
        port=int(_env("POSTGRES_PORT", "5432")),
        user=_env("POSTGRES_USER", "wiki"),
        password=_env("POSTGRES_PASSWORD", "wiki"),
        dbname=dbname or _env("POSTGRES_DB", "wiki"),
    )


def log_connection_target(dbname: str | None = None) -> None:
    info = conninfo_to_dict(connect_dsn(dbname))
    print(
        "Postgres target:",
        f"host={info.get('host')}",
        f"port={info.get('port')}",
        f"dbname={info.get('dbname')}",
        f"user={info.get('user')}",
    )


def ensure_airflow_database() -> None:
    """Create airflow_meta DB if missing (idempotent)."""
    meta_db = _env("AIRFLOW_META_DB", "airflow_meta")
    admin_db = maintenance_dbname()
    with psycopg.connect(connect_dsn(dbname=admin_db), autocommit=True) as conn:
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
    log_connection_target()
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
