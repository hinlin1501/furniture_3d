from decimal import Decimal

import pytest

from app.models import ImageType, ProductStatus

API = "/api/v1"  # đổi nếu prefix của dự án khác


@pytest.fixture
def category(make_category):
    return make_category("Sofa")


def add(client, headers, product_id, qty=1):
    return client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": qty}, headers=headers)


def code(r):
    return r.json()["error"]["code"]


def test_cart_requires_auth(client):
    assert client.get(f"{API}/cart").status_code == 401


def test_manager_cannot_use_cart(client, manager_headers):
    assert client.get(f"{API}/cart", headers=manager_headers).status_code == 403


def test_empty_cart(client, customer_headers):
    body = client.get(f"{API}/cart", headers=customer_headers).json()
    assert body["items"] == [] and Decimal(body["subtotal"]) == 0 and body["has_issues"] is False


def test_add_and_subtotal(client, customer_headers, category, make_product):
    p1 = make_product(category, price="10000000", images=[("http://img/1.jpg", True, ImageType.GALLERY)])
    p2 = make_product(category, price="2000000")
    r = add(client, customer_headers, p1.id, 2)
    assert r.status_code == 201
    body = add(client, customer_headers, p2.id, 1).json()
    assert Decimal(body["subtotal"]) == Decimal("22000000")
    assert body["total_quantity"] == 3 and body["has_issues"] is False
    assert body["items"][0]["image_url"] == "http://img/1.jpg"


def test_add_existing_merges(client, customer_headers, category, make_product):
    p = make_product(category)
    add(client, customer_headers, p.id, 1)
    body = add(client, customer_headers, p.id, 2).json()
    assert len(body["items"]) == 1 and body["items"][0]["quantity"] == 3


def test_add_over_stock(client, customer_headers, category, make_product):
    p = make_product(category, stock=3)
    r = add(client, customer_headers, p.id, 4)
    assert r.status_code == 409 and code(r) == "INSUFFICIENT_STOCK"
    assert r.json()["error"]["details"] == {"available_stock": 3}
    add(client, customer_headers, p.id, 3)
    assert add(client, customer_headers, p.id, 1).status_code == 409  # cộng dồn vượt tồn kho


def test_add_unavailable_products(client, customer_headers, category, make_product):
    out = make_product(category, stock=0)
    off = make_product(category, status=ProductStatus.INACTIVE)
    assert code(add(client, customer_headers, out.id)) == "OUT_OF_STOCK"
    assert code(add(client, customer_headers, off.id)) == "PRODUCT_UNAVAILABLE"
    r = add(client, customer_headers, 99999)
    assert r.status_code == 404 and code(r) == "PRODUCT_NOT_FOUND"


def test_invalid_quantity(client, customer_headers, category, make_product):
    p = make_product(category)
    assert add(client, customer_headers, p.id, 0).status_code == 422


def test_quantity_limit(client, customer_headers, category, make_product):
    p = make_product(category, stock=500)
    r = add(client, customer_headers, p.id, 100)
    assert r.status_code == 422 and code(r) == "QUANTITY_LIMIT"


def test_update_and_remove(client, customer_headers, category, make_product):
    p = make_product(category, price="1000000", stock=5)
    item = add(client, customer_headers, p.id).json()["items"][0]
    r = client.patch(f"{API}/cart/items/{item['id']}", json={"quantity": 4}, headers=customer_headers)
    assert Decimal(r.json()["subtotal"]) == Decimal("4000000")
    r = client.patch(f"{API}/cart/items/{item['id']}", json={"quantity": 6}, headers=customer_headers)
    assert r.status_code == 409
    r = client.delete(f"{API}/cart/items/{item['id']}", headers=customer_headers)
    assert r.json()["items"] == []


def test_cannot_touch_other_users_item(client, customer_headers, make_user, auth_headers, category, make_product):
    p = make_product(category)
    item = add(client, customer_headers, p.id).json()["items"][0]
    other = auth_headers(make_user("other@example.com"))
    assert client.patch(f"{API}/cart/items/{item['id']}", json={"quantity": 2}, headers=other).status_code == 404
    assert client.delete(f"{API}/cart/items/{item['id']}", headers=other).status_code == 404


def test_clear_cart(client, customer_headers, category, make_product):
    add(client, customer_headers, make_product(category).id)
    assert client.delete(f"{API}/cart", headers=customer_headers).json()["items"] == []


def test_cart_flags_stock_drop_and_price_is_live(client, customer_headers, db, category, make_product):
    p = make_product(category, price="1000000", stock=10)
    add(client, customer_headers, p.id, 4)
    p.stock_quantity, p.price = 2, Decimal("1500000")
    db.commit()
    body = client.get(f"{API}/cart", headers=customer_headers).json()
    assert body["has_issues"] and body["items"][0]["issue"] == "INSUFFICIENT_STOCK"
    assert Decimal(body["items"][0]["unit_price"]) == Decimal("1500000")
