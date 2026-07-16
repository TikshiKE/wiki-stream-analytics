"""Raw table freshness check."""

from __future__ import annotations

from datetime import UTC, datetime

import psycopg

from healthchecker.checks.base import HealthCheck
from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus


class FreshnessCheck(HealthCheck):
    def __init__(self, settings: Settings, connection: psycopg.Connection | None = None) -> None:
        self._settings = settings
        self._connection = connection

    @property
    def name(self) -> str:
        return "freshness"

    def check(self) -> CheckResult:
        try:
            if self._connection is not None:
                max_ts = self._query_max_ts(self._connection)
            else:
                with psycopg.connect(self._settings.postgres_dsn) as conn:
                    max_ts = self._query_max_ts(conn)
        except psycopg.Error as exc:
            return CheckResult(CheckStatus.CRITICAL, {"error": str(exc)})

        if max_ts is None:
            return CheckResult(CheckStatus.CRITICAL, {"error": "no rows in raw.recentchange"})

        if max_ts.tzinfo is None:
            max_ts = max_ts.replace(tzinfo=UTC)
        age_seconds = (datetime.now(UTC) - max_ts).total_seconds()
        age_minutes = age_seconds / 60
        details = {
            "max_event_ts": max_ts.isoformat(),
            "age_minutes": round(age_minutes, 2),
        }

        if age_minutes > self._settings.freshness_critical_minutes:
            return CheckResult(CheckStatus.CRITICAL, details)
        if age_minutes > self._settings.freshness_warn_minutes:
            return CheckResult(CheckStatus.WARN, details)
        return CheckResult(CheckStatus.OK, details)

    @staticmethod
    def _query_max_ts(conn: psycopg.Connection) -> datetime | None:
        row = conn.execute("SELECT max(event_ts) FROM raw.recentchange").fetchone()
        return row[0] if row else None
