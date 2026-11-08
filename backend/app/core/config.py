"""Application configuration, loaded from environment variables / .env file."""

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRETS = {"", "change-me", "changeme", "secret"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Application ---
    app_name: str = "HLK E-Furniture Platform API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_json: bool = False

    # --- Database ---
    # SQLAlchemy URL using the psycopg (v3) driver.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/furniture_3d"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    db_echo: bool = False
    # pgvector embedding size. Must match the vector(N) columns in ai.* tables.
    # Not finalised yet; keep configurable (e.g. 512 for CLIP ViT-B/32).
    embedding_dimension: int = 512

    # --- Security (used from Phase 2) ---
    secret_key: str | None = Field(default=None)
    jwt_secret_key: str | None = None  # env JWT_SECRET_KEY; falls back to SECRET_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Payment Security ---
    payment_webhook_secret: str | None = Field(default=None)
    payment_session_ttl_minutes: int = 15

    # --- E-commerce: Cart ---
    max_cart_line_qty: int = 99

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @model_validator(mode="after")
    def _resolve_jwt_secret(self) -> "Settings":
        if not self.jwt_secret_key:
            self.jwt_secret_key = self.secret_key
        if not self.jwt_secret_key:
            if self.app_env == "production":
                raise ValueError("JWT_SECRET_KEY (or SECRET_KEY) must be set in production")
            # dev/test only: random per-process key (tokens do not survive a restart)
            self.jwt_secret_key = secrets.token_urlsafe(48)
        return self

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        if self.app_env == "production":
            if (self.secret_key or "").lower() in _INSECURE_SECRETS or len(self.secret_key or "") < 32:
                raise ValueError("SECRET_KEY must be set to a random value of >= 32 chars in production")
            if self.debug:
                raise ValueError("DEBUG must be false in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()