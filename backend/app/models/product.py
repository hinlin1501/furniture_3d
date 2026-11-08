import enum
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.category import Category

LOW_STOCK_THRESHOLD = 5
MAX_GLB_BYTES = 15 * 1024 * 1024  # NFR-10


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"  # soft delete / hidden from catalog


class ImageType(str, enum.Enum):
    GALLERY = "GALLERY"
    VIEW_360 = "VIEW_360"


class AttributeType(str, enum.Enum):
    MATERIAL = "MATERIAL"
    STYLE = "STYLE"
    COLOR = "COLOR"


def _enum(e: type[enum.Enum], name: str) -> Enum:
    return Enum(e, name=name, native_enum=False, length=20, create_constraint=True)


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint("stock_quantity >= 0", name="stock_non_negative"),
        Index("ix_products_category_status", "category_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="VND", server_default="VND")
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[ProductStatus] = mapped_column(
        _enum(ProductStatus, "product_status"),
        default=ProductStatus.ACTIVE,
        server_default=ProductStatus.ACTIVE.value,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))

    category: Mapped[Category] = relationship()
    dimension: Mapped["ProductDimension | None"] = relationship(
        back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.display_order, ProductImage.id",
    )
    models: Mapped[list["ProductModel"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductModel.id"
    )
    attributes: Mapped[list["ProductAttribute"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductAttribute.value"
    )

    # ---- derived read-only helpers (used by response schemas) ----
    @property
    def is_available(self) -> bool:
        return self.status == ProductStatus.ACTIVE and self.stock_quantity > 0

    @property
    def stock_status(self) -> str:
        if self.stock_quantity <= 0:
            return "OUT_OF_STOCK"
        if self.stock_quantity <= LOW_STOCK_THRESHOLD:
            return "LOW_STOCK"
        return "IN_STOCK"

    def _attr_values(self, kind: AttributeType) -> list[str]:
        return [a.value for a in self.attributes if a.attribute_type == kind]

    @property
    def materials(self) -> list[str]:
        return self._attr_values(AttributeType.MATERIAL)

    @property
    def styles(self) -> list[str]:
        return self._attr_values(AttributeType.STYLE)

    @property
    def colors(self) -> list[str]:
        return self._attr_values(AttributeType.COLOR)

    @property
    def primary_image_url(self) -> str | None:
        gallery = [i for i in self.images if i.image_type == ImageType.GALLERY]
        for img in gallery:
            if img.is_primary:
                return img.url
        return gallery[0].url if gallery else None

    @property
    def has_3d_model(self) -> bool:
        return any(m.is_active for m in self.models)


class ProductDimension(Base):
    """1-to-1 with Product. All values in centimetres."""

    __tablename__ = "product_dimensions"
    __table_args__ = (
        CheckConstraint("length_cm > 0", name="length_positive"),
        CheckConstraint("width_cm > 0", name="width_positive"),
        CheckConstraint("height_cm > 0", name="height_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), unique=True
    )
    length_cm: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    width_cm: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    height_cm: Mapped[Decimal] = mapped_column(Numeric(8, 2))

    product: Mapped[Product] = relationship(back_populates="dimension")


class ProductImage(Base, TimestampMixin):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(1024))
    alt_text: Mapped[str | None] = mapped_column(String(255))
    image_type: Mapped[ImageType] = mapped_column(
        _enum(ImageType, "image_type"),
        default=ImageType.GALLERY,
        server_default=ImageType.GALLERY.value,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    product: Mapped[Product] = relationship(back_populates="images")


class ProductModel(Base, TimestampMixin):
    """3D asset (GLB for web/Android, optional USDZ for iOS Quick Look)."""

    __tablename__ = "product_models"
    __table_args__ = (
        CheckConstraint(
            f"file_size_bytes IS NULL OR file_size_bytes <= {MAX_GLB_BYTES}",
            name="glb_size_limit",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    glb_url: Mapped[str] = mapped_column(String(1024))
    usdz_url: Mapped[str | None] = mapped_column(String(1024))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    product: Mapped[Product] = relationship(back_populates="models")


class ProductAttribute(Base):
    """Material / style / colour tags used for filtering and AI feature matching."""

    __tablename__ = "product_attributes"
    __table_args__ = (
        UniqueConstraint("product_id", "attribute_type", "value", name="uq_product_attr"),
        Index("ix_product_attributes_type_value", "attribute_type", "value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    attribute_type: Mapped[AttributeType] = mapped_column(_enum(AttributeType, "attribute_type"))
    value: Mapped[str] = mapped_column(String(100))

    product: Mapped[Product] = relationship(back_populates="attributes")


