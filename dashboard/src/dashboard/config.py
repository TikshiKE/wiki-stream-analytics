"""Dashboard configuration from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "wiki"
    postgres_ro_user: str = "wiki_ro"
    postgres_ro_password: str = "wiki_ro"
    redis_url: str = "redis://localhost:6379/0"
    github_repo_url: str = "https://github.com/TikshiKE/wiki-stream-analytics"
    live_refresh_seconds: int = 10

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_ro_user} "
            f"password={self.postgres_ro_password}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
