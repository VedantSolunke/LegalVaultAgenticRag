from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEGALVAULT_")

    test_auth_token: str = "test-user-token"
    # Reserved for Supabase JWT verification and environment-specific config.
    supabase_jwt_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
