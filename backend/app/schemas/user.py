import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-]{7,18}$")


def _validate_phone(v: str | None) -> str | None:
    if v is None:
        return v
    v = v.strip()
    if v == "":
        return None
    if not PHONE_RE.match(v):
        raise ValueError("Invalid phone number")
    return v


class UserRead(BaseModel):
    """Public representation of a user. password_hash is never exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    shipping_address: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """UC-C03: only full name, phone and shipping address are editable.
    Unknown fields (email, role, ...) are rejected, preventing privilege escalation."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = None
    shipping_address: str | None = Field(default=None, max_length=1000)

    _phone = field_validator("phone")(_validate_phone)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("full_name must not be blank")
        return v
