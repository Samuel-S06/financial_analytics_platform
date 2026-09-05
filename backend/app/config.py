"""App configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    service_name: str = "financial-platform-backend"
    redis_host: str = "localhost"
    redis_port: int = 6379
    use_redis: bool = True
    job_ttl_seconds: int = 86400
    # Comma-separated list of origins allowed to call the API from a browser.
    # In-cluster and in `npm run dev` the frontend is same-origin (nginx / the
    # Vite proxy sit in front), so this is empty-by-default and only matters
    # once the frontend is hosted separately from the backend.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
