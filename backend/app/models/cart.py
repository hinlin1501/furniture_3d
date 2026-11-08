"""Giỏ hàng (UC-C18). Mỗi user có tối đa 1 giỏ; giá luôn lấy từ products.price tại thời điểm xem/đặt."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.product import Product


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", order_by="CartItem.id"
    )


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (
        # Alternative Flow UC-C18: sản phẩm đã có trong giỏ thì cộng dồn, không tạo dòng trùng
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer)

    cart: Mapped[Cart] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()