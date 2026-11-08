from app.core.security import create_access_token
from tests.conftest import PASSWORD

REG = {"email": "New.User@Example.com", "password": PASSWORD, "full_name": "New User"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/ready").json()["database"] == "up"


def test_register_success_and_no_password_leak(client):
    r = client.post("/api/v1/auth/register", json=REG)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new.user@example.com"  # normalised
    assert body["role"] == "CUSTOMER"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_case_insensitive(client):
    assert client.post("/api/v1/auth/register", json=REG).status_code == 201
    r = client.post("/api/v1/auth/register", json={**REG, "email": "NEW.user@example.COM"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_register_rejects_weak_password_and_bad_email(client):
    assert client.post("/api/v1/auth/register", json={**REG, "password": "short1"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={**REG, "password": "onlyletters"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={**REG, "email": "nope"}).status_code == 422
    r = client.post("/api/v1/auth/register", json={**REG, "phone": "abc"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_cannot_set_role(client):
    r = client.post("/api/v1/auth/register", json={**REG, "role": "STORE_MANAGER"})
    assert r.status_code == 422


def test_login_success(client):
    client.post("/api/v1/auth/register", json=REG)
    r = client.post("/api/v1/auth/login", json={"email": "new.user@EXAMPLE.com", "password": PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"] and body["expires_in"] > 0
    assert "password_hash" not in body["user"]
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "new.user@example.com"


def test_login_failures_are_indistinguishable(client, customer, make_user):
    make_user("off@example.com", active=False)
    wrong_pw = client.post("/api/v1/auth/login", json={"email": customer.email, "password": "Wrong123456"})
    no_user = client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": PASSWORD})
    disabled = client.post("/api/v1/auth/login", json={"email": "off@example.com", "password": PASSWORD})
    for r in (wrong_pw, no_user, disabled):
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"
        assert r.headers["www-authenticate"] == "Bearer"


def test_protected_endpoint_requires_valid_token(client, customer):
    assert client.get("/api/v1/users/me").status_code == 401
    bad = client.get("/api/v1/users/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "INVALID_TOKEN"
    expired, _ = create_access_token(customer.id, expires_minutes=-1)
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_token_of_deactivated_or_deleted_user_rejected(client, db, customer, customer_headers):
    assert client.get("/api/v1/users/me", headers=customer_headers).status_code == 200
    customer.is_active = False
    db.commit()
    assert client.get("/api/v1/users/me", headers=customer_headers).status_code == 401
    db.delete(customer)
    db.commit()
    assert client.get("/api/v1/users/me", headers=customer_headers).status_code == 401


def test_update_profile(client, customer_headers):
    r = client.patch(
        "/api/v1/users/me",
        headers=customer_headers,
        json={"full_name": "  Nguyễn Văn A ", "phone": "+84 912 345 678", "shipping_address": "1 Lý Thường Kiệt"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Nguyễn Văn A"
    assert r.json()["phone"] == "+84 912 345 678"
    assert client.get("/api/v1/users/me", headers=customer_headers).json()["shipping_address"] == "1 Lý Thường Kiệt"


def test_update_profile_blocks_privileged_fields(client, customer_headers):
    for payload in ({"role": "STORE_MANAGER"}, {"email": "x@y.com"}, {"is_active": False}, {"id": 99}):
        r = client.patch("/api/v1/users/me", headers=customer_headers, json=payload)
        assert r.status_code == 422, payload
    assert client.get("/api/v1/users/me", headers=customer_headers).json()["role"] == "CUSTOMER"


def test_update_profile_validation(client, customer_headers):
    assert client.patch("/api/v1/users/me", headers=customer_headers, json={"full_name": "  "}).status_code == 422
    assert client.patch("/api/v1/users/me", headers=customer_headers, json={"phone": "12"}).status_code == 422
    ok = client.patch("/api/v1/users/me", headers=customer_headers, json={"phone": ""})
    assert ok.status_code == 200 and ok.json()["phone"] is None


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
