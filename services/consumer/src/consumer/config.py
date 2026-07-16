"""Consumer configuration from environment variables."""

from psycopg.conninfo import make_conninfo
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_topic_events: str = "wiki.recentchange"
    kafka_consumer_group: str = "pg-writer"

    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    database_private_url: str | None = Field(default=None, validation_alias="DATABASE_PRIVATE_URL")

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
        url = self.database_url or self.database_private_url
        if url:
            return url
        return make_conninfo(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            dbname=self.postgres_db,
        )
