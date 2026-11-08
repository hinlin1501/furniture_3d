from decimal import Decimal
from datetime import timedelta

import pytest

from app.models import Order, Payment, PaymentStatus
from app.services.payment_gateway import sign_result

API = "/api/v1"
SHIPPING = {"recipient_name": "Nguyen Van A", "phone": "0901234567", "address": "12 Le Loi, Q1, TP.HCM"}


@pytest.fixture
def category(make_category):
    return make_category("Sofa")


def add(client, h, pid, qty=1):
    assert client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": qty}, headers=h).status_code == 201


def start(client, h, shipping=SHIPPING, method="SANDBOX_CARD"):
    return client.post(f"{API}/checkout", json={"shipping": shipping, "payment_method": method}, headers=h)


def confirm(client, h, payment_id, outcome="SUCCESS"):
    return client.post(f"{API}/payments/{payment_id}/sandbox-confirm", json={"outcome": outcome}, headers=h)


def cart_items(client, h):
    return client.get(f"{API}/cart", headers=h).json()["items"]


def stock_of(db, p):
    db.refresh(p)
    return p.stock_quantity


def code(r):
    return r.json()["error"]["code"]


def test_empty_cart_cannot_checkout(client, customer_headers):
    r = client.post(f"{API}/checkout/validate", headers=customer_headers)
    assert r.status_code == 422 and code(r) == "CART_EMPTY"
    assert start(client, customer_headers).status_code == 422


def test_invalid_shipping_rejected(client, customer_headers, category, make_product):
    add(client, customer_headers, make_product(category).id)
    assert start(client, customer_headers, {**SHIPPING, "phone": "123"}).status_code == 422
    assert start(client, customer_headers, {**SHIPPING, "address": "  "}).status_code == 422


def test_success_creates_order_deducts_stock_clears_cart(client, customer_headers, db, category, make_product):
    p1 = make_product(category, price="10000000", stock=5)
    p2 = make_product(category, price="2000000", stock=3)
    add(client, customer_headers, p1.id, 2)
    add(client, customer_headers, p2.id, 1)
    pay = start(client, customer_headers).json()
    assert Decimal(pay["amount"]) == Decimal("22000000") and pay["status"] == "PENDING"
    assert stock_of(db, p1) == 5  # chưa trừ kho trước khi thanh toán thành công

    r = confirm(client, customer_headers, pay["payment_id"]).json()
    assert r["status"] == "SUCCESS" and r["order_code"].startswith("ORD-")
    assert stock_of(db, p1) == 3 and stock_of(db, p2) == 2
    assert cart_items(client, customer_headers) == []

    order = client.get(f"{API}/orders/{r['order_id']}", headers=customer_headers).json()
    assert order["status"] == "CONFIRMED" and Decimal(order["total_amount"]) == Decimal("22000000")
    assert [i["quantity"] for i in order["items"]] == [2, 1]
    assert order["recipient_name"] == SHIPPING["recipient_name"] and len(order["history"]) == 1


def test_duplicate_confirmation_is_idempotent(client, customer_headers, db, category, make_product):
    p = make_product(category, stock=5)
    add(client, customer_headers, p.id, 2)
    pid = start(client, customer_headers).json()["payment_id"]
    first = confirm(client, customer_headers, pid).json()
    second = confirm(client, customer_headers, pid).json()
    assert first["order_id"] == second["order_id"]
    assert stock_of(db, p) == 3
    assert db.query(Order).count() == 1


def test_failed_payment_keeps_cart_and_stock_and_can_retry(client, customer_headers, db, category, make_product):
    p = make_product(category, stock=5)
    add(client, customer_headers, p.id, 2)
    pid = start(client, customer_headers).json()["payment_id"]
    r = confirm(client, customer_headers, pid, "FAILED").json()
    assert r["status"] == "FAILED" and r["order_id"] is None
    assert stock_of(db, p) == 5 and len(cart_items(client, customer_headers)) == 1
    assert client.get(f"{API}/orders", headers=customer_headers).json()["total"] == 0
    pid2 = start(client, customer_headers).json()["payment_id"]
    assert confirm(client, customer_headers, pid2).json()["status"] == "SUCCESS"
    assert stock_of(db, p) == 3


def test_expired_payment(client, customer_headers, db, category, make_product):
    p = make_product(category, stock=5)
    add(client, customer_headers, p.id)
    pid = start(client, customer_headers).json()["payment_id"]
    assert confirm(client, customer_headers, pid, "EXPIRED").json()["status"] == "EXPIRED"
    assert stock_of(db, p) == 5


def test_real_time_expiry(client, customer_headers, db, category, make_product):
    from datetime import datetime, timezone
    p = make_product(category, stock=5)
    add(client, customer_headers, p.id)
    pid = start(client, customer_headers).json()["payment_id"]
    pay = db.get(Payment, pid)
    pay.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    assert confirm(client, customer_headers, pid).json()["status"] == "EXPIRED"
    assert stock_of(db, p) == 5


def test_sold_out_between_checkout_and_payment_refunds(client, customer_headers, db, make_user, auth_headers,
                                                       category, make_product):
    p = make_product(category, stock=3)
    other = auth_headers(make_user("other@example.com"))
    add(client, customer_headers, p.id, 3)
    pid_a = start(client, customer_headers).json()["payment_id"]
    add(client, other, p.id, 3)
    pid_b = start(client, other).json()["payment_id"]
    assert confirm(client, other, pid_b).json()["status"] == "SUCCESS"
    r = confirm(client, customer_headers, pid_a).json()
    assert r["status"] == "REFUNDED" and r["order_id"] is None
    assert stock_of(db, p) == 0 and db.query(Order).count() == 1


def test_partial_stock_failure_rolls_back_all_deductions(client, customer_headers, db, category, make_product):
    p1 = make_product(category, stock=5)
    p2 = make_product(category, stock=5)
    add(client, customer_headers, p1.id, 2)
    add(client, customer_headers, p2.id, 3)
    pid = start(client, customer_headers).json()["payment_id"]
    p2.stock_quantity = 1  # p2 bị bán bớt sau khi mở phiên thanh toán
    db.commit()
    assert confirm(client, customer_headers, pid).json()["status"] == "REFUNDED"
    assert stock_of(db, p1) == 5 and stock_of(db, p2) == 1  # p1 không bị trừ dở dang


def test_checkout_blocked_when_cart_has_issues(client, customer_headers, db, category, make_product):
    p = make_product(category, stock=5)
    add(client, customer_headers, p.id, 3)
    p.stock_quantity = 1
    db.commit()
    r = start(client, customer_headers)
    assert r.status_code == 409 and code(r) == "CART_INVALID"
    assert client.post(f"{API}/checkout/validate", headers=customer_headers).json()["valid"] is False


def test_additions_after_session_are_kept(client, customer_headers, category, make_product):
    p = make_product(category, stock=5)
    add(client, customer_headers, p.id, 1)
    pid = start(client, customer_headers).json()["payment_id"]
    add(client, customer_headers, p.id, 1)  # khách thêm tiếp trong lúc đang thanh toán
    confirm(client, customer_headers, pid)
    items = cart_items(client, customer_headers)
    assert len(items) == 1 and items[0]["quantity"] == 1


def test_new_session_supersedes_pending(client, customer_headers, category, make_product):
    add(client, customer_headers, make_product(category).id)
    p1 = start(client, customer_headers).json()["payment_id"]
    p2 = start(client, customer_headers).json()["payment_id"]
    assert client.get(f"{API}/payments/{p1}", headers=customer_headers).json()["status"] == "EXPIRED"
    assert confirm(client, customer_headers, p2).json()["status"] == "SUCCESS"


def test_cannot_access_others_payment(client, customer_headers, make_user, auth_headers, category, make_product):
    add(client, customer_headers, make_product(category).id)
    pid = start(client, customer_headers).json()["payment_id"]
    other = auth_headers(make_user("other@example.com"))
    assert confirm(client, other, pid).status_code == 404
    assert client.get(f"{API}/payments/{pid}", headers=other).status_code == 404


def test_webhook_signature_amount_and_success(client, customer_headers, db, category, make_product):
    p = make_product(category, price="1000000", stock=5)
    add(client, customer_headers, p.id)
    s = start(client, customer_headers).json()
    amt = Decimal(s["amount"])
    body = {"gateway_ref": s["gateway_ref"], "result": "SUCCESS", "amount": str(amt)}

    r = client.post(f"{API}/payments/webhook", json=body, headers={"X-Signature": "bad"})
    assert r.status_code == 401 and code(r) == "INVALID_SIGNATURE"
    assert stock_of(db, p) == 5

    bad = {**body, "amount": "1.00"}  # đúng chữ ký nhưng sai số tiền
    sig = sign_result(s["gateway_ref"], "SUCCESS", Decimal("1.00"))
    r = client.post(f"{API}/payments/webhook", json=bad, headers={"X-Signature": sig}).json()
    assert r["status"] == "FAILED" and stock_of(db, p) == 5

    # phiên đã FAILED: kết quả hợp lệ đến sau không làm gì (idempotent)
    sig = sign_result(s["gateway_ref"], "SUCCESS", amt)
    r = client.post(f"{API}/payments/webhook", json=body, headers={"X-Signature": sig}).json()
    assert r["status"] == "FAILED" and stock_of(db, p) == 5


def test_webhook_success(client, customer_headers, db, category, make_product):
    p = make_product(category, price="1000000", stock=5)
    add(client, customer_headers, p.id)
    s = start(client, customer_headers).json()
    sig = sign_result(s["gateway_ref"], "SUCCESS", Decimal(s["amount"]))
    body = {"gateway_ref": s["gateway_ref"], "result": "SUCCESS", "amount": s["amount"]}
    r = client.post(f"{API}/payments/webhook", json=body, headers={"X-Signature": sig}).json()
    assert r["status"] == "SUCCESS" and stock_of(db, p) == 4
