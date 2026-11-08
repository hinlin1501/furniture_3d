from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession, require_roles
from app.models.user import User, UserRole
from app.schemas.order import OrderDetail, OrderList
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.get("", response_model=OrderList)
def my_orders(
    user: Customer, db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return OrderService(db).list(user, page, page_size)


@router.get("/{order_id}", response_model=OrderDetail)
def order_detail(order_id: int, user: Customer, db: DbSession):
    return OrderService(db).get(user, order_id)
