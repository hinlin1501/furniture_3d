import pytest

API = "/api/v1"
SHIPPING = {"recipient_name": "Nguyen Van A", "phone": "0901234567", "address": "12 Le Loi, Q1, TP.HCM"}


@pytest.fixture
def category(make_category):
    return make_category("Sofa")


def buy(client, headers, items):
    for pid, qty in items:
        client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": qty}, headers=headers)
    pay = client.post(f"{API}/checkout", json={"shipping": SHIPPING, "payment_method": "SANDBOX_WALLET"},
                      headers=headers).json()
    return client.post(f"{API}/payments/{pay['payment_id']}/sandbox-confirm", json={"outcome": "SUCCESS"},
                       headers=headers).json()


def test_orders_require_customer(client, manager_headers):
    assert client.get(f"{API}/orders").status_code == 401
    assert client.get(f"{API}/orders", headers=manager_headers).status_code == 403


def test_empty_history(client, customer_headers):
    body = client.get(f"{API}/orders", headers=customer_headers).json()
    assert body["items"] == [] and body["total"] == 0


def test_list_detail_and_isolation(client, customer_headers, make_user, auth_headers, category, make_product):
    p1, p2 = make_product(category, stock=10), make_product(category, stock=10)
    first = buy(client, customer_headers, [(p1.id, 2), (p2.id, 1)])
    buy(client, customer_headers, [(p2.id, 1)])

    mine = client.get(f"{API}/orders", headers=customer_headers).json()
    assert mine["total"] == 2 and {o["item_count"] for o in mine["items"]} == {3, 1}
    assert mine["items"][0]["id"] > mine["items"][1]["id"]  # mới nhất trước

    detail = client.get(f"{API}/orders/{first['order_id']}", headers=customer_headers).json()
    assert detail["payment_method"] == "SANDBOX_WALLET" and len(detail["items"]) == 2

    other = auth_headers(make_user("other@example.com"))
    assert client.get(f"{API}/orders", headers=other).json()["total"] == 0
    r = client.get(f"{API}/orders/{first['order_id']}", headers=other)
    assert r.status_code == 404 and r.json()["error"]["code"] == "ORDER_NOT_FOUND"
    assert client.get(f"{API}/orders/99999", headers=customer_headers).status_code == 404


def test_pagination(client, customer_headers, category, make_product):
    p = make_product(category, stock=50)
    for _ in range(3):
        buy(client, customer_headers, [(p.id, 1)])
    page2 = client.get(f"{API}/orders?page=2&page_size=2", headers=customer_headers).json()
    assert page2["total"] == 3 and len(page2["items"]) == 1 and page2["page"] == 2
    assert client.get(f"{API}/orders?page_size=500", headers=customer_headers).status_code == 422
