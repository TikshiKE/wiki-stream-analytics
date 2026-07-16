"""Database size check."""

from __future__ import annotations

import psycopg

from healthchecker.checks.base import HealthCheck
from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus


class DbSizeCheck(HealthCheck):
    def __init__(self, settings: Settings, connection: psycopg.Connection | None = None) -> None:
        self._settings = settings
        self._connection = connection

    @property
    def name(self) -> str:
        return "db_size"

    def check(self) -> CheckResult:
        try:
            if self._connection is not None:
                size_bytes = self._query_size(self._connection)
            else:
                with psycopg.connect(self._settings.postgres_dsn) as conn:
                    size_bytes = self._query_size(conn)
        except psycopg.Error as exc:
            return CheckResult(CheckStatus.CRITICAL, {"error": str(exc)})

        details = {
            "database": self._settings.postgres_db,
            "size_bytes": size_bytes,
            "size_gb": round(size_bytes / (1024**3), 2),
            "warn_threshold_bytes": self._settings.db_size_warn_bytes,
        }
        if size_bytes > self._settings.db_size_warn_bytes:
            return CheckResult(CheckStatus.WARN, details)
        return CheckResult(CheckStatus.OK, details)

    def _query_size(self, conn: psycopg.Connection) -> int:
        row = conn.execute(
            "SELECT pg_database_size(%s)",
            (self._settings.postgres_db,),
        ).fetchone()
        return int(row[0])
