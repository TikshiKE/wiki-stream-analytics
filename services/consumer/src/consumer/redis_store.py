"""Redis deduplication and live edit counters."""

from __future__ import annotations

from datetime import UTC

import redis
import structlog

from consumer.mapper import RecentChangeRow

log = structlog.get_logger(__name__)


class DedupStore:
    def __init__(self, client: redis.Redis, ttl_s: int) -> None:
        self._client = client
        self._ttl_s = ttl_s
        self._available = True

    @property
    def available(self) -> bool:
        return self._available

    def is_duplicate(self, event_id: str) -> bool:
        if not self._available:
            return False
        key = f"dedup:{event_id}"
        try:
            created = self._client.set(key, "1", nx=True, ex=self._ttl_s)
            return created is None
        except redis.RedisError as exc:
            self._available = False
            log.warning("redis_dedup_unavailable", error=str(exc))
            return False

    def ping(self) -> bool:
        try:
            self._client.ping()
            self._available = True
            return True
        except redis.RedisError:
            self._available = False
            return False


class LiveCounters:
    def __init__(self, client: redis.Redis, ttl_s: int) -> None:
        self._client = client
        self._ttl_s = ttl_s
        self._available = True

    def increment(self, row: RecentChangeRow) -> None:
        if not self._available:
            return
        minute = row.event_ts.astimezone(UTC).strftime("%Y%m%d%H%M")
        keys = (f"live:edits:total:{minute}", f"live:edits:{row.wiki}:{minute}")
        try:
            pipe = self._client.pipeline()
            for key in keys:
                pipe.incr(key)
                pipe.expire(key, self._ttl_s)
            pipe.execute()
        except redis.RedisError as exc:
            self._available = False
            log.warning("redis_counters_unavailable", error=str(exc))

    def increment_many(self, rows: list[RecentChangeRow]) -> None:
        for row in rows:
            self.increment(row)
