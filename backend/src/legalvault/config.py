from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEGALVAULT_")

    test_auth_token: str = "test-user-token"
    # Reserved for Supabase JWT verification and environment-specific config.
    supabase_jwt_secret: str | None = None
    corpus_backend: Literal["fixture", "postgres"] = "fixture"
    database_url: str | None = None
    cors_origins: str = "http://localhost:3000"
    session_ttl_days: int = 30
    bns_sections_json_path: Path | None = None
    ipc_mapping_primary_csv: Path | None = None
    ipc_mapping_supplemental_csv: Path | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
