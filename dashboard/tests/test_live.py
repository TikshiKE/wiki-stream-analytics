"""Tests for Redis live counter reads."""

from datetime import UTC, datetime

import fakeredis
from dashboard.live import edits_last_minute, sparkline_last_60_minutes


def test_edits_last_minute_reads_total_key() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    minute = datetime(2026, 7, 16, 14, 30, tzinfo=UTC).strftime("%Y%m%d%H%M")
    client.set(f"live:edits:total:{minute}", 42)

    class FixedNow:
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 7, 16, 14, 30, 15, tzinfo=UTC)

    import dashboard.live as live_mod

    original = live_mod.datetime
    live_mod.datetime = FixedNow
    try:
        assert edits_last_minute(client) == 42
    finally:
        live_mod.datetime = original


def test_sparkline_returns_60_points() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    points = sparkline_last_60_minutes(client)
    assert len(points) == 60
    assert all(count >= 0 for _, count in points)
