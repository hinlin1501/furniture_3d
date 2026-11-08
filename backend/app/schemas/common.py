from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class PageResult:
    """Plain container returned by services (items are ORM objects)."""

    def __init__(self, items: list, total: int, page: int, page_size: int) -> None:
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.pages = -(-total // page_size) if total else 0


def to_page(result: PageResult, item_schema: type) -> "Page":
    return Page[item_schema].model_validate(  # type: ignore[valid-type]
        {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "pages": result.pages,
        },
        from_attributes=True,
    )
