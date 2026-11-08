from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.order import OrderStatus


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    image_url: str | None
    unit_price: Decimal
    quantity: int


class OrderHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: OrderStatus
    created_at: datetime


class OrderSummary(BaseModel):
    id: int
    code: str
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime


class OrderDetail(BaseModel):
    id: int
    code: str
    status: OrderStatus
    total_amount: Decimal
    recipient_name: str
    phone: str
    shipping_address: str
    note: str | None
    payment_method: str
    created_at: datetime
    items: list[OrderItemRead]
    history: list[OrderHistoryRead]


class OrderList(BaseModel):
    items: list[OrderSummary]
    total: int
    page: int
    page_size: int
