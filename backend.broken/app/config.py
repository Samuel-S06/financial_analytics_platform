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

    # Redis connection - defaults work for local dev with `redis-server`
    # running on the host. In k8s this is overridden via the ConfigMap to
    # point at the Redis Service.
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Whether to use Redis for the job store. False falls back to an
    # in-memory dict, which is convenient for tests but breaks across
    # multiple replicas. Defaults to True so production-shaped deployments
    # work out of the box; tests override via fixture.
    use_redis: bool = True

    # How long to keep job records around in Redis. 24h is plenty for a
    # demo - prevents Redis from filling up with old jobs forever.
    job_ttl_seconds: int = 86400


# Single shared instance, imported wherever config is needed.
settings = Settings()