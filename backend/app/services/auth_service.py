from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: RegisterRequest) -> User:
        email = data.email.strip().lower()
        if self.users.get_by_email(email):
            raise ConflictError("Email is already registered", code="EMAIL_ALREADY_REGISTERED")
        user = User(
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role=UserRole.CUSTOMER,  # always CUSTOMER: managers are provisioned out-of-band
        )
        try:
            self.users.add(user)
            self.db.commit()
        except IntegrityError as exc:  # race on the unique email index
            self.db.rollback()
            raise ConflictError(
                "Email is already registered", code="EMAIL_ALREADY_REGISTERED"
            ) from exc
        return user

    def login(self, data: LoginRequest) -> TokenResponse:
        invalid = AuthenticationError("Incorrect email or password", code="INVALID_CREDENTIALS")
        user = self.users.get_by_email(data.email.strip().lower())
        if user is None:
            verify_dummy_password(data.password)
            raise invalid
        if not verify_password(data.password, user.password_hash) or not user.is_active:
            raise invalid
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(data.password)
            self.db.commit()
        token, expires_in = create_access_token(user.id)
        return TokenResponse(
            access_token=token, expires_in=expires_in, user=UserRead.model_validate(user)
        )
