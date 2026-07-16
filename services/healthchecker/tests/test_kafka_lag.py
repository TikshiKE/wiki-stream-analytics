"""Tests for Kafka lag check."""

from unittest.mock import MagicMock, patch

from healthchecker.checks.kafka_lag import KafkaLagCheck
from healthchecker.config import Settings
from healthchecker.models import CheckStatus


def test_kafka_lag_ok() -> None:
    admin = MagicMock()
    committed_tp = MagicMock()
    committed_tp.topic_partitions = [MagicMock(partition=0, offset=100)]
    future = MagicMock()
    future.result.return_value = committed_tp
    admin.list_consumer_group_offsets.return_value = {"pg-writer": future}

    consumer = MagicMock()
    topic_meta = MagicMock()
    topic_meta.error = None
    topic_meta.partitions = {0: None}
    metadata = MagicMock()
    metadata.topics = {"wiki.recentchange": topic_meta}
    consumer.list_topics.return_value = metadata
    consumer.get_watermark_offsets.return_value = (0, 150)

    check = KafkaLagCheck(Settings(), admin_client=admin)
    with patch("healthchecker.checks.kafka_lag.Consumer", return_value=consumer):
        result = check.check()
    assert result.status == CheckStatus.OK
    assert result.details["total_lag"] == 50


def test_kafka_lag_critical_when_group_missing() -> None:
    admin = MagicMock()
    admin.list_consumer_group_offsets.side_effect = RuntimeError("group not found")
    consumer = MagicMock()
    topic_meta = MagicMock()
    topic_meta.error = None
    topic_meta.partitions = {0: None}
    metadata = MagicMock()
    metadata.topics = {"wiki.recentchange": topic_meta}
    consumer.list_topics.return_value = metadata

    check = KafkaLagCheck(Settings(), admin_client=admin)
    with patch("healthchecker.checks.kafka_lag.Consumer", return_value=consumer):
        result = check.check()
    assert result.status == CheckStatus.CRITICAL
