import os

import pytest
from fastapi.testclient import TestClient

from legalvault.config import get_settings
from legalvault.main import create_app


@pytest.fixture(autouse=True)
def _isolate_settings_from_local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests use dev bearer tokens unless a case sets Supabase/Postgres explicitly."""
    monkeypatch.setenv("LEGALVAULT_SUPABASE_URL", "")
    monkeypatch.setenv("LEGALVAULT_SUPABASE_JWT_SECRET", "")
    monkeypatch.setenv("LEGALVAULT_CORPUS_BACKEND", "fixture")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("LEGALVAULT_GEMINI_API_KEY", "")
    test_db = os.environ.get("LEGALVAULT_TEST_DATABASE_URL")
    if test_db:
        monkeypatch.setenv("LEGALVAULT_DATABASE_URL", test_db)
    else:
        monkeypatch.setenv("LEGALVAULT_DATABASE_URL", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-user-token"}
