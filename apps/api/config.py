from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_asyncpg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    database_url: str

    bot_token: str
    telegram_webhook_secret: str

    api_base_url: str
    mini_app_url: str
    merchant_ton_wallet: str = ""

    jetton_master_address: str = ""

    # Comma-separated extra CORS origins (e.g. Railway preview URLs)
    allowed_origins: str = ""

    run_migrations_on_startup: bool = True
    seed_products_on_startup: bool = True

    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = "INFO"
    log_json: bool = False
    sql_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return _normalize_asyncpg_url(value)

    def cors_origins(self) -> list[str]:
        origins = {
            self.mini_app_url.rstrip("/"),
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        }
        for item in self.allowed_origins.split(","):
            origin = item.strip().rstrip("/")
            if origin:
                origins.add(origin)
        return sorted(origins)


settings = Settings()
