"""Provision the first STORE_MANAGER account (and optional demo catalog).

Usage (from backend/):
    SEED_MANAGER_EMAIL=... SEED_MANAGER_PASSWORD=... python -m scripts.seed [--demo]

Idempotent: existing rows are left untouched. Demo data is clearly marked (SKU prefix "DEMO-")
and contains NO real 3D assets or images - those arrive with Phase 3.
"""
import argparse
import os
import sys
from decimal import Decimal

from app.core.security import hash_password
from app.database.session import get_session_factory
from app.models import (
    AttributeType,
    Category,
    Product,
    ProductAttribute,
    ProductDimension,
    User,
    UserRole,
)
from app.repositories.product_repository import ProductRepository
from app.utils.text import slugify

DEMO = [
    # (category, parent, sku, name, price, stock, (L, W, H), materials, styles, colors)
    ("Phòng khách", None, None, None, None, None, None, None, None, None),
    ("Sofa", "Phòng khách", "DEMO-SOFA-001", "Sofa Bắc Âu 3 chỗ", "12990000", 8, (210, 90, 85), ["Vải bố", "Gỗ sồi"], ["Scandinavian"], ["Be", "Trắng"]),
    ("Bàn trà", "Phòng khách", "DEMO-TBL-001", "Bàn trà tròn gỗ óc chó", "3490000", 15, (80, 80, 40), ["Gỗ óc chó"], ["Minimalism"], ["Nâu"]),
    ("Phòng ngủ", None, None, None, None, None, None, None, None, None),
    ("Giường", "Phòng ngủ", "DEMO-BED-001", "Giường ngủ 1m6 phong cách Industrial", "9990000", 4, (210, 170, 90), ["Thép", "Gỗ công nghiệp"], ["Industrial"], ["Đen"]),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="also insert a tiny demo catalog")
    args = parser.parse_args()

    email = os.environ.get("SEED_MANAGER_EMAIL", "").strip().lower()
    password = os.environ.get("SEED_MANAGER_PASSWORD", "")
    if not email or len(password) < 8:
        print("SEED_MANAGER_EMAIL and SEED_MANAGER_PASSWORD (>= 8 chars) are required", file=sys.stderr)
        return 1

    db = get_session_factory()()
    try:
        if db.query(User).filter(User.email == email).first():
            print(f"manager {email}: already exists")
        else:
            db.add(User(email=email, password_hash=hash_password(password),
                        full_name="Store Manager", role=UserRole.STORE_MANAGER))
            db.commit()
            print(f"manager {email}: created")

        if args.demo:
            cats: dict[str, Category] = {}
            for name, parent, sku, pname, price, stock, dims, mats, styles, colors in DEMO:
                cat = db.query(Category).filter(Category.name == name).first()
                if cat is None:
                    cat = Category(name=name, slug=slugify(name),
                                   parent_id=cats[parent].id if parent else None)
                    db.add(cat)
                    db.flush()
                cats[name] = cat
                if sku and not ProductRepository(db).get_by_sku(sku):
                    p = Product(sku=sku, name=pname, price=Decimal(price), stock_quantity=stock,
                                category_id=cat.id,
                                dimension=ProductDimension(length_cm=dims[0], width_cm=dims[1], height_cm=dims[2]))
                    for kind, vals in ((AttributeType.MATERIAL, mats), (AttributeType.STYLE, styles), (AttributeType.COLOR, colors)):
                        p.attributes.extend(ProductAttribute(attribute_type=kind, value=v) for v in vals)
                    db.add(p)
            db.commit()
            print("demo catalog: ensured")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
