"""UC-C20 Theo dõi đơn hàng (FR-25). Customer chỉ truy cập đơn của chính mình."""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderDetail, OrderList, OrderSummary


class OrderService:
    def __init__(self, db: Session) -> None:
        self.repo = OrderRepository(db)

    def list(self, user: User, page: int, page_size: int) -> OrderList:
        rows, total = self.repo.list_for_user(user.id, page, page_size)
        return OrderList(
            items=[
                OrderSummary(id=o.id, code=o.code, status=o.status, total_amount=o.total_amount,
                             item_count=n, created_at=o.created_at)
                for o, n in rows
            ],
            total=total, page=page, page_size=page_size,
        )

    def get(self, user: User, order_id: int) -> OrderDetail:
        o = self.repo.get_for_user(order_id, user.id)
        if o is None:
            raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
        return OrderDetail(
            id=o.id, code=o.code, status=o.status, total_amount=o.total_amount,
            recipient_name=o.recipient_name, phone=o.phone, shipping_address=o.shipping_address,
            note=o.note, payment_method=o.payment.method, created_at=o.created_at,
            items=o.items, history=o.history,
        )
