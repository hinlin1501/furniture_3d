from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.product import ImageType, ProductStatus
from app.schemas.category import CategoryBrief

# NOTE: monetary values (Decimal) are serialised as JSON strings, e.g. "4990000.00",
# to avoid floating point errors. The frontend should parse/format them explicitly.


# ----------------------------- read schemas -----------------------------
class DimensionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    alt_text: str | None
    image_type: ImageType
    is_primary: bool
    display_order: int


class ModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    glb_url: str
    usdz_url: str | None
    file_size_bytes: int | None
    is_active: bool


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    price: Decimal
    currency: str
    category: CategoryBrief
    primary_image_url: str | None
    stock_status: str
    is_available: bool
    has_3d_model: bool
    dimension: DimensionRead | None
    materials: list[str]
    styles: list[str]
    colors: list[str]


class ProductDetail(ProductListItem):
    description: str | None
    images: list[ImageRead]
    models: list[ModelRead]


class AdminProductRead(ProductDetail):
    stock_quantity: int
    status: ProductStatus
    created_at: datetime
    updated_at: datetime


class ProductAssets(BaseModel):
    product_id: int
    images: list[ImageRead]
    models: list[ModelRead]


# ----------------------------- query params -----------------------------
class ProductSortBy(str, Enum):
    newest = "newest"
    price_asc = "price_asc"
    price_desc = "price_desc"
    name_asc = "name_asc"


class ProductFilterParams(BaseModel):
    q: str | None = Field(default=None, max_length=100, description="Keyword search")
    category_id: int | None = Field(default=None, ge=1)
    include_subcategories: bool = True
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    material: list[str] = Field(default_factory=list, max_length=10)
    style: list[str] = Field(default_factory=list, max_length=10)
    color: list[str] = Field(default_factory=list, max_length=10)
    min_length_cm: Decimal | None = Field(default=None, ge=0)
    max_length_cm: Decimal | None = Field(default=None, ge=0)
    min_width_cm: Decimal | None = Field(default=None, ge=0)
    max_width_cm: Decimal | None = Field(default=None, ge=0)
    min_height_cm: Decimal | None = Field(default=None, ge=0)
    max_height_cm: Decimal | None = Field(default=None, ge=0)
    in_stock_only: bool = False
    sort: ProductSortBy = ProductSortBy.newest
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def _ranges(self) -> "ProductFilterParams":
        for lo, hi in (
            ("min_price", "max_price"),
            ("min_length_cm", "max_length_cm"),
            ("min_width_cm", "max_width_cm"),
            ("min_height_cm", "max_height_cm"),
        ):
            a, b = getattr(self, lo), getattr(self, hi)
            if a is not None and b is not None and a > b:
                raise ValueError(f"{lo} must be <= {hi}")
        return self


class AdminProductFilterParams(ProductFilterParams):
    status: ProductStatus | None = None


# ----------------------------- write schemas -----------------------------
class DimensionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_cm: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    width_cm: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    height_cm: Decimal = Field(gt=0, max_digits=8, decimal_places=2)


class DimensionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_cm: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    width_cm: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    height_cm: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)


def _clean_tags(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    for v in values:
        if len(" ".join(v.split())) > 100:
            raise ValueError("Attribute value too long (max 100 chars)")
    return values


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._\-]*$")
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="VND", pattern=r"^[A-Z]{3}$")
    stock_quantity: int = Field(default=0, ge=0)
    category_id: int = Field(ge=1)
    status: ProductStatus = ProductStatus.ACTIVE
    dimension: DimensionInput
    materials: list[str] = Field(default_factory=list, max_length=20)
    styles: list[str] = Field(default_factory=list, max_length=20)
    colors: list[str] = Field(default_factory=list, max_length=20)

    _tags = field_validator("materials", "styles", "colors")(_clean_tags)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("name must not be blank")
        return v


class ProductUpdate(BaseModel):
    """Partial update. SKU is immutable. Provided attribute lists REPLACE the stored ones."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    stock_quantity: int | None = Field(default=None, ge=0)
    category_id: int | None = Field(default=None, ge=1)
    status: ProductStatus | None = None
    dimension: DimensionPatch | None = None
    materials: list[str] | None = Field(default=None, max_length=20)
    styles: list[str] | None = Field(default=None, max_length=20)
    colors: list[str] | None = Field(default=None, max_length=20)

    _tags = field_validator("materials", "styles", "colors")(_clean_tags)

    @model_validator(mode="after")
    def _no_null_required(self) -> "ProductUpdate":
        for f in ("name", "price", "currency", "stock_quantity", "category_id", "status"):
            if f in self.model_fields_set and getattr(self, f) is None:
                raise ValueError(f"{f} must not be null")
        return self
