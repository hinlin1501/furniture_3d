import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-test-secret-key-0123456789"
os.environ["ENVIRONMENT"] = "test"

from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import (  # noqa: E402
    AttributeType,
    Category,
    ImageType,
    Product,
    ProductAttribute,
    ProductDimension,
    ProductImage,
    ProductModel,
    ProductStatus,
    User,
    UserRole,
)

PASSWORD = "Passw0rd123"


@pytest.fixture
def engine():
    """SQLite in-memory by default; set TEST_DATABASE_URL to run against PostgreSQL."""
    from sqlalchemy import create_engine, event

    pg_url = os.environ.get("TEST_DATABASE_URL")
    if pg_url:
        eng = create_engine(pg_url, pool_pre_ping=True)
        Base.metadata.drop_all(eng)
    else:
        # in-memory SQLite needs a single shared connection
        eng = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(eng, "connect")
        def _fk(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    if pg_url:
        Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture
def client(engine):
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _make_user(db, email, role=UserRole.CUSTOMER, active=True):
    u = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        full_name="Test User",
        role=role,
        is_active=active,
    )
    db.add(u)
    db.commit()
    return u


def _headers(user):
    token, _ = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer(db):
    return _make_user(db, "customer@example.com")


@pytest.fixture
def manager(db):
    return _make_user(db, "manager@example.com", UserRole.STORE_MANAGER)


@pytest.fixture
def customer_headers(customer):
    return _headers(customer)


@pytest.fixture
def manager_headers(manager):
    return _headers(manager)


@pytest.fixture
def make_user(db):
    return lambda *a, **k: _make_user(db, *a, **k)


@pytest.fixture
def auth_headers():
    return _headers


@pytest.fixture
def make_product(db):
    counter = {"n": 0}

    def factory(
        category,
        *,
        name=None,
        price="1000000",
        stock=10,
        status=ProductStatus.ACTIVE,
        dims=(100, 50, 40),
        materials=(),
        styles=(),
        colors=(),
        description=None,
        sku=None,
        images=(),
        models=(),
    ):
        counter["n"] += 1
        n = counter["n"]
        p = Product(
            sku=sku or f"SKU-{n:03d}",
            name=name or f"Product {n}",
            description=description,
            price=Decimal(price),
            stock_quantity=stock,
            status=status,
            category_id=category.id,
            dimension=ProductDimension(length_cm=dims[0], width_cm=dims[1], height_cm=dims[2]),
        )
        for kind, vals in (
            (AttributeType.MATERIAL, materials),
            (AttributeType.STYLE, styles),
            (AttributeType.COLOR, colors),
        ):
            p.attributes.extend(ProductAttribute(attribute_type=kind, value=v) for v in vals)
        for i, (url, primary, typ) in enumerate(images):
            p.images.append(
                ProductImage(url=url, is_primary=primary, image_type=typ, display_order=i)
            )
        for glb, active in models:
            p.models.append(ProductModel(glb_url=glb, is_active=active, file_size_bytes=1024))
        db.add(p)
        db.commit()
        return p

    return factory


@pytest.fixture
def make_category(db):
    def factory(name, *, parent=None, active=True, slug=None):
        c = Category(
            name=name,
            slug=slug or name.lower().replace(" ", "-"),
            parent_id=parent.id if parent else None,
            is_active=active,
        )
        db.add(c)
        db.commit()
        return c

    return factory


__all__ = ["ImageType"]
