from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///data/airacast.db"
    demo_mode: bool = Field(
        default=False, validation_alias=AliasChoices("demo_mode", "AIRACAST_DEMO")
    )

    data_gov_in_api_key: str = ""
    cpcb_resource_id: str = ""
    openaq_api_key: str = ""
    waqi_api_token: str = ""

    # Bearer token required for admin-guarded endpoints (alert rules CRUD, etc.).
    admin_token: str = ""

    http_timeout_seconds: float = 30.0
    provider_chunk_size: int = 25

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
