import json

from producer.kafka_sink import event_message
from producer.models import parse_event


def test_event_message_key_is_wiki_and_value_is_raw_payload() -> None:
    raw = json.dumps(
        {
            "meta": {"id": "b1f7a3c2-0000-4000-8000-000000000001", "dt": "2026-07-14T12:00:00Z"},
            "type": "edit",
            "wiki": "ruwiki",
        }
    )
    event = parse_event(raw)

    key, value = event_message(event, raw)

    assert key == b"ruwiki"
    # The consumer receives the original payload untouched
    assert json.loads(value.decode()) == json.loads(raw)
