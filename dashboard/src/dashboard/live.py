"""Redis live counter reads for the dashboard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import redis


def _minute_key(minute: datetime) -> str:
    return minute.astimezone(UTC).strftime("%Y%m%d%H%M")


def edits_last_minute(client: redis.Redis) -> int:
    """Sum of edits in the current UTC minute bucket."""
    key = f"live:edits:total:{_minute_key(datetime.now(UTC))}"
    value = client.get(key)
    return int(value) if value else 0


def sparkline_last_60_minutes(client: redis.Redis) -> list[tuple[datetime, int]]:
    """Edit counts per minute for the last 60 completed UTC minutes (oldest first)."""
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    points: list[tuple[datetime, int]] = []
    for offset in range(59, -1, -1):
        minute = now - timedelta(minutes=offset)
        key = f"live:edits:total:{_minute_key(minute)}"
        value = client.get(key)
        points.append((minute, int(value) if value else 0))
    return points
