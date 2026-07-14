"""Kafka sink: idempotent topic creation and at-least-once event publishing."""

import structlog
from confluent_kafka import KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from producer.config import Settings
from producer.models import RecentChangeEvent

log = structlog.get_logger(__name__)


def event_message(event: RecentChangeEvent, raw: str) -> tuple[bytes, bytes]:
    """Map a validated event to a Kafka (key, value) pair.

    Key = wiki code, so all events of one wiki land in one partition (ordering per wiki).
    Value = original JSON payload untouched: the consumer decides what to extract.
    """
    return event.wiki.encode(), raw.encode()


def ensure_topics(settings: Settings) -> None:
    """Create topics if missing; existing topics are left as-is (idempotent)."""
    admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})
    existing = admin.list_topics(timeout=10).topics
    wanted = [
        NewTopic(
            settings.kafka_topic_events,
            num_partitions=settings.events_topic_partitions,
            replication_factor=1,
            config={"retention.ms": str(settings.events_topic_retention_ms)},
        ),
        NewTopic(settings.kafka_topic_dlq, num_partitions=1, replication_factor=1),
    ]
    missing = [t for t in wanted if t.topic not in existing]
    if not missing:
        return
    for topic, future in admin.create_topics(missing).items():
        try:
            future.result(timeout=30)
            log.info("topic_created", topic=topic)
        except KafkaException as exc:
            # Racing another instance is fine; anything else is fatal at startup
            if exc.args[0].code() != 36:  # TOPIC_ALREADY_EXISTS
                raise


class KafkaSink:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._producer = Producer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "acks": "all",
                "enable.idempotence": True,
                "compression.type": "lz4",
                "linger.ms": 100,
            }
        )
        self.delivered = 0
        self.delivery_errors = 0

    def _on_delivery(self, err, msg) -> None:
        if err is None:
            self.delivered += 1
        else:
            self.delivery_errors += 1
            log.error("delivery_failed", topic=msg.topic(), error=str(err))

    def send_event(self, event: RecentChangeEvent, raw: str) -> None:
        key, value = event_message(event, raw)
        self._producer.produce(
            self._settings.kafka_topic_events, value=value, key=key, on_delivery=self._on_delivery
        )

    def send_dlq(self, raw: str, reason: str) -> None:
        self._producer.produce(
            self._settings.kafka_topic_dlq,
            value=raw.encode(),
            headers={"reason": reason.encode()},
            on_delivery=self._on_delivery,
        )

    def poll(self) -> None:
        """Serve delivery callbacks; call regularly from the main loop."""
        self._producer.poll(0)

    def close(self) -> None:
        remaining = self._producer.flush(30)
        if remaining:
            log.error("flush_incomplete", undelivered=remaining)
