from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.text import slugify


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    # ---- queries ----
    def list_all(self, *, include_inactive: bool = False) -> list[Category]:
        return self.repo.list_all(include_inactive=include_inactive)

    def get(self, category_id: int, *, include_inactive: bool = False) -> Category:
        cat = self.repo.get(category_id)
        if cat is None or (not cat.is_active and not include_inactive):
            raise NotFoundError("Category not found", code="CATEGORY_NOT_FOUND")
        return cat

    # ---- commands (admin) ----
    def create(self, data: CategoryCreate) -> Category:
        slug = data.slug or slugify(data.name)
        if not slug:
            raise BusinessRuleError("Cannot derive a slug from the name; provide one", code="INVALID_SLUG")
        self._ensure_unique(name=data.name, slug=slug)
        if data.parent_id is not None:
            self.get(data.parent_id, include_inactive=True)  # 404 if parent missing
        cat = Category(
            name=data.name,
            slug=slug,
            description=data.description,
            parent_id=data.parent_id,
            display_order=data.display_order,
            is_active=data.is_active,
        )
        return self._commit(cat, add=True)

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        cat = self.get(category_id, include_inactive=True)
        changes = data.model_dump(exclude_unset=True)

        if changes.get("name") is None:
            changes.pop("name", None)
        if changes.get("display_order") is None:
            changes.pop("display_order", None)
        if changes.get("is_active") is None:
            changes.pop("is_active", None)
        if "slug" in changes and changes["slug"] is None:
            changes.pop("slug")

        self._ensure_unique(
            name=changes.get("name"), slug=changes.get("slug"), exclude_id=cat.id
        )

        if "parent_id" in changes and changes["parent_id"] is not None:
            parent_id = changes["parent_id"]
            if parent_id == cat.id or parent_id in self.repo.descendant_ids(cat.id):
                raise BusinessRuleError(
                    "A category cannot be its own ancestor", code="CATEGORY_CYCLE"
                )
            self.get(parent_id, include_inactive=True)

        if changes.get("is_active") is False and cat.is_active:
            if self.repo.count_products(cat.id, active_only=True):
                raise ConflictError(
                    "Cannot deactivate a category that still has active products",
                    code="CATEGORY_HAS_ACTIVE_PRODUCTS",
                )

        for k, v in changes.items():
            setattr(cat, k, v)
        return self._commit(cat)

    def delete(self, category_id: int) -> None:
        cat = self.get(category_id, include_inactive=True)
        if self.repo.count_products(cat.id, active_only=True):
            raise ConflictError(
                "Cannot delete a category that still has active products",
                code="CATEGORY_HAS_ACTIVE_PRODUCTS",
            )
        if self.repo.count_products(cat.id, active_only=False):
            raise ConflictError(
                "Category is referenced by inactive products; deactivate it instead of deleting",
                code="CATEGORY_HAS_PRODUCTS",
            )
        if self.repo.count_children(cat.id):
            raise ConflictError(
                "Cannot delete a category that has sub-categories",
                code="CATEGORY_HAS_CHILDREN",
            )
        self.repo.delete(cat)
        self.db.commit()

    # ---- helpers ----
    def _ensure_unique(
        self, *, name: str | None, slug: str | None, exclude_id: int | None = None
    ) -> None:
        if name:
            other = self.repo.get_by_name(name)
            if other and other.id != exclude_id:
                raise ConflictError("Category name already exists", code="CATEGORY_NAME_EXISTS")
        if slug:
            other = self.repo.get_by_slug(slug)
            if other and other.id != exclude_id:
                raise ConflictError("Category slug already exists", code="CATEGORY_SLUG_EXISTS")

    def _commit(self, cat: Category, *, add: bool = False) -> Category:
        try:
            if add:
                self.repo.add(cat)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Category name or slug already exists") from exc
        self.db.refresh(cat)
        return cat
