"""Micro-batch buffer for Kafka messages."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from consumer.mapper import RecentChangeRow


@dataclass
class BufferedMessage:
    row: RecentChangeRow
    partition: int
    offset: int


@dataclass
class BatchBuffer:
    max_size: int
    max_wait_s: float
    _items: list[BufferedMessage] = field(default_factory=list)
    _opened_at: float = field(default_factory=time.monotonic)

    def add(self, item: BufferedMessage) -> None:
        self._items.append(item)

    def should_flush(self) -> bool:
        if not self._items:
            return False
        if len(self._items) >= self.max_size:
            return True
        return (time.monotonic() - self._opened_at) >= self.max_wait_s

    def drain(self) -> list[BufferedMessage]:
        items = self._items
        self._items = []
        self._opened_at = time.monotonic()
        return items

    def __len__(self) -> int:
        return len(self._items)
