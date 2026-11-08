BASE = "/api/v1"


def test_public_list_shows_only_active(client, make_category):
    make_category("Sofa")
    make_category("Hidden", active=False)
    r = client.get(f"{BASE}/categories")
    assert r.status_code == 200
    assert [c["name"] for c in r.json()] == ["Sofa"]


def test_public_get_and_404_for_inactive(client, make_category):
    a = make_category("Sofa")
    h = make_category("Hidden", active=False)
    assert client.get(f"{BASE}/categories/{a.id}").json()["slug"] == "sofa"
    r = client.get(f"{BASE}/categories/{h.id}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "CATEGORY_NOT_FOUND"
    assert client.get(f"{BASE}/categories/9999").status_code == 404


def test_admin_endpoints_require_manager(client, customer_headers, manager_headers):
    payload = {"name": "Tủ"}
    assert client.post(f"{BASE}/admin/categories", json=payload).status_code == 401
    assert client.post(f"{BASE}/admin/categories", json=payload, headers=customer_headers).status_code == 403
    assert client.get(f"{BASE}/admin/categories", headers=customer_headers).status_code == 403
    assert client.post(f"{BASE}/admin/categories", json=payload, headers=manager_headers).status_code == 201


def test_create_generates_vietnamese_slug(client, manager_headers):
    r = client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "  Sofa   Phòng Khách "})
    assert r.status_code == 201
    assert r.json()["name"] == "Sofa Phòng Khách"
    assert r.json()["slug"] == "sofa-phong-khach"


def test_create_duplicates_conflict(client, manager_headers):
    client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "Sofa"})
    r = client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "SOFA"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_NAME_EXISTS"
    r = client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "Other", "slug": "sofa"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_SLUG_EXISTS"


def test_create_validation(client, manager_headers):
    assert client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": ""}).status_code == 422
    assert client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "x", "slug": "Bad Slug"}).status_code == 422
    assert client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "x", "parent_id": 999}).status_code == 404
    assert client.post(f"{BASE}/admin/categories", headers=manager_headers, json={"name": "!!!"}).json()["error"]["code"] == "INVALID_SLUG"


def test_update_category_and_rename_to_self_is_ok(client, manager_headers, make_category):
    c = make_category("Sofa")
    r = client.patch(f"{BASE}/admin/categories/{c.id}", headers=manager_headers, json={"name": "Sofa", "description": "d"})
    assert r.status_code == 200 and r.json()["description"] == "d"
    other = make_category("Bàn")
    r = client.patch(f"{BASE}/admin/categories/{other.id}", headers=manager_headers, json={"name": "sofa"})
    assert r.status_code == 409


def test_cycle_prevention(client, manager_headers, make_category):
    a = make_category("A")
    b = make_category("B", parent=a)
    c = make_category("C", parent=b)
    for target, parent in ((a, a), (a, c), (a, b)):
        r = client.patch(f"{BASE}/admin/categories/{target.id}", headers=manager_headers, json={"parent_id": parent.id})
        assert r.status_code == 422 and r.json()["error"]["code"] == "CATEGORY_CYCLE"


def test_delete_blocked_by_active_products_then_allowed(client, manager_headers, make_category, make_product):
    cat = make_category("Sofa")
    p = make_product(cat)
    r = client.delete(f"{BASE}/admin/categories/{cat.id}", headers=manager_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_HAS_ACTIVE_PRODUCTS"
    # deactivating the category is blocked too while it has active products
    r = client.patch(f"{BASE}/admin/categories/{cat.id}", headers=manager_headers, json={"is_active": False})
    assert r.status_code == 409
    # soft-delete the product -> still cannot hard-delete (history), must deactivate
    assert client.delete(f"{BASE}/admin/products/{p.id}", headers=manager_headers).status_code == 204
    r = client.delete(f"{BASE}/admin/categories/{cat.id}", headers=manager_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_HAS_PRODUCTS"
    assert client.patch(f"{BASE}/admin/categories/{cat.id}", headers=manager_headers, json={"is_active": False}).status_code == 200


def test_delete_empty_category_and_children_guard(client, manager_headers, make_category):
    parent = make_category("Parent")
    child = make_category("Child", parent=parent)
    r = client.delete(f"{BASE}/admin/categories/{parent.id}", headers=manager_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_HAS_CHILDREN"
    assert client.delete(f"{BASE}/admin/categories/{child.id}", headers=manager_headers).status_code == 204
    assert client.delete(f"{BASE}/admin/categories/{parent.id}", headers=manager_headers).status_code == 204
    assert client.delete(f"{BASE}/admin/categories/{parent.id}", headers=manager_headers).status_code == 404


def test_admin_list_includes_inactive(client, manager_headers, make_category):
    make_category("A")
    make_category("B", active=False)
    assert len(client.get(f"{BASE}/admin/categories", headers=manager_headers).json()) == 2
