import enum

from sqlalchemy import Boolean, Enum, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    STORE_MANAGER = "STORE_MANAGER"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # stored lower-case
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    shipping_address: Mapped[str | None] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=20, create_constraint=True),
        default=UserRole.CUSTOMER,
        server_default=UserRole.CUSTOMER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
