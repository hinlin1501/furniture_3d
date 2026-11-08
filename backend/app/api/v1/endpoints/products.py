from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import DbSession, require_manager
from app.schemas.common import Page, to_page
from app.schemas.product import (
    AdminProductFilterParams,
    AdminProductRead,
    ProductAssets,
    ProductCreate,
    ProductDetail,
    ProductFilterParams,
    ProductListItem,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])
admin_router = APIRouter(
    prefix="/admin/products", tags=["Admin – Products"], dependencies=[Depends(require_manager)]
)


@router.get("", response_model=Page[ProductListItem])
def list_products(filters: Annotated[ProductFilterParams, Query()], db: DbSession):
    """FR-06/07. Keyword search, filters (category, price, material, style, color,
    dimensions), sorting and pagination. Only ACTIVE products are returned."""
    return to_page(ProductService(db).list_products(filters), ProductListItem)


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: DbSession):
    """FR-08. Dimensions, attributes, images, 3D models, stock status, category."""
    return ProductService(db).get_product(product_id)


@router.get("/{product_id}/assets", response_model=ProductAssets)
def get_product_assets(product_id: int, db: DbSession):
    return ProductService(db).get_assets(product_id)


@admin_router.get("", response_model=Page[AdminProductRead])
def admin_list_products(filters: Annotated[AdminProductFilterParams, Query()], db: DbSession):
    return to_page(ProductService(db).list_products(filters, admin=True), AdminProductRead)


@admin_router.get("/{product_id}", response_model=AdminProductRead)
def admin_get_product(product_id: int, db: DbSession):
    return ProductService(db).get_product(product_id, admin=True)


@admin_router.post("", response_model=AdminProductRead, status_code=status.HTTP_201_CREATED)
def admin_create_product(data: ProductCreate, db: DbSession):
    return ProductService(db).create_product(data)


@admin_router.patch("/{product_id}", response_model=AdminProductRead)
def admin_update_product(product_id: int, data: ProductUpdate, db: DbSession):
    return ProductService(db).update_product(product_id, data)


@admin_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_deactivate_product(product_id: int, db: DbSession):
    """Soft delete (status -> INACTIVE)."""
    ProductService(db).deactivate_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
