"""Tests for Redis deduplication."""

import fakeredis
from conftest import SAMPLE_MINIMAL
from consumer.mapper import parse_payload, row_from_payload
from consumer.redis_store import DedupStore, LiveCounters


def test_dedup_rejects_second_event_with_same_id() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    store = DedupStore(client, ttl_s=3600)
    event_id = "550e8400-e29b-41d4-a716-446655440000"
    assert store.is_duplicate(event_id) is False
    assert store.is_duplicate(event_id) is True


def test_live_counters_increment_keys() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    counters = LiveCounters(client, ttl_s=7200)
    row = row_from_payload(parse_payload(SAMPLE_MINIMAL))
    counters.increment(row)
    assert client.get("live:edits:total:202607141200") == "1"
    assert client.get("live:edits:enwiki:202607141200") == "1"
