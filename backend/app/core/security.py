from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing-equalisation")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except (VerificationError, InvalidHashError):
        return False


def verify_dummy_password(plain: str) -> None:
    """Burn comparable CPU time when the account does not exist (anti user-enumeration)."""
    verify_password(plain, _DUMMY_HASH)


def password_needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


def create_access_token(user_id: int, expires_minutes: int | None = None) -> tuple[str, int]:
    """Return (token, expires_in_seconds). Role is intentionally NOT put in the token:
    authorisation always uses the role stored in the database."""
    settings = get_settings()
    minutes = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired", code="TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid token", code="INVALID_TOKEN") from exc
    if payload.get("type") != "access" or not str(payload["sub"]).isdigit():
        raise AuthenticationError("Invalid token", code="INVALID_TOKEN")
    return payload
