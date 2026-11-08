from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.product import (
    AttributeType,
    Product,
    ProductAttribute,
    ProductDimension,
    ProductStatus,
)
from app.schemas.product import ProductFilterParams, ProductSortBy
from app.utils.text import escape_like

LOAD_OPTIONS = (
    selectinload(Product.category),
    selectinload(Product.dimension),
    selectinload(Product.images),
    selectinload(Product.models),
    selectinload(Product.attributes),
)

_ORDER = {
    ProductSortBy.newest: lambda: (Product.created_at.desc(), Product.id.desc()),
    ProductSortBy.price_asc: lambda: (Product.price.asc(), Product.id.asc()),
    ProductSortBy.price_desc: lambda: (Product.price.desc(), Product.id.asc()),
    ProductSortBy.name_asc: lambda: (func.lower(Product.name).asc(), Product.id.asc()),
}


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, product_id: int, *, include_inactive: bool = False) -> Product | None:
        stmt = select(Product).where(Product.id == product_id).options(*LOAD_OPTIONS)
        if not include_inactive:
            stmt = stmt.where(Product.status == ProductStatus.ACTIVE)
        return self.db.scalar(stmt)

    def get_by_sku(self, sku: str) -> Product | None:
        return self.db.scalar(select(Product).where(func.lower(Product.sku) == sku.lower()))

    def add(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        return product

    def search(
        self,
        f: ProductFilterParams,
        *,
        include_inactive: bool = False,
        status: ProductStatus | None = None,
        category_ids: list[int] | None = None,
    ) -> tuple[list[Product], int]:
        conds = []
        if not include_inactive:
            conds.append(Product.status == ProductStatus.ACTIVE)
        elif status is not None:
            conds.append(Product.status == status)

        if category_ids:
            conds.append(Product.category_id.in_(category_ids))
        if f.min_price is not None:
            conds.append(Product.price >= f.min_price)
        if f.max_price is not None:
            conds.append(Product.price <= f.max_price)
        if f.in_stock_only:
            conds.append(Product.stock_quantity > 0)

        # keyword search: every token must match name / description / sku / any attribute
        for token in (f.q or "").split():
            pattern = f"%{escape_like(token)}%"
            conds.append(
                or_(
                    Product.name.ilike(pattern, escape="\\"),
                    Product.description.ilike(pattern, escape="\\"),
                    Product.sku.ilike(pattern, escape="\\"),
                    Product.attributes.any(ProductAttribute.value.ilike(pattern, escape="\\")),
                )
            )

        # attribute filters: OR within one attribute type, AND across types
        for kind, values in (
            (AttributeType.MATERIAL, f.material),
            (AttributeType.STYLE, f.style),
            (AttributeType.COLOR, f.color),
        ):
            lowered = [v.strip().lower() for v in values if v.strip()]
            if lowered:
                conds.append(
                    Product.attributes.any(
                        and_(
                            ProductAttribute.attribute_type == kind,
                            func.lower(ProductAttribute.value).in_(lowered),
                        )
                    )
                )

        dim_conds = []
        for col, lo, hi in (
            (ProductDimension.length_cm, f.min_length_cm, f.max_length_cm),
            (ProductDimension.width_cm, f.min_width_cm, f.max_width_cm),
            (ProductDimension.height_cm, f.min_height_cm, f.max_height_cm),
        ):
            if lo is not None:
                dim_conds.append(col >= lo)
            if hi is not None:
                dim_conds.append(col <= hi)
        if dim_conds:
            conds.append(Product.dimension.has(and_(*dim_conds)))

        where = and_(*conds) if conds else True
        total = int(self.db.scalar(select(func.count()).select_from(Product).where(where)) or 0)
        stmt = (
            select(Product)
            .where(where)
            .order_by(*_ORDER[f.sort]())
            .offset((f.page - 1) * f.page_size)
            .limit(f.page_size)
            .options(*LOAD_OPTIONS)
        )
        return list(self.db.scalars(stmt)), total
