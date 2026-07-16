"""Kafka consumer group lag check."""

from __future__ import annotations

from confluent_kafka import Consumer, ConsumerGroupTopicPartitions, TopicPartition
from confluent_kafka.admin import AdminClient

from healthchecker.checks.base import HealthCheck
from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus


class KafkaLagCheck(HealthCheck):
    def __init__(self, settings: Settings, admin_client: AdminClient | None = None) -> None:
        self._settings = settings
        self._admin = admin_client

    @property
    def name(self) -> str:
        return "kafka_lag"

    def check(self) -> CheckResult:
        settings = self._settings
        admin = self._admin or AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})
        consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "group.id": "healthchecker-lag-probe",
                "enable.auto.commit": False,
            }
        )
        try:
            metadata = consumer.list_topics(settings.kafka_topic_events, timeout=10)
            topic_meta = metadata.topics.get(settings.kafka_topic_events)
            if topic_meta is None or topic_meta.error is not None:
                return CheckResult(
                    CheckStatus.CRITICAL,
                    {"error": f"topic {settings.kafka_topic_events} not found"},
                )

            partitions = [
                TopicPartition(settings.kafka_topic_events, partition_id)
                for partition_id in topic_meta.partitions
            ]
            try:
                futures = admin.list_consumer_group_offsets(
                    [ConsumerGroupTopicPartitions(settings.kafka_consumer_group, partitions)],
                    request_timeout=10,
                )
                committed = futures[settings.kafka_consumer_group].result(timeout=10)
            except Exception as exc:
                return CheckResult(
                    CheckStatus.CRITICAL,
                    {"error": f"consumer group missing or unreachable: {exc}"},
                )

            total_lag = 0
            per_partition: dict[int, int] = {}
            for tp in committed.topic_partitions:
                _, high = consumer.get_watermark_offsets(tp, timeout=10)
                offset = tp.offset if tp.offset >= 0 else 0
                lag = max(0, high - offset)
                per_partition[tp.partition] = lag
                total_lag += lag

            details = {
                "group": settings.kafka_consumer_group,
                "topic": settings.kafka_topic_events,
                "total_lag": total_lag,
                "partitions": per_partition,
            }
            if total_lag > settings.kafka_lag_critical:
                return CheckResult(CheckStatus.CRITICAL, details)
            if total_lag > settings.kafka_lag_warn:
                return CheckResult(CheckStatus.WARN, details)
            return CheckResult(CheckStatus.OK, details)
        finally:
            consumer.close()
