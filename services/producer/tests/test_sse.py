"""Reconnect behaviour of EventStream with a mocked SSE transport."""

from contextlib import contextmanager
from types import SimpleNamespace

import httpx
import producer.sse as sse_module
from producer.backoff import ExponentialBackoff
from producer.sse import EventStream


class FakeSSEvent(SimpleNamespace):
    pass


class FakeSource:
    """One SSE connection: yields given events, then raises to simulate a drop."""

    def __init__(self, events: list[FakeSSEvent], error: Exception | None):
        self._events = events
        self._error = error
        self.response = SimpleNamespace(raise_for_status=lambda: None)

    def iter_sse(self):
        yield from self._events
        if self._error is not None:
            raise self._error


def test_reconnects_and_resumes_with_last_event_id(monkeypatch) -> None:
    seen_headers: list[dict] = []
    first = FakeSource(
        [FakeSSEvent(id='["offset-1"]', data='{"a": 1}')], httpx.ReadError("connection lost")
    )
    second = FakeSource([FakeSSEvent(id='["offset-2"]', data='{"a": 2}')], None)

    stream = EventStream(
        url="http://test/stream",
        user_agent="test-agent",
        backoff=ExponentialBackoff(base=0.0, cap=0.0, jitter=0.0),
        sleep=lambda _: None,
    )
    pending = [first, second]

    @contextmanager
    def fake_connect_sse(client, method, url, headers):
        seen_headers.append(dict(headers))
        yield pending.pop(0)

    monkeypatch.setattr(sse_module, "connect_sse", fake_connect_sse)

    received: list[str] = []
    for data in stream.events():
        received.append(data)
        if len(received) == 2:
            stream.stop()

    assert received == ['{"a": 1}', '{"a": 2}']
    assert stream.reconnects == 1
    # First connection: no resume header; second: resumes from the last seen event id
    assert "Last-Event-ID" not in seen_headers[0]
    assert seen_headers[1]["Last-Event-ID"] == '["offset-1"]'
    assert seen_headers[1]["User-Agent"] == "test-agent"


def test_stop_terminates_the_generator(monkeypatch) -> None:
    source = FakeSource(
        [FakeSSEvent(id=None, data='{"a": 1}'), FakeSSEvent(id=None, data='{"a": 2}')], None
    )

    stream = EventStream(
        url="http://test/stream",
        user_agent="test-agent",
        backoff=ExponentialBackoff(base=0.0, cap=0.0, jitter=0.0),
        sleep=lambda _: None,
    )

    @contextmanager
    def fake_connect_sse(client, method, url, headers):
        yield source

    monkeypatch.setattr(sse_module, "connect_sse", fake_connect_sse)

    received = []
    for data in stream.events():
        received.append(data)
        stream.stop()

    assert received == ['{"a": 1}']
