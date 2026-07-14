"""Producer configuration, read from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    sse_url: str = "https://stream.wikimedia.org/v2/stream/recentchange"
    sse_user_agent: str = (
        "wiki-stream-analytics/0.1 "
        "(https://github.com/TikshiKE/wiki-stream-analytics; evgeny.kren.engineer@gmail.com)"
    )
    # Reconnect if the stream is silent for this long (EventStreams is never quiet for 60s)
    sse_read_timeout_s: float = 60.0

    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_topic_events: str = "wiki.recentchange"
    kafka_topic_dlq: str = "wiki.recentchange.dlq"
    events_topic_partitions: int = 3
    events_topic_retention_ms: int = 24 * 60 * 60 * 1000  # 24h

    backoff_base_s: float = 1.0
    backoff_cap_s: float = 60.0

    stats_interval_s: float = 30.0
