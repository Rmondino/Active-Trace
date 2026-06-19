"""Tests for core.config — Settings validation (TDD)."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsValidation:
    """RED → GREEN → TRIANGULATE for Settings configuration."""

    # ── RED: Settings should instantiate with valid env ──

    def test_settings_instantiates_with_valid_env(self):
        """Settings object is created successfully with valid environment variables."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
            ACCESS_TOKEN_EXPIRE_MINUTES=15,
        )
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/db"
        assert settings.SECRET_KEY == "a" * 32
        assert settings.ENCRYPTION_KEY == "b" * 32
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15

    # ── RED: Missing required env should fail ──

    def test_missing_required_variable_raises_error(self):
        """Settings raises ValidationError when a required variable is missing."""
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                # Missing DATABASE_URL
                SECRET_KEY="a" * 32,
                ENCRYPTION_KEY="b" * 32,
            )

    # ── RED: Invalid SECRET_KEY length should fail ──

    def test_secret_key_too_short_raises_error(self):
        """Settings raises ValidationError when SECRET_KEY is too short."""
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
                SECRET_KEY="short",  # Less than 32 chars
                ENCRYPTION_KEY="b" * 32,
            )

    # ── RED: Invalid ENCRYPTION_KEY length should fail ──

    def test_encryption_key_wrong_length_raises_error(self):
        """Settings raises ValidationError when ENCRYPTION_KEY is not exactly 32 chars."""
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
                SECRET_KEY="a" * 32,
                ENCRYPTION_KEY="wrong_length",  # Not 32 chars
            )

    # ── RED: Default value for ACCESS_TOKEN_EXPIRE_MINUTES ──

    def test_access_token_expire_default(self):
        """ACCESS_TOKEN_EXPIRE_MINUTES defaults to 15 when not provided."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15

    # ── TRIANGULATE: Invalid type should fail ──

    def test_invalid_type_raises_error(self):
        """Settings raises ValidationError when a value has an invalid type."""
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
                SECRET_KEY="a" * 32,
                ENCRYPTION_KEY="b" * 32,
                ACCESS_TOKEN_EXPIRE_MINUTES="not-a-number",  # Invalid type
            )
