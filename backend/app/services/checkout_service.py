"""UC-C19 Thanh toán và đặt hàng (FR-21 → FR-24, NFR-12).

Toàn vẹn giao dịch:
  * Đơn hàng CHỈ được tạo khi nhận kết quả thanh toán hợp lệ (đúng số tiền, chưa hết hạn).
  * Trừ kho bằng UPDATE có điều kiện (stock >= qty) trong cùng transaction với việc tạo đơn;
    thiếu hàng ở bất kỳ sản phẩm nào -> hoàn tác toàn bộ (savepoint).
  * Khóa dòng payment + orders.payment_id UNIQUE => kết quả gửi lặp không tạo đơn / trừ kho lần 2.
  * Thất bại / hết hạn: không tạo đơn, không trừ kho, giỏ giữ nguyên.
"""
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, BusinessRuleError, ConflictError, NotFoundError
from app.models.order import (
    Order, OrderItem, OrderStatus, OrderStatusHistory, Payment, PaymentStatus,
)
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.repositories.cart_repository import CartRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.checkout import (
    CheckoutRequest, CheckoutValidateRead, PaymentSessionRead, PaymentStatusRead,
)
from app.services import payment_gateway
from app.services.cart_service import to_cart_read


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # SQLite trả datetime naive


def status_read(p: Payment) -> PaymentStatusRead:
    return PaymentStatusRead(
        payment_id=p.id, status=p.status, failure_reason=p.failure_reason,
        order_id=p.order.id if p.order else None, order_code=p.order.code if p.order else None,
    )


class CheckoutService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.carts = CartRepository(db)
        self.payments = PaymentRepository(db)

    # ---- FR-21 Kiểm tra giỏ hàng ----
    def validate(self, user: User) -> CheckoutValidateRead:
        cart = self.carts.get_cart(user.id)
        if cart is None or not cart.items:
            raise BusinessRuleError("Cart is empty", code="CART_EMPTY")
        read = to_cart_read(cart)
        return CheckoutValidateRead(valid=not read.has_issues, cart=read)

    # ---- FR-22/23 Xác nhận thông tin + khởi tạo giao dịch ----
    def start(self, user: User, data: CheckoutRequest) -> PaymentSessionRead:
        checked = self.validate(user)
        if not checked.valid:
            raise ConflictError(
                "Some items in your cart can no longer be ordered; please adjust your cart",
                code="CART_INVALID",
                details=[{"product_id": i.product_id, "issue": i.issue} for i in checked.cart.items if i.issue],
            )
        for old in self.payments.pending_of_user(user.id):  # chỉ giữ 1 phiên đang chờ
            old.status, old.failure_reason = PaymentStatus.EXPIRED, "Superseded by a newer payment session"

        snapshot = {
            "items": [
                {"product_id": i.product_id, "name": i.name, "image_url": i.image_url,
                 "unit_price": str(i.unit_price), "quantity": i.quantity}
                for i in checked.cart.items
            ],
            "shipping": data.shipping.model_dump(),
        }
        payment = self.payments.add(Payment(
            user_id=user.id, method=data.payment_method, amount=checked.cart.subtotal, snapshot=snapshot,
            gateway_ref="SBX-" + secrets.token_hex(10).upper(),
            expires_at=_now() + timedelta(minutes=payment_gateway.session_ttl_minutes()),
        ))
        self.db.commit()
        return PaymentSessionRead(
            payment_id=payment.id, gateway_ref=payment.gateway_ref, amount=payment.amount,
            method=payment.method, status=payment.status, expires_at=payment.expires_at,
        )

    def get_payment(self, user: User, payment_id: int) -> Payment:
        p = self.payments.get(payment_id)
        if p is None or p.user_id != user.id:  # không lộ giao dịch của người khác
            raise NotFoundError("Payment not found", code="PAYMENT_NOT_FOUND")
        return p

    # ---- Payment Sandbox: khách xác nhận -> cổng gửi kết quả có chữ ký ----
    def sandbox_confirm(self, user: User, payment_id: int, outcome: str) -> PaymentStatusRead:
        p = self.get_payment(user, payment_id)
        reason = "Payment declined (sandbox)" if outcome == "FAILED" else None
        return self.apply_gateway_result(p.gateway_ref, outcome, p.amount, reason)

    # ---- FR-24 Điểm vào duy nhất cho kết quả giao dịch (idempotent) ----
    def apply_gateway_result(
        self, gateway_ref: str, result: str, amount: Decimal, reason: str | None = None
    ) -> PaymentStatusRead:
        payment = self.payments.get_by_gateway_ref_for_update(gateway_ref)
        if payment is None:
            raise NotFoundError("Payment not found", code="PAYMENT_NOT_FOUND")
        if payment.status != PaymentStatus.PENDING:  # kết quả gửi lặp: trả trạng thái hiện có
            return status_read(payment)

        payment.completed_at = _now()
        if result == "FAILED":
            payment.status, payment.failure_reason = PaymentStatus.FAILED, reason or "Payment failed"
        elif result == "EXPIRED" or _now() > _aware(payment.expires_at):
            payment.status, payment.failure_reason = PaymentStatus.EXPIRED, "Payment session expired"
        elif Decimal(amount) != payment.amount:
            payment.status, payment.failure_reason = PaymentStatus.FAILED, "Paid amount does not match"
        else:
            self._finalize_success(payment)
            return status_read(payment)
        self.db.commit()
        return status_read(payment)

    def _finalize_success(self, payment: Payment) -> None:
        snap = payment.snapshot
        order: Order | None = None
        try:
            with self.db.begin_nested():  # savepoint: thiếu hàng sẽ hoàn tác mọi lần trừ kho dở dang
                for it in sorted(snap["items"], key=lambda i: i["product_id"]):  # thứ tự cố định, tránh deadlock
                    res = self.db.execute(
                        update(Product)
                        .where(Product.id == it["product_id"], Product.status == ProductStatus.ACTIVE,
                               Product.stock_quantity >= it["quantity"])
                        .values(stock_quantity=Product.stock_quantity - it["quantity"])
                    )
                    if res.rowcount != 1:
                        raise ConflictError(f"'{it['name']}' no longer has enough stock", code="STOCK_CHANGED")
                ship = snap["shipping"]
                order = Order(
                    code=f"ORD-{_now():%Y%m%d}-{secrets.token_hex(4).upper()}",
                    user_id=payment.user_id, payment_id=payment.id, status=OrderStatus.CONFIRMED,
                    total_amount=payment.amount, recipient_name=ship["recipient_name"], phone=ship["phone"],
                    shipping_address=ship["address"], note=ship.get("note"),
                )
                order.items = [
                    OrderItem(product_id=i["product_id"], product_name=i["name"], image_url=i.get("image_url"),
                              unit_price=Decimal(i["unit_price"]), quantity=i["quantity"])
                    for i in snap["items"]
                ]
                order.history = [OrderStatusHistory(status=OrderStatus.CONFIRMED)]
                self.db.add(order)
                self.db.flush()
        except AppError as e:
            # Đã thu tiền nhưng không lập được đơn -> hoàn tiền sandbox, không tạo đơn, không trừ kho
            payment.status = PaymentStatus.REFUNDED
            payment.failure_reason = f"{e.message}. The payment was refunded."
            self.db.commit()
            return
        payment.status = PaymentStatus.SUCCESS
        self._remove_purchased_from_cart(payment)
        self.db.commit()
        self.db.refresh(payment)

    def _remove_purchased_from_cart(self, payment: Payment) -> None:
        """Chỉ trừ phần đã mua; nếu khách thêm tiếp sản phẩm trong lúc thanh toán thì giữ phần dư."""
        cart = self.carts.get_cart(payment.user_id)
        if cart is None:
            return
        bought = {i["product_id"]: i["quantity"] for i in payment.snapshot["items"]}
        for item in list(cart.items):
            q = bought.get(item.product_id)
            if q is None:
                continue
            if item.quantity > q:
                item.quantity -= q
            else:
                cart.items.remove(item)
