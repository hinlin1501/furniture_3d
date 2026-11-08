"""Thanh toán và đơn hàng (UC-C19, UC-C20)."""
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON, CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class OrderStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"  # đã thanh toán, chờ xử lý
    PREPARING = "PREPARING"  # đang chuẩn bị hàng
    SHIPPING = "SHIPPING"    # đang giao
    COMPLETED = "COMPLETED"  # hoàn tất


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"  # đã thu tiền nhưng không lập được đơn (vd: hết hàng) -> hoàn tiền sandbox


def _enum(e: type[enum.Enum], name: str) -> Enum:
    return Enum(e, name=name, native_enum=False, length=20, create_constraint=True)


class Payment(Base, TimestampMixin):
    """Giao dịch thanh toán; giữ snapshot giỏ hàng + thông tin nhận hàng tại lúc khởi tạo."""
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    method: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        _enum(PaymentStatus, "payment_status"),
        default=PaymentStatus.PENDING, server_default=PaymentStatus.PENDING.value, index=True,
    )
    snapshot: Mapped[dict] = mapped_column(JSON)
    gateway_ref: Mapped[str] = mapped_column(String(64), unique=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped["Order | None"] = relationship(back_populates="payment", uselist=False)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("total_amount > 0", name="total_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    # UNIQUE: mỗi giao dịch tối đa 1 đơn => không trừ kho trùng lặp (NFR-12)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), unique=True)
    status: Mapped[OrderStatus] = mapped_column(
        _enum(OrderStatus, "order_status"),
        default=OrderStatus.CONFIRMED, server_default=OrderStatus.CONFIRMED.value, index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    recipient_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    shipping_address: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["OrderItem"]] = relationship(
        cascade="all, delete-orphan", order_by="OrderItem.id"
    )
    history: Mapped[list["OrderStatusHistory"]] = relationship(
        cascade="all, delete-orphan", order_by="OrderStatusHistory.id"
    )
    payment: Mapped[Payment] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(255))  # snapshot
    image_url: Mapped[str | None] = mapped_column(String(1024))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # snapshot
    quantity: Mapped[int] = mapped_column(Integer)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[OrderStatus] = mapped_column(_enum(OrderStatus, "order_history_status"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )