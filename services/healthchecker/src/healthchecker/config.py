"""Healthchecker configuration from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_topic_events: str = "wiki.recentchange"
    kafka_consumer_group: str = "pg-writer"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "wiki"
    postgres_password: str = "wiki"
    postgres_db: str = "wiki"

    redis_url: str = "redis://localhost:6379/0"
    dashboard_url: str = "http://localhost:8501"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    check_interval_seconds: int = 60
    alert_throttle_seconds: int = 1800

    kafka_lag_warn: int = 10_000
    kafka_lag_critical: int = 50_000

    freshness_warn_minutes: int = 5
    freshness_critical_minutes: int = 15

    redis_live_lookback_minutes: int = 5

    db_size_warn_bytes: int = 10 * 1024**3  # 10 GiB

    health_host: str = "0.0.0.0"
    health_port: int = 8090

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"user={self.postgres_user} password={self.postgres_password} "
            f"dbname={self.postgres_db}"
        )
