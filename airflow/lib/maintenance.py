"""Maintenance tasks invoked by Airflow DAGs (Postgres operations)."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import psycopg2

from lib.dq import evaluate_freshness, evaluate_volume
from lib.partitions import (
    create_partition_sql,
    drop_partition_sql,
    parse_partition_date,
    partitions_to_create,
    should_drop_partition,
)


def _connect():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "wiki"),
        password=os.environ.get("POSTGRES_PASSWORD", "wiki"),
        dbname=os.environ.get("POSTGRES_DB", "wiki"),
    )


def create_raw_partitions(days_ahead: int = 3) -> int:
    today = datetime.now(UTC).date()
    created = 0
    with _connect() as conn:
        with conn.cursor() as cur:
            for day in partitions_to_create(today, days_ahead):
                cur.execute(create_partition_sql(day))
                created += 1
        conn.commit()
    return created


def drop_old_partitions(retention_days: int | None = None) -> int:
    today = datetime.now(UTC).date()
    retention = retention_days or int(os.environ.get("RETENTION_DAYS", "7"))
    dropped = 0
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT child.relname
                FROM pg_inherits inh
                JOIN pg_class parent ON parent.oid = inh.inhparent
                JOIN pg_class child ON child.oid = inh.inhrelid
                JOIN pg_namespace ns ON ns.oid = parent.relnamespace
                WHERE ns.nspname = 'raw' AND parent.relname = 'recentchange'
                """
            )
            for (relname,) in cur.fetchall():
                part_day = parse_partition_date(relname)
                if part_day and should_drop_partition(part_day, today, retention):
                    cur.execute(drop_partition_sql(part_day))
                    dropped += 1
        conn.commit()
    return dropped


def vacuum_marts() -> None:
    tables = [
        "marts.dim_wiki",
        "marts.fct_edits",
        "marts.agg_edits_hourly",
        "marts.mart_top_pages_daily",
        "marts.mart_editor_activity_daily",
    ]
    conn = _connect()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f"VACUUM ANALYZE {table}")
    finally:
        conn.close()


def check_freshness(max_age_minutes: int = 10) -> str:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT max(event_ts) FROM raw.recentchange")
        max_ts = cur.fetchone()[0]
    ok, message = evaluate_freshness(max_ts, datetime.now(UTC), max_age_minutes)
    if not ok:
        raise ValueError(message)
    return message


def check_volume(tolerance: float = 0.6) -> str:
    sql = """
        WITH daily AS (
            SELECT date_trunc('day', event_ts)::date AS d, count(*)::int AS cnt
            FROM raw.recentchange
            WHERE event_ts >= current_date - interval '8 days'
            GROUP BY 1
        )
        SELECT
            (SELECT cnt FROM daily WHERE d = current_date - 1) AS yesterday,
            (SELECT avg(cnt) FROM daily
             WHERE d BETWEEN current_date - 8 AND current_date - 2) AS avg_7d
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        yesterday, avg_7d = cur.fetchone()
    ok, message = evaluate_volume(yesterday, float(avg_7d) if avg_7d else None, tolerance)
    if not ok:
        raise ValueError(message)
    return message
