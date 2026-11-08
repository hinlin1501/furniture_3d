from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: int, page: int, page_size: int) -> tuple[list[tuple[Order, int]], int]:
        total = int(self.db.scalar(select(func.count()).select_from(Order).where(Order.user_id == user_id)) or 0)
        rows = self.db.execute(
            select(Order, func.coalesce(func.sum(OrderItem.quantity), 0))
            .outerjoin(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.user_id == user_id)
            .group_by(Order.id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return [(o, int(n)) for o, n in rows], total

    def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        order = self.db.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.history), selectinload(Order.payment))
        )
        # đơn của người khác -> None (API trả 404, không lộ sự tồn tại)
        return order if order is not None and order.user_id == user_id else None
