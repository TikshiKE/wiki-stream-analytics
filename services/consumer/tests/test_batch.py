"""Tests for micro-batch buffer."""

from conftest import SAMPLE_MINIMAL
from consumer.batch import BatchBuffer, BufferedMessage
from consumer.mapper import parse_payload, row_from_payload


def _item() -> BufferedMessage:
    row = row_from_payload(parse_payload(SAMPLE_MINIMAL))
    return BufferedMessage(row=row, partition=0, offset=0)


def test_flush_by_size() -> None:
    buf = BatchBuffer(max_size=2, max_wait_s=60.0)
    buf.add(_item())
    assert not buf.should_flush()
    buf.add(_item())
    assert buf.should_flush()
    assert len(buf.drain()) == 2


def test_flush_by_timeout(monkeypatch) -> None:
    buf = BatchBuffer(max_size=100, max_wait_s=0.05)
    buf._opened_at = 1000.0
    monkeypatch.setattr("consumer.batch.time.monotonic", lambda: 1000.06)
    buf.add(_item())
    assert buf.should_flush()
