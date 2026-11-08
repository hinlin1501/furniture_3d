from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import DbSession, require_roles
from app.models.user import User, UserRole
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.get("", response_model=CartRead)
def get_cart(user: Customer, db: DbSession):
    return CartService(db).get(user)


@router.post("/items", response_model=CartRead, status_code=201)
def add_item(data: CartItemCreate, user: Customer, db: DbSession):
    return CartService(db).add_item(user, data.product_id, data.quantity)


@router.patch("/items/{item_id}", response_model=CartRead)
def update_item(item_id: int, data: CartItemUpdate, user: Customer, db: DbSession):
    return CartService(db).update_item(user, item_id, data.quantity)


@router.delete("/items/{item_id}", response_model=CartRead)
def remove_item(item_id: int, user: Customer, db: DbSession):
    return CartService(db).remove_item(user, item_id)


@router.delete("", response_model=CartRead)
def clear_cart(user: Customer, db: DbSession):
    return CartService(db).clear(user)