"""
Application configuration.

Centralizes all environment-driven settings using pydantic-settings, which
validates types on startup. Anything we'd want different per-environment
(local vs k8s) lives here, never hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic-settings automatically reads from environment variables.
    # Field names are case-insensitive: REDIS_HOST env var -> redis_host attr.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Service identity (shown in /health for debugging which pod responded)
    service_name: str = "financial-platform-backend"

    # Redis connection - defaults work for local docker-compose-style networking,
    # overridden in k8s via the ConfigMap.
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Whether to actually connect to Redis. False means use an in-memory fallback,
    # which is useful for stub/dev mode before Redis is wired in.
    use_redis: bool = False


# Single shared instance, imported wherever config is needed.
settings = Settings()