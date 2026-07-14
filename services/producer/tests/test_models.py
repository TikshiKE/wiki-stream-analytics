import json

import pytest
from producer.models import ParseError, parse_event

VALID_EVENT = {
    "meta": {
        "id": "b1f7a3c2-0000-4000-8000-000000000001",
        "dt": "2026-07-14T12:00:00Z",
        "domain": "en.wikipedia.org",
    },
    "type": "edit",
    "wiki": "enwiki",
    "namespace": 0,
    "title": "Prague",
    "user": "ExampleUser",
    "bot": False,
    "minor": True,
    "comment": "fixed a typo",
    "length": {"old": 1000, "new": 1010},
    "server_name": "en.wikipedia.org",
    "unknown_field": "is ignored",
}


def test_parse_valid_event() -> None:
    event = parse_event(json.dumps(VALID_EVENT))
    assert event.meta.id == VALID_EVENT["meta"]["id"]
    assert event.wiki == "enwiki"
    assert event.type == "edit"
    assert event.length is not None and event.length.new == 1010
    assert event.meta.dt.year == 2026


def test_invalid_json_raises_with_reason() -> None:
    with pytest.raises(ParseError) as exc_info:
        parse_event("{not json")
    assert exc_info.value.reason == "invalid_json"
    assert exc_info.value.raw == "{not json"


def test_non_object_payload_rejected() -> None:
    with pytest.raises(ParseError) as exc_info:
        parse_event('["a", "list"]')
    assert exc_info.value.reason == "not_an_object"


def test_event_without_meta_id_rejected() -> None:
    broken = {**VALID_EVENT, "meta": {"dt": "2026-07-14T12:00:00Z"}}
    with pytest.raises(ParseError) as exc_info:
        parse_event(json.dumps(broken))
    assert exc_info.value.reason == "schema_validation_failed"


def test_event_without_wiki_rejected() -> None:
    broken = {k: v for k, v in VALID_EVENT.items() if k != "wiki"}
    with pytest.raises(ParseError) as exc_info:
        parse_event(json.dumps(broken))
    assert exc_info.value.reason == "schema_validation_failed"
