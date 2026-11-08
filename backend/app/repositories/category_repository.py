from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product, ProductStatus


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def get_by_name(self, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))

    def get_by_slug(self, slug: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.slug == slug))

    def list_all(self, *, include_inactive: bool = False) -> list[Category]:
        stmt = select(Category).order_by(Category.display_order, Category.name)
        if not include_inactive:
            stmt = stmt.where(Category.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def child_ids(self, parent_ids: list[int]) -> list[int]:
        if not parent_ids:
            return []
        return list(self.db.scalars(select(Category.id).where(Category.parent_id.in_(parent_ids))))

    def descendant_ids(self, category_id: int) -> list[int]:
        """All descendants (excluding the category itself). Guards against cycles."""
        seen: set[int] = {category_id}
        frontier = [category_id]
        result: list[int] = []
        while frontier:
            frontier = [i for i in self.child_ids(frontier) if i not in seen]
            seen.update(frontier)
            result.extend(frontier)
        return result

    def count_products(self, category_id: int, *, active_only: bool) -> int:
        stmt = select(func.count()).select_from(Product).where(Product.category_id == category_id)
        if active_only:
            stmt = stmt.where(Product.status == ProductStatus.ACTIVE)
        return int(self.db.scalar(stmt) or 0)

    def count_children(self, category_id: int) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(Category).where(Category.parent_id == category_id)
            )
            or 0
        )

    def add(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.flush()
