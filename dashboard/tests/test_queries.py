"""Tests for mart SQL query helpers."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from dashboard import queries


class _DictRowCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def __enter__(self) -> _DictRowCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        self.sql = sql

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def fetchone(self) -> tuple[int, ...] | None:
        return (1,)


class _FakeConnection:
    def __init__(self, rows: list[dict[str, Any]] | None = None, exists: bool = True) -> None:
        self._rows = rows or []
        self._exists = exists

    def cursor(self, row_factory=None) -> _DictRowCursor | MagicMock:
        if row_factory is None:
            mock = MagicMock()
            mock.__enter__ = MagicMock(return_value=mock)
            mock.__exit__ = MagicMock(return_value=False)
            mock.fetchone.return_value = (1,) if self._exists else None
            return mock
        return _DictRowCursor(self._rows)

    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_fetch_hourly_activity() -> None:
    conn = _FakeConnection(
        [{"hour_ts": "2026-07-16T12:00:00+00:00", "wiki": "enwiki", "edit_count": 10}]
    )
    rows = queries.fetch_hourly_activity(conn)
    assert rows[0]["wiki"] == "enwiki"
    assert rows[0]["edit_count"] == 10


def test_marts_available_false_when_missing() -> None:
    conn = _FakeConnection(exists=False)
    assert queries.marts_available(conn) is False
