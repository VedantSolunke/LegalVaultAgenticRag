from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LEGALVAULT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    test_auth_token: str = "test-user-token"
    # Supabase Auth: JWKS URL is derived from supabase_url; legacy HS256 uses jwt_secret.
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    corpus_backend: Literal["fixture", "postgres"] = "fixture"
    database_url: str | None = None
    cors_origins: str = "http://localhost:3000"
    session_ttl_days: int = 30
    bns_sections_json_path: Path | None = None
    ipc_mapping_primary_csv: Path | None = None
    ipc_mapping_supplemental_csv: Path | None = None
    fact_pattern_llm_faithfulness: bool = False
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LEGALVAULT_GEMINI_API_KEY", "GEMINI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        validation_alias=AliasChoices("LEGALVAULT_GEMINI_MODEL", "GEMINI_MODEL"),
    )

    @field_validator("database_url", "supabase_url", "supabase_jwt_secret", mode="before")
    @classmethod
    def _blank_str_is_none(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
