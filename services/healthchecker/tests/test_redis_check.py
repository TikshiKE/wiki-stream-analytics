"""Tests for Redis check."""

from datetime import UTC, datetime

import fakeredis
from healthchecker.checks.redis_check import RedisCheck
from healthchecker.config import Settings
from healthchecker.models import CheckStatus


def test_redis_ok_with_recent_counters() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    minute = datetime.now(UTC).strftime("%Y%m%d%H%M")
    client.set(f"live:edits:total:{minute}", 5)
    check = RedisCheck(Settings(redis_live_lookback_minutes=5), client=client)
    assert check.check().status == CheckStatus.OK


def test_redis_critical_without_counters() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    check = RedisCheck(Settings(redis_live_lookback_minutes=5), client=client)
    assert check.check().status == CheckStatus.CRITICAL
