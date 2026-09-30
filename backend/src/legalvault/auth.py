from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from legalvault.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)

_TEST_USER_TOKENS: dict[str, str] = {
    "test-user-token": "test-user",
    "test-user-b-token": "test-user-b",
}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    is_admin: bool = False


def _user_from_supabase_jwt(token: str, secret: str) -> AuthenticatedUser:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from None
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return AuthenticatedUser(user_id=str(sub))


def _user_from_test_token(token: str, settings: Settings) -> AuthenticatedUser | None:
    if token in _TEST_USER_TOKENS:
        return AuthenticatedUser(user_id=_TEST_USER_TOKENS[token])
    if token == settings.test_auth_token:
        return AuthenticatedUser(user_id="test-user")
    return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if settings.supabase_jwt_secret:
        return _user_from_supabase_jwt(credentials.credentials, settings.supabase_jwt_secret)

    test_user = _user_from_test_token(credentials.credentials, settings)
    if test_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return test_user
