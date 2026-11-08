from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product


class CartRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_cart(self, user_id: int, *, lock: bool = False) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
            .execution_options(populate_existing=True)  # luôn đọc lại dữ liệu mới nhất
        )
        if lock:
            stmt = stmt.with_for_update()  # tuần tự hóa các thao tác đồng thời của cùng một user
        return self.db.scalar(stmt)

    def get_or_create_cart(self, user_id: int, *, lock: bool = False) -> Cart:
        cart = self.get_cart(user_id, lock=lock)
        if cart is not None:
            return cart
        try:
            with self.db.begin_nested():
                self.db.add(Cart(user_id=user_id))
                self.db.flush()
        except IntegrityError:  # request song song đã tạo giỏ trước (UNIQUE user_id)
            pass
        return self.get_cart(user_id, lock=lock)  # type: ignore[return-value]

    def get_product(self, product_id: int) -> Product | None:
        return self.db.scalar(
            select(Product).where(Product.id == product_id).options(selectinload(Product.images))
        )

    def add_item(self, cart_id: int, product_id: int, quantity: int) -> None:
        self.db.add(CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity))
        self.db.flush()