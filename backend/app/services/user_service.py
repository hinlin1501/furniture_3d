from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_profile(self, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "full_name" and value is None:
                continue  # full name is mandatory
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user
