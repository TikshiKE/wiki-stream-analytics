"""Tests for event -> row mapping."""

from datetime import UTC, datetime
from uuid import UUID

from conftest import SAMPLE_EDIT
from consumer.mapper import (
    is_anonymous_user,
    parse_payload,
    row_from_payload,
    row_to_tuple,
    should_persist,
)


def test_should_persist_only_edit_and_new() -> None:
    assert should_persist("edit")
    assert should_persist("new")
    assert not should_persist("log")


def test_is_anonymous_user_detects_ip() -> None:
    assert is_anonymous_user("127.0.0.1")
    assert is_anonymous_user("2001:db8::1")
    assert not is_anonymous_user("ExampleEditor")


def test_row_from_payload_maps_fields() -> None:
    payload = parse_payload(SAMPLE_EDIT)
    row = row_from_payload(payload)
    assert row.event_id == UUID("550e8400-e29b-41d4-a716-446655440000")
    assert row.event_ts == datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    assert row.wiki == "enwiki"
    assert row.is_anonymous is True
    assert row.length_new == 105


def test_row_to_tuple_has_fourteen_values() -> None:
    row = row_from_payload(parse_payload(SAMPLE_EDIT))
    assert len(row_to_tuple(row)) == 14
