"""Producer entrypoint: SSE stream -> validate -> Kafka (events or DLQ)."""

import logging
import signal
import time

import structlog

from producer.backoff import ExponentialBackoff
from producer.config import Settings
from producer.kafka_sink import KafkaSink, ensure_topics
from producer.models import ParseError, parse_event
from producer.sse import EventStream

log = structlog.get_logger(__name__)


def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


def run() -> None:
    setup_logging()
    settings = Settings()
    ensure_topics(settings)

    stream = EventStream(
        url=settings.sse_url,
        user_agent=settings.sse_user_agent,
        read_timeout_s=settings.sse_read_timeout_s,
        backoff=ExponentialBackoff(base=settings.backoff_base_s, cap=settings.backoff_cap_s),
    )
    sink = KafkaSink(settings)

    def shutdown(signum, frame) -> None:
        log.info("shutdown_requested", signal=signum)
        stream.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    received = 0
    parse_errors = 0
    last_report = time.monotonic()

    log.info("producer_started", sse_url=settings.sse_url, topic=settings.kafka_topic_events)
    for raw in stream.events():
        received += 1
        try:
            event = parse_event(raw)
            sink.send_event(event, raw)
        except ParseError as exc:
            parse_errors += 1
            sink.send_dlq(raw, exc.reason)
        sink.poll()

        now = time.monotonic()
        if now - last_report >= settings.stats_interval_s:
            log.info(
                "stats",
                received=received,
                delivered=sink.delivered,
                delivery_errors=sink.delivery_errors,
                parse_errors=parse_errors,
                reconnects=stream.reconnects,
                rate_per_s=round(received / (now - last_report), 1),
            )
            received = 0
            parse_errors = 0
            last_report = now

    sink.close()
    log.info("producer_stopped")


if __name__ == "__main__":
    run()
