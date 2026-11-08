"""UC-C18 Quản lý giỏ hàng (FR-19, FR-20)."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.cart import Cart, CartItem
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.repositories.cart_repository import CartRepository
from app.schemas.cart import CartItemRead, CartRead

MAX_LINE_QUANTITY = 99


def item_issue(item: CartItem) -> str | None:
    p = item.product
    if p.status != ProductStatus.ACTIVE:
        return "PRODUCT_UNAVAILABLE"
    if p.stock_quantity <= 0:
        return "OUT_OF_STOCK"
    if item.quantity > p.stock_quantity:
        return "INSUFFICIENT_STOCK"
    return None


def to_cart_read(cart: Cart | None) -> CartRead:
    """Giá và tồn kho luôn lấy theo dữ liệu sản phẩm hiện hành => giỏ hàng nhất quán."""
    items = [
        CartItemRead(
            id=i.id, product_id=i.product_id, sku=i.product.sku, name=i.product.name,
            image_url=i.product.primary_image_url, unit_price=i.product.price, quantity=i.quantity,
            line_total=i.product.price * i.quantity,
            available_stock=max(i.product.stock_quantity, 0), issue=item_issue(i),
        )
        for i in (cart.items if cart else [])
    ]
    return CartRead(
        items=items,
        total_quantity=sum(i.quantity for i in items),
        subtotal=sum((i.line_total for i in items), Decimal("0")),
        has_issues=any(i.issue for i in items),
    )


def _check_quantity(product: Product, quantity: int) -> None:
    if product.status != ProductStatus.ACTIVE:
        raise ConflictError(f"Product '{product.name}' is no longer available", code="PRODUCT_UNAVAILABLE")
    if product.stock_quantity <= 0:
        raise ConflictError(f"Product '{product.name}' is out of stock", code="OUT_OF_STOCK")
    if quantity > product.stock_quantity:
        raise ConflictError(
            f"Only {product.stock_quantity} unit(s) of '{product.name}' left in stock",
            code="INSUFFICIENT_STOCK", details={"available_stock": product.stock_quantity},
        )
    if quantity > MAX_LINE_QUANTITY:
        raise BusinessRuleError(
            f"Maximum quantity per product is {MAX_LINE_QUANTITY}", code="QUANTITY_LIMIT"
        )


class CartService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CartRepository(db)

    def get(self, user: User) -> CartRead:
        return to_cart_read(self.repo.get_cart(user.id))

    def add_item(self, user: User, product_id: int, quantity: int) -> CartRead:
        product = self.repo.get_product(product_id)
        if product is None:
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        cart = self.repo.get_or_create_cart(user.id, lock=True)
        existing = next((i for i in cart.items if i.product_id == product_id), None)
        # Alternative Flow: sản phẩm đã có -> cộng dồn số lượng, không tạo dòng trùng
        new_qty = (existing.quantity if existing else 0) + quantity
        _check_quantity(product, new_qty)
        if existing:
            existing.quantity = new_qty
        else:
            self.repo.add_item(cart.id, product_id, quantity)
        self.db.commit()
        return self.get(user)

    def _item(self, cart: Cart, item_id: int) -> CartItem:
        item = next((i for i in cart.items if i.id == item_id), None)
        if item is None:
            raise NotFoundError("Cart item not found", code="CART_ITEM_NOT_FOUND")
        return item

    def update_item(self, user: User, item_id: int, quantity: int) -> CartRead:
        cart = self.repo.get_or_create_cart(user.id, lock=True)
        item = self._item(cart, item_id)
        _check_quantity(item.product, quantity)
        item.quantity = quantity
        self.db.commit()
        return self.get(user)

    def remove_item(self, user: User, item_id: int) -> CartRead:
        cart = self.repo.get_or_create_cart(user.id, lock=True)
        cart.items.remove(self._item(cart, item_id))
        self.db.commit()
        return self.get(user)

    def clear(self, user: User) -> CartRead:
        cart = self.repo.get_or_create_cart(user.id, lock=True)
        cart.items.clear()
        self.db.commit()
        return self.get(user)