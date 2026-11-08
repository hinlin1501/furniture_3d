from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

CartIssue = Literal["PRODUCT_UNAVAILABLE", "OUT_OF_STOCK", "INSUFFICIENT_STOCK"]


class CartItemCreate(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemRead(BaseModel):
    id: int
    product_id: int
    sku: str
    name: str
    image_url: str | None
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    available_stock: int
    issue: CartIssue | None = None


class CartRead(BaseModel):
    items: list[CartItemRead]
    total_quantity: int
    subtotal: Decimal  # tổng tiền tạm tính
    currency: str = "VND"
    has_issues: bool