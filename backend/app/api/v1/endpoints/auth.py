from fastapi import APIRouter, status

from app.core.dependencies import DbSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession):
    """FR-01. Always creates a CUSTOMER account."""
    return AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DbSession):
    """FR-02. Returns a short-lived JWT access token."""
    return AuthService(db).login(data)
