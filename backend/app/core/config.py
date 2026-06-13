"""Application configuration via Pydantic v2 Settings.

Loaded from environment variables and/or .env file.
Validates all required values at startup — invalid config prevents the app from starting.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration.

    Attributes:
        DATABASE_URL: PostgreSQL connection string (asyncpg).
        SECRET_KEY: Key for JWT signing — minimum 32 characters.
        ENCRYPTION_KEY: Key for AES-256 at-rest encryption — exactly 32 characters.
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT access token lifetime in minutes (default 15).
        OTEL_SERVICE_NAME: OpenTelemetry service name (optional).
        OTEL_EXPORTER_OTLP_ENDPOINT: OpenTelemetry exporter endpoint (optional).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # ── Required ──
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string via asyncpg",
    )
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing (min 32 characters)",
    )
    ENCRYPTION_KEY: str = Field(
        ...,
        min_length=32,
        max_length=32,
        description="Key for AES-256 encryption (exactly 32 characters)",
    )

    # ── Optional with defaults ──
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        ge=1,
        description="JWT access token expiration in minutes",
    )

    # ── OpenTelemetry (optional) ──
    OTEL_SERVICE_NAME: str | None = Field(
        default=None,
        description="OpenTelemetry service name",
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = Field(
        default=None,
        description="OpenTelemetry OTLP exporter endpoint",
    )

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def encryption_key_must_be_32_chars(cls, v: str) -> str:
        """Validate that ENCRYPTION_KEY is exactly 32 characters."""
        if len(v) != 32:
            raise ValueError(
                f"ENCRYPTION_KEY must be exactly 32 characters (got {len(v)})"
            )
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_be_asyncpg(cls, v: str) -> str:
        """Validate that DATABASE_URL uses the asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use asyncpg driver "
                "(postgresql+asyncpg://...)"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """FastAPI dependency: return a cached Settings instance.

    Cached to avoid re-parsing environment variables on every request.
    """
    return Settings()  # type: ignore[call-arg]
