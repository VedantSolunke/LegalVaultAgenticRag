from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from legalvault.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)

_TEST_USER_TOKENS: dict[str, tuple[str, bool]] = {
    "test-user-token": ("test-user", False),
    "test-user-b-token": ("test-user-b", False),
    "test-admin-token": ("test-admin", True),
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
    app_metadata = payload.get("app_metadata") or {}
    is_admin = bool(app_metadata.get("is_admin"))
    return AuthenticatedUser(user_id=str(sub), is_admin=is_admin)


def _profile_is_admin(user_id: str, settings: Settings) -> bool | None:
    if settings.database_url is None:
        return None
    import psycopg

    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT is_admin FROM profiles WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
    except psycopg.Error:
        return None
    if row is None:
        return None
    return bool(row[0])


def _user_from_test_token(token: str, settings: Settings) -> AuthenticatedUser | None:
    if token in _TEST_USER_TOKENS:
        user_id, is_admin = _TEST_USER_TOKENS[token]
        profile_admin = _profile_is_admin(user_id, settings)
        if profile_admin is not None:
            is_admin = profile_admin
        return AuthenticatedUser(user_id=user_id, is_admin=is_admin)
    if token == settings.test_auth_token:
        user_id = "test-user"
        profile_admin = _profile_is_admin(user_id, settings)
        return AuthenticatedUser(
            user_id=user_id,
            is_admin=profile_admin if profile_admin is not None else False,
        )
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
        user = _user_from_supabase_jwt(
            credentials.credentials, settings.supabase_jwt_secret
        )
        profile_admin = _profile_is_admin(user.user_id, settings)
        if profile_admin is not None:
            return AuthenticatedUser(user_id=user.user_id, is_admin=profile_admin)
        return user

    test_user = _user_from_test_token(credentials.credentials, settings)
    if test_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return test_user


def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
