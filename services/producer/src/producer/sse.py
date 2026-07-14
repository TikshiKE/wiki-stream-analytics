"""Resilient SSE stream over Wikimedia EventStreams.

Yields raw event payloads forever, transparently reconnecting with Last-Event-ID
so no events are lost across disconnects (the server replays from that offset).
"""

import time
from collections.abc import Iterator

import httpx
import structlog
from httpx_sse import SSEError, connect_sse

from producer.backoff import ExponentialBackoff

log = structlog.get_logger(__name__)

RETRYABLE_ERRORS = (httpx.HTTPError, SSEError)


class EventStream:
    def __init__(
        self,
        url: str,
        user_agent: str,
        read_timeout_s: float = 60.0,
        backoff: ExponentialBackoff | None = None,
        sleep=time.sleep,
    ) -> None:
        self._url = url
        self._user_agent = user_agent
        self._timeout = httpx.Timeout(connect=10.0, read=read_timeout_s, write=10.0, pool=10.0)
        self._backoff = backoff or ExponentialBackoff()
        self._sleep = sleep
        self._last_event_id: str | None = None
        self._stopped = False
        self.reconnects = 0

    def stop(self) -> None:
        self._stopped = True

    def _headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/event-stream",
        }
        if self._last_event_id:
            headers["Last-Event-ID"] = self._last_event_id
        return headers

    def events(self) -> Iterator[str]:
        """Yield raw SSE data payloads; reconnect forever until stop() is called."""
        while not self._stopped:
            try:
                with httpx.Client(timeout=self._timeout) as client:  # noqa: SIM117
                    with connect_sse(client, "GET", self._url, headers=self._headers()) as source:
                        source.response.raise_for_status()
                        log.info("sse_connected", url=self._url, resumed=bool(self._last_event_id))
                        for sse in source.iter_sse():
                            if self._stopped:
                                return
                            # A yielded event proves the connection is healthy
                            self._backoff.reset()
                            if sse.id:
                                self._last_event_id = sse.id
                            if sse.data:
                                yield sse.data
            except RETRYABLE_ERRORS as exc:
                if self._stopped:
                    return
                self.reconnects += 1
                delay = self._backoff.next_delay()
                log.warning(
                    "sse_disconnected",
                    error=str(exc),
                    error_type=type(exc).__name__,
                    retry_in_s=round(delay, 1),
                    reconnects=self.reconnects,
                )
                self._sleep(delay)
