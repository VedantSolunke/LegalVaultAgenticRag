"""Auth tests for Supabase JWT and test tokens."""

import jwt

from legalvault.config import get_settings


def test_research_rejects_invalid_jwt_when_supabase_secret_configured(
    client, monkeypatch
) -> None:
    monkeypatch.setenv("LEGALVAULT_SUPABASE_URL", "")
    monkeypatch.setenv(
        "LEGALVAULT_SUPABASE_JWT_SECRET",
        "unit-test-jwt-secret-at-least-32-bytes-long",
    )
    get_settings.cache_clear()

    response = client.post(
        "/research",
        json={"query": "What is BNS section 101?"},
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert response.status_code == 401

    get_settings.cache_clear()
    monkeypatch.delenv("LEGALVAULT_SUPABASE_JWT_SECRET", raising=False)


def test_research_accepts_signed_supabase_jwt(client, monkeypatch) -> None:
    secret = "unit-test-jwt-secret-at-least-32-bytes-long"
    monkeypatch.setenv("LEGALVAULT_SUPABASE_URL", "")
    monkeypatch.setenv("LEGALVAULT_SUPABASE_JWT_SECRET", secret)
    get_settings.cache_clear()

    token = jwt.encode(
        {"sub": "supabase-user-1", "aud": "authenticated"},
        secret,
        algorithm="HS256",
    )
    response = client.post(
        "/research",
        json={"query": "What is BNS section 101?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    get_settings.cache_clear()
    monkeypatch.delenv("LEGALVAULT_SUPABASE_JWT_SECRET", raising=False)
