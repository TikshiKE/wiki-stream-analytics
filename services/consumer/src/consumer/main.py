"""Consumer entrypoint: Kafka -> dedup -> Postgres raw layer + Redis live counters."""

from __future__ import annotations

import logging
import signal
import time

import redis
import structlog
from confluent_kafka import Consumer, KafkaError, KafkaException, TopicPartition

from consumer.batch import BatchBuffer, BufferedMessage
from consumer.config import Settings
from consumer.mapper import parse_payload, row_from_payload, should_persist
from consumer.pg_writer import PostgresWriter
from consumer.redis_store import DedupStore, LiveCounters

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


class WikiConsumer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stopped = False
        self._buffer = BatchBuffer(settings.batch_size, settings.batch_timeout_s)
        self._pending_offsets: dict[int, int] = {}
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._dedup = DedupStore(self._redis, settings.dedup_ttl_s)
        self._counters = LiveCounters(self._redis, settings.live_counter_ttl_s)
        self._pg = PostgresWriter(settings.postgres_dsn)
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "group.id": settings.kafka_consumer_group,
                "enable.auto.commit": False,
                "auto.offset.reset": "earliest",
            }
        )

        self.consumed = 0
        self.written = 0
        self.filtered = 0
        self.deduped = 0
        self.parse_errors = 0

    def stop(self) -> None:
        self._stopped = True

    def _track_offset(self, partition: int, offset: int) -> None:
        current = self._pending_offsets.get(partition)
        if current is None or offset > current:
            self._pending_offsets[partition] = offset

    def _commit_offsets(self) -> None:
        if not self._pending_offsets:
            return
        commits = [
            TopicPartition(
                self._settings.kafka_topic_events,
                partition,
                offset + 1,
            )
            for partition, offset in self._pending_offsets.items()
        ]
        self._consumer.commit(offsets=commits, asynchronous=False)
        self._pending_offsets.clear()

    def _flush(self) -> None:
        rows = [item.row for item in self._buffer.drain()]
        if rows:
            self._pg.write_batch(rows)
            self._counters.increment_many(rows)
            self.written += len(rows)
        self._commit_offsets()

    def _handle_message(self, msg) -> None:
        self.consumed += 1
        self._track_offset(msg.partition(), msg.offset())
        raw = msg.value().decode("utf-8")
        try:
            payload = parse_payload(raw)
            row = row_from_payload(payload)
        except (ValueError, KeyError, TypeError) as exc:
            self.parse_errors += 1
            log.warning(
                "parse_failed", error=str(exc), partition=msg.partition(), offset=msg.offset()
            )
            return

        if not should_persist(row.change_type):
            self.filtered += 1
            return

        if self._dedup.is_duplicate(str(row.event_id)):
            self.deduped += 1
            return

        self._buffer.add(BufferedMessage(row=row, partition=msg.partition(), offset=msg.offset()))

    def run(self) -> None:
        self._pg.connect()
        self._dedup.ping()
        self._consumer.subscribe([self._settings.kafka_topic_events])
        log.info(
            "consumer_started",
            topic=self._settings.kafka_topic_events,
            group=self._settings.kafka_consumer_group,
        )

        last_report = time.monotonic()
        try:
            while not self._stopped:
                msg = self._consumer.poll(1.0)
                if msg is None:
                    if self._buffer.should_flush():
                        self._flush()
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())
                self._handle_message(msg)
                if self._buffer.should_flush():
                    self._flush()

                now = time.monotonic()
                if now - last_report >= self._settings.stats_interval_s:
                    log.info(
                        "stats",
                        consumed=self.consumed,
                        written=self.written,
                        filtered=self.filtered,
                        deduped=self.deduped,
                        parse_errors=self.parse_errors,
                        buffer=len(self._buffer),
                    )
                    self.consumed = 0
                    self.written = 0
                    self.filtered = 0
                    self.deduped = 0
                    self.parse_errors = 0
                    last_report = now
        finally:
            if len(self._buffer) or self._pending_offsets:
                self._flush()
            self._consumer.close()
            self._pg.close()
            log.info("consumer_stopped")


def run() -> None:
    setup_logging()
    settings = Settings()
    app = WikiConsumer(settings)

    def shutdown(signum, frame) -> None:
        log.info("shutdown_requested", signal=signum)
        app.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    app.run()


if __name__ == "__main__":
    run()
