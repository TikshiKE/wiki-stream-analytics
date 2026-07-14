"""Postgres batch writer for the raw.recentchange table."""

from __future__ import annotations

import psycopg
import structlog

from consumer.mapper import RecentChangeRow, row_to_tuple

log = structlog.get_logger(__name__)

INSERT_SQL = """
INSERT INTO raw.recentchange (
    event_id, event_ts, wiki, domain, change_type, namespace, title,
    user_name, is_bot, is_anonymous, is_minor, comment, length_old, length_new
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (event_id, event_ts) DO NOTHING
"""


class PostgresWriter:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: psycopg.Connection | None = None

    def connect(self) -> None:
        self._conn = psycopg.connect(self._dsn, autocommit=False)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def write_batch(self, rows: list[RecentChangeRow]) -> int:
        if not rows:
            return 0
        assert self._conn is not None
        tuples = [row_to_tuple(row) for row in rows]
        with self._conn.cursor() as cur:
            cur.executemany(INSERT_SQL, tuples)
        self._conn.commit()
        return len(rows)
