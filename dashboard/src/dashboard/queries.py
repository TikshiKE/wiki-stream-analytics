"""Postgres queries against dbt mart tables (read-only)."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

HOURLY_ACTIVITY_SQL = """
    SELECT hour_ts, wiki, edit_count::bigint AS edit_count
    FROM marts.agg_edits_hourly
    WHERE hour_ts >= now() AT TIME ZONE 'utc' - interval '7 days'
    ORDER BY hour_ts, wiki
"""

EDITOR_ACTIVITY_SQL = """
    SELECT edit_date, editor_type, edit_count::bigint AS edit_count
    FROM marts.mart_editor_activity_daily
    WHERE edit_date >= current_date - interval '30 days'
    ORDER BY edit_date, editor_type
"""

TOP_PAGES_TODAY_SQL = """
    SELECT wiki, title, edit_count::bigint AS edit_count
    FROM marts.mart_top_pages_daily
    WHERE edit_date = current_date
    ORDER BY edit_count DESC
    LIMIT 20
"""


def fetch_hourly_activity(conn: psycopg.Connection) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(HOURLY_ACTIVITY_SQL)
        return list(cur.fetchall())


def fetch_editor_activity(conn: psycopg.Connection) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(EDITOR_ACTIVITY_SQL)
        return list(cur.fetchall())


def fetch_top_pages_today(conn: psycopg.Connection) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(TOP_PAGES_TODAY_SQL)
        return list(cur.fetchall())


def table_exists(conn: psycopg.Connection, schema: str, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        return cur.fetchone() is not None


def marts_available(conn: psycopg.Connection) -> bool:
    return table_exists(conn, "marts", "agg_edits_hourly")
