"""App configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    service_name: str = "spendline-backend"
    redis_host: str = "localhost"
    redis_port: int = 6379
    use_redis: bool = True
    job_ttl_seconds: int = 86400
    # Comma-separated list of origins allowed to call the API from a browser.
    # In-cluster and in `npm run dev` the frontend is same-origin (nginx / the
    # Vite proxy sit in front), so this is empty-by-default and only matters
    # once the frontend is hosted separately from the backend.
    cors_origins: str = "http://localhost:5173"
    # Hosts like Vercel give every deployment its own subdomain, so an exact
    # origin list only ever covers the production alias and every preview URL
    # fails CORS. A regex covers the whole project. Keep it anchored - a
    # pattern like ".*vercel.app" would allow anybody's Vercel site.
    cors_origin_regex: str = ""

    # --- Auth ---------------------------------------------------------------
    # Defaults to ON so a misconfigured deploy fails closed rather than serving
    # everyone's data. Turning it off is opt-in and logged loudly - see
    # docker-compose.yml, which sets it for local work before Supabase keys
    # exist.
    auth_enabled: bool = True
    # e.g. https://abcdefgh.supabase.co - used to build the JWKS URL and to
    # check the issuer claim.
    supabase_url: str = ""
    # Only for projects still on legacy HS256 symmetric signing. Newer Supabase
    # projects sign with ES256/RS256 and publish a JWKS, which needs no secret.
    supabase_jwt_secret: str = ""
    # Identity attributed to requests when auth_enabled is false.
    dev_user_id: str = "dev-user"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def jwt_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"


settings = Settings()
