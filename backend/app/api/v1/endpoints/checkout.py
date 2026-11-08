from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.core.dependencies import DbSession, require_roles
from app.core.exceptions import AuthenticationError
from app.models.user import User, UserRole
from app.schemas.checkout import (
    CheckoutRequest, CheckoutValidateRead, GatewayWebhookRequest, PaymentSessionRead,
    PaymentStatusRead, SandboxConfirmRequest,
)
from app.services import payment_gateway
from app.services.checkout_service import CheckoutService, status_read

router = APIRouter(prefix="/checkout", tags=["checkout"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.post("/validate", response_model=CheckoutValidateRead)
def validate_cart(user: Customer, db: DbSession):
    """FR-21: kiểm tra giỏ hàng trước khi đặt hàng."""
    return CheckoutService(db).validate(user)


@router.post("", response_model=PaymentSessionRead, status_code=201)
def start_checkout(data: CheckoutRequest, user: Customer, db: DbSession):
    """FR-22/23: xác nhận thông tin nhận hàng + phương thức, khởi tạo giao dịch thanh toán."""
    return CheckoutService(db).start(user, data)


@payments_router.get("/{payment_id}", response_model=PaymentStatusRead)
def payment_status(payment_id: int, user: Customer, db: DbSession):
    return status_read(CheckoutService(db).get_payment(user, payment_id))


@payments_router.post("/{payment_id}/sandbox-confirm", response_model=PaymentStatusRead)
def sandbox_confirm(payment_id: int, data: SandboxConfirmRequest, user: Customer, db: DbSession):
    """Giả lập cổng thanh toán (SUCCESS / FAILED / EXPIRED)."""
    return CheckoutService(db).sandbox_confirm(user, payment_id, data.outcome)


@payments_router.post("/webhook", response_model=PaymentStatusRead)
def gateway_webhook(
    data: GatewayWebhookRequest, db: DbSession, x_signature: Annotated[str, Header()] = ""
):
    """Nhận kết quả từ cổng thanh toán bên ngoài; chữ ký HMAC-SHA256 ở header X-Signature."""
    if not payment_gateway.verify_signature(data.gateway_ref, data.result, data.amount, x_signature):
        raise AuthenticationError("Invalid payment signature", code="INVALID_SIGNATURE")
    return CheckoutService(db).apply_gateway_result(data.gateway_ref, data.result, data.amount, data.reason)
