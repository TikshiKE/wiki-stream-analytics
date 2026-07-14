"""Consumer configuration from environment variables."""

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

    batch_size: int = 500
    batch_timeout_s: float = 5.0
    dedup_ttl_s: int = 3600
    live_counter_ttl_s: int = 7200

    stats_interval_s: float = 30.0

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"user={self.postgres_user} password={self.postgres_password} "
            f"dbname={self.postgres_db}"
        )
