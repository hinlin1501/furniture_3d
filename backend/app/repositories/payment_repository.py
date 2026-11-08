from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def get(self, payment_id: int) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def get_by_gateway_ref_for_update(self, gateway_ref: str) -> Payment | None:
        return self.db.scalar(
            select(Payment).where(Payment.gateway_ref == gateway_ref).with_for_update()
        )

    def pending_of_user(self, user_id: int) -> list[Payment]:
        return list(
            self.db.scalars(
                select(Payment).where(Payment.user_id == user_id, Payment.status == PaymentStatus.PENDING)
            )
        )
