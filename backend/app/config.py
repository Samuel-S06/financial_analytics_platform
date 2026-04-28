"""App configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    service_name: str = "financial-platform-backend"
    redis_host: str = "localhost"
    redis_port: int = 6379
    use_redis: bool = True
    job_ttl_seconds: int = 86400


settings = Settings()
