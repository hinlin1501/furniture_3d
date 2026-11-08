from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.product import (
    AttributeType,
    Product,
    ProductAttribute,
    ProductDimension,
    ProductStatus,
)
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import PageResult
from app.schemas.product import (
    AdminProductFilterParams,
    ProductAssets,
    ProductCreate,
    ProductFilterParams,
    ProductUpdate,
)
from app.utils.text import normalize_spaces


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        clean = normalize_spaces(v)
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            out.append(clean)
    return out


def _build_attributes(
    materials: list[str], styles: list[str], colors: list[str]
) -> list[ProductAttribute]:
    attrs: list[ProductAttribute] = []
    for kind, values in (
        (AttributeType.MATERIAL, materials),
        (AttributeType.STYLE, styles),
        (AttributeType.COLOR, colors),
    ):
        attrs.extend(ProductAttribute(attribute_type=kind, value=v) for v in _dedupe(values))
    return attrs


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.categories = CategoryRepository(db)

    # ------------------------------ queries ------------------------------
    def list_products(self, f: ProductFilterParams, *, admin: bool = False) -> PageResult:
        category_ids = None
        if f.category_id is not None:
            category_ids = [f.category_id]
            if f.include_subcategories:
                category_ids += self.categories.descendant_ids(f.category_id)
        status = f.status if isinstance(f, AdminProductFilterParams) else None
        items, total = self.products.search(
            f, include_inactive=admin, status=status, category_ids=category_ids
        )
        return PageResult(items, total, f.page, f.page_size)

    def get_product(self, product_id: int, *, admin: bool = False) -> Product:
        product = self.products.get(product_id, include_inactive=admin)
        if product is None:
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        return product

    def get_assets(self, product_id: int) -> ProductAssets:
        product = self.get_product(product_id)
        return ProductAssets.model_validate(
            {"product_id": product.id, "images": product.images, "models": product.models},
            from_attributes=True,
        )

    # ------------------------------ commands -----------------------------
    def create_product(self, data: ProductCreate) -> Product:
        category = self.categories.get(data.category_id)
        if category is None or not category.is_active:
            raise BusinessRuleError("Category does not exist or is inactive", code="INVALID_CATEGORY")
        if self.products.get_by_sku(data.sku):
            raise ConflictError("SKU already exists", code="SKU_ALREADY_EXISTS")

        product = Product(
            sku=data.sku,
            name=data.name,
            description=data.description,
            price=data.price,
            currency=data.currency,
            stock_quantity=data.stock_quantity,
            status=data.status,
            category_id=data.category_id,
            dimension=ProductDimension(**data.dimension.model_dump()),
            attributes=_build_attributes(data.materials, data.styles, data.colors),
        )
        try:
            self.products.add(product)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("SKU already exists", code="SKU_ALREADY_EXISTS") from exc
        return self._reload(product.id)

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get_product(product_id, admin=True)
        changes = data.model_dump(exclude_unset=True)

        if "category_id" in changes:
            category = self.categories.get(changes["category_id"])
            if category is None or not category.is_active:
                raise BusinessRuleError(
                    "Category does not exist or is inactive", code="INVALID_CATEGORY"
                )
            product.category_id = changes["category_id"]

        for field in ("name", "description", "price", "currency", "stock_quantity", "status"):
            if field in changes:
                setattr(product, field, changes[field])
        if "name" in changes:
            product.name = normalize_spaces(changes["name"])

        if "dimension" in changes and changes["dimension"]:
            for k, v in changes["dimension"].items():
                if v is not None and product.dimension is not None:
                    setattr(product.dimension, k, v)

        for kind, key in (
            (AttributeType.MATERIAL, "materials"),
            (AttributeType.STYLE, "styles"),
            (AttributeType.COLOR, "colors"),
        ):
            if changes.get(key) is not None:
                self._sync_attributes(product, kind, changes[key])

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Product update violates a constraint") from exc
        return self._reload(product.id)

    def deactivate_product(self, product_id: int) -> None:
        """Soft delete: products are never physically removed (historical orders, Phase 4)."""
        product = self.get_product(product_id, admin=True)
        product.status = ProductStatus.INACTIVE
        self.db.commit()

    # ------------------------------ helpers ------------------------------
    @staticmethod
    def _sync_attributes(product: Product, kind: AttributeType, values: list[str]) -> None:
        """Diff-based replace so retained values are not deleted+reinserted
        (which would violate the unique constraint within one flush)."""
        wanted = {v.lower(): v for v in _dedupe(values)}
        current = [a for a in product.attributes if a.attribute_type == kind]
        for attr in current:
            if attr.value.lower() not in wanted:
                product.attributes.remove(attr)
        existing = {a.value.lower() for a in current}
        for low, value in wanted.items():
            if low not in existing:
                product.attributes.append(ProductAttribute(attribute_type=kind, value=value))

    def _reload(self, product_id: int) -> Product:
        self.db.expire_all()
        return self.get_product(product_id, admin=True)
