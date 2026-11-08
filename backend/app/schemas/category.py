from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class CategoryRead(CategoryBrief):
    description: str | None
    parent_id: int | None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


def _clean_name(v: str | None) -> str | None:
    if v is None:
        return v
    v = " ".join(v.split())
    if not v:
        raise ValueError("name must not be blank")
    return v


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=2000)
    parent_id: int | None = None
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True

    _name = field_validator("name")(_clean_name)


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=2000)
    parent_id: int | None = None
    display_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    _name = field_validator("name")(_clean_name)
