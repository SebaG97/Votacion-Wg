from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="VOTACION WG API", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(
        default="sqlite:///./votacion_wg.db",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174", alias="CORS_ORIGINS"
    )
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")
    rate_limit_por_minuto: int = Field(default=20, alias="RATE_LIMIT_POR_MINUTO")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
