from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id")
