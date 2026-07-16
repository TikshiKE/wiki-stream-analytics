"""Pipeline health checks."""

from healthchecker.checks.base import HealthCheck
from healthchecker.checks.dashboard import DashboardCheck
from healthchecker.checks.db_size import DbSizeCheck
from healthchecker.checks.freshness import FreshnessCheck
from healthchecker.checks.kafka_lag import KafkaLagCheck
from healthchecker.checks.redis_check import RedisCheck
from healthchecker.config import Settings

__all__ = [
    "DashboardCheck",
    "DbSizeCheck",
    "FreshnessCheck",
    "HealthCheck",
    "KafkaLagCheck",
    "RedisCheck",
    "build_checks",
]


def build_checks(settings: Settings) -> list[HealthCheck]:
    return [
        KafkaLagCheck(settings),
        FreshnessCheck(settings),
        RedisCheck(settings),
        DbSizeCheck(settings),
        DashboardCheck(settings),
    ]
