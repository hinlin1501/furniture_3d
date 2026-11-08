import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.order import PaymentStatus
from app.schemas.cart import CartRead

_PHONE_RE = re.compile(r"^(\+84|0)\d{9,10}$")
PaymentMethod = Literal["SANDBOX_CARD", "SANDBOX_WALLET"]
GatewayResult = Literal["SUCCESS", "FAILED", "EXPIRED"]


class ShippingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_name: str = Field(min_length=1, max_length=255)
    phone: str
    address: str = Field(min_length=5, max_length=500)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("recipient_name", "address")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not _PHONE_RE.match(v):
            raise ValueError("invalid phone number")
        return v


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shipping: ShippingInput
    payment_method: PaymentMethod


class CheckoutValidateRead(BaseModel):
    valid: bool
    cart: CartRead


class PaymentSessionRead(BaseModel):
    payment_id: int
    gateway_ref: str
    amount: Decimal
    method: str
    status: PaymentStatus
    expires_at: datetime


class PaymentStatusRead(BaseModel):
    payment_id: int
    status: PaymentStatus
    failure_reason: str | None = None
    order_id: int | None = None
    order_code: str | None = None


class SandboxConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: GatewayResult = "SUCCESS"


class GatewayWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gateway_ref: str = Field(min_length=1, max_length=64)
    result: GatewayResult
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    reason: str | None = Field(default=None, max_length=255)
