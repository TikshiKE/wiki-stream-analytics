"""Redis availability and live counter check."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import redis

from healthchecker.checks.base import HealthCheck
from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus


class RedisCheck(HealthCheck):
    def __init__(self, settings: Settings, client: redis.Redis | None = None) -> None:
        self._settings = settings
        self._client = client

    @property
    def name(self) -> str:
        return "redis"

    def check(self) -> CheckResult:
        client = self._client or redis.from_url(self._settings.redis_url, decode_responses=True)
        try:
            if client.ping() is not True:
                return CheckResult(CheckStatus.CRITICAL, {"error": "redis ping failed"})
        except redis.RedisError as exc:
            return CheckResult(CheckStatus.CRITICAL, {"error": str(exc)})

        now = datetime.now(UTC).replace(second=0, microsecond=0)
        lookback = self._settings.redis_live_lookback_minutes
        hits = 0
        for offset in range(lookback):
            minute = now - timedelta(minutes=offset)
            key = f"live:edits:total:{minute.strftime('%Y%m%d%H%M')}"
            value = client.get(key)
            if value and int(value) > 0:
                hits += 1

        details = {"live_minutes_with_data": hits, "lookback_minutes": lookback}
        if hits == 0:
            return CheckResult(CheckStatus.CRITICAL, details)
        return CheckResult(CheckStatus.OK, details)
