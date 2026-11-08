from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def get_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead)
def update_me(data: UserUpdate, user: CurrentUser, db: DbSession):
    """FR-03. Only full_name, phone and shipping_address can be changed."""
    return UserService(db).update_profile(user, data)
