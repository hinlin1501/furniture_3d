"""Payment Sandbox: ký / xác thực kết quả giao dịch giữa cổng thanh toán và hệ thống (FR-23).

Cấu hình qua biến môi trường (chuyển sang settings của dự án nếu muốn):
  PAYMENT_WEBHOOK_SECRET        khóa HMAC (bắt buộc khi ENVIRONMENT=production)
  PAYMENT_SESSION_TTL_MINUTES   thời hạn phiên thanh toán, mặc định 15
"""
import hashlib
import hmac
import os
from decimal import Decimal

from app.core.exceptions import ServiceUnavailableError

_DEFAULT_SECRET = "sandbox-webhook-secret"


def session_ttl_minutes() -> int:
    return int(os.getenv("PAYMENT_SESSION_TTL_MINUTES", "15"))


def _secret() -> bytes:
    secret = os.getenv("PAYMENT_WEBHOOK_SECRET")
    if not secret:
        if os.getenv("ENVIRONMENT", "").lower() == "production":
            raise ServiceUnavailableError("Payment gateway is not configured", code="PAYMENT_NOT_CONFIGURED")
        secret = _DEFAULT_SECRET
    return secret.encode()


def money(amount: Decimal) -> str:
    return format(Decimal(amount).quantize(Decimal("0.01")), "f")


def sign_result(gateway_ref: str, result: str, amount: Decimal) -> str:
    msg = f"{gateway_ref}|{result}|{money(amount)}".encode()
    return hmac.new(_secret(), msg, hashlib.sha256).hexdigest()


def verify_signature(gateway_ref: str, result: str, amount: Decimal, signature: str) -> bool:
    return hmac.compare_digest(sign_result(gateway_ref, result, amount), signature or "")
