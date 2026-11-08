from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    if credentials is None:
        raise AuthenticationError("Authentication required", code="NOT_AUTHENTICATED")
    payload = decode_access_token(credentials.credentials)
    user = UserRepository(db).get_by_id(int(payload["sub"]))
    # Role and active flag always come from the DB, never from the token.
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid token", code="INVALID_TOKEN")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError()
        return user

    return checker


require_manager = require_roles(UserRole.STORE_MANAGER)
