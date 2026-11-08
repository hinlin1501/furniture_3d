from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import DbSession, require_manager
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])
admin_router = APIRouter(
    prefix="/admin/categories", tags=["Admin – Categories"], dependencies=[Depends(require_manager)]
)


@router.get("", response_model=list[CategoryRead])
def list_categories(db: DbSession):
    """FR-05. Active categories (flat list; use parent_id to build the tree)."""
    return CategoryService(db).list_all()


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: DbSession):
    return CategoryService(db).get(category_id)


@admin_router.get("", response_model=list[CategoryRead])
def admin_list_categories(db: DbSession):
    return CategoryService(db).list_all(include_inactive=True)


@admin_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def admin_create_category(data: CategoryCreate, db: DbSession):
    return CategoryService(db).create(data)


@admin_router.patch("/{category_id}", response_model=CategoryRead)
def admin_update_category(category_id: int, data: CategoryUpdate, db: DbSession):
    return CategoryService(db).update(category_id, data)


@admin_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_category(category_id: int, db: DbSession):
    CategoryService(db).delete(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
