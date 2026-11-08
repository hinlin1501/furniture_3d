from app.models import ImageType, ProductStatus

BASE = "/api/v1"


def names(r):
    return [p["name"] for p in r.json()["items"]]


def test_list_pagination_and_default_sort(client, make_category, make_product):
    cat = make_category("Sofa")
    for i in range(5):
        make_product(cat, name=f"P{i}")
    r = client.get(f"{BASE}/products", params={"page_size": 2, "page": 2})
    body = r.json()
    assert r.status_code == 200
    assert (body["total"], body["page"], body["page_size"], body["pages"]) == (5, 2, 2, 3)
    assert len(body["items"]) == 2
    # newest first, stable tiebreak by id -> P4,P3 | P2,P1 | P0
    assert names(r) == ["P2", "P1"]
    assert client.get(f"{BASE}/products", params={"page": 9}).json()["items"] == []


def test_page_size_limits(client):
    assert client.get(f"{BASE}/products", params={"page_size": 101}).status_code == 422
    assert client.get(f"{BASE}/products", params={"page": 0}).status_code == 422


def test_only_active_products_listed(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="Visible")
    make_product(cat, name="Gone", status=ProductStatus.INACTIVE)
    assert names(client.get(f"{BASE}/products")) == ["Visible"]


def test_keyword_search_name_description_sku_attribute(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="Sofa Bắc Âu", description="Vải bố cao cấp", sku="SF-100", styles=["Scandinavian"])
    make_product(cat, name="Bàn ăn", description="Gỗ sồi", sku="BA-200", materials=["Oak"])
    q = lambda s: names(client.get(f"{BASE}/products", params={"q": s}))  # noqa: E731
    assert q("sofa") == ["Sofa Bắc Âu"]
    assert q("vải") == ["Sofa Bắc Âu"]
    assert q("ba-200") == ["Bàn ăn"]
    assert q("scandinavian") == ["Sofa Bắc Âu"]
    assert q("oak bàn") == ["Bàn ăn"]  # all tokens must match
    assert q("sofa oak") == []
    assert q("zzz") == []


def test_search_treats_wildcards_literally(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="Sofa 50% off")
    make_product(cat, name="Sofa plain")
    assert names(client.get(f"{BASE}/products", params={"q": "%"})) == ["Sofa 50% off"]
    assert names(client.get(f"{BASE}/products", params={"q": "_"})) == []


def test_search_is_sql_injection_safe(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="Sofa")
    r = client.get(f"{BASE}/products", params={"q": "'; DROP TABLE products; --"})
    assert r.status_code == 200 and r.json()["total"] == 0
    assert client.get(f"{BASE}/products").json()["total"] == 1


def test_filter_price_range(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="cheap", price="1000000")
    make_product(cat, name="mid", price="5000000")
    make_product(cat, name="pricey", price="9000000")
    r = client.get(f"{BASE}/products", params={"min_price": 2000000, "max_price": 6000000})
    assert names(r) == ["mid"]
    assert client.get(f"{BASE}/products", params={"min_price": 5000000, "max_price": 5000000}).json()["total"] == 1
    assert client.get(f"{BASE}/products", params={"min_price": 9, "max_price": 1}).status_code == 422


def test_filter_attributes_or_within_type_and_across_types(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="A", materials=["Oak"], styles=["Minimalism"], colors=["White"])
    make_product(cat, name="B", materials=["Walnut"], styles=["Minimalism"], colors=["Black"])
    make_product(cat, name="C", materials=["Oak"], styles=["Industrial"], colors=["Black"])
    get = lambda **p: sorted(names(client.get(f"{BASE}/products", params=p)))  # noqa: E731
    assert get(material="oak") == ["A", "C"]  # case-insensitive
    assert get(material=["Oak", "Walnut"]) == ["A", "B", "C"]  # OR inside a type
    assert get(material="Oak", color="Black") == ["C"]  # AND across types
    assert get(style="minimalism", color="black") == ["B"]
    assert get(color="Green") == []


def test_filter_dimensions(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="small", dims=(80, 40, 40))
    make_product(cat, name="large", dims=(220, 95, 85))
    get = lambda **p: names(client.get(f"{BASE}/products", params=p))  # noqa: E731
    assert get(max_length_cm=100) == ["small"]
    assert get(min_length_cm=200) == ["large"]
    assert get(max_length_cm=250, max_width_cm=50) == ["small"]
    assert get(min_height_cm=80, max_height_cm=90) == ["large"]


def test_filter_category_includes_subcategories(client, make_category, make_product):
    parent = make_category("Living room")
    child = make_category("Sofa", parent=parent)
    other = make_category("Bedroom")
    make_product(parent, name="in-parent")
    make_product(child, name="in-child")
    make_product(other, name="elsewhere")
    get = lambda **p: sorted(names(client.get(f"{BASE}/products", params=p)))  # noqa: E731
    assert get(category_id=parent.id) == ["in-child", "in-parent"]
    assert get(category_id=parent.id, include_subcategories="false") == ["in-parent"]
    assert get(category_id=child.id) == ["in-child"]
    assert get(category_id=9999) == []


def test_filter_in_stock_only(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="in", stock=3)
    make_product(cat, name="out", stock=0)
    assert sorted(names(client.get(f"{BASE}/products"))) == ["in", "out"]
    assert names(client.get(f"{BASE}/products", params={"in_stock_only": "true"})) == ["in"]


def test_sorting(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(cat, name="banana", price="300")
    make_product(cat, name="Apple", price="100")
    make_product(cat, name="cherry", price="200")
    get = lambda s: names(client.get(f"{BASE}/products", params={"sort": s}))  # noqa: E731
    assert get("price_asc") == ["Apple", "cherry", "banana"]
    assert get("price_desc") == ["banana", "cherry", "Apple"]
    assert get("name_asc") == ["Apple", "banana", "cherry"]  # case-insensitive
    assert get("newest") == ["cherry", "Apple", "banana"]
    assert client.get(f"{BASE}/products", params={"sort": "bogus"}).status_code == 422


def test_list_item_shape_and_stock_status(client, make_category, make_product):
    cat = make_category("Sofa")
    make_product(
        cat, name="S", stock=3, materials=["Oak"], styles=["Modern"], colors=["White"],
        images=[("http://x/1.jpg", False, ImageType.GALLERY), ("http://x/2.jpg", True, ImageType.GALLERY)],
        models=[("http://x/m.glb", True)],
    )
    make_product(cat, name="O", stock=0)
    make_product(cat, name="I", stock=50)
    items = {p["name"]: p for p in client.get(f"{BASE}/products").json()["items"]}
    s = items["S"]
    assert s["stock_status"] == "LOW_STOCK" and s["is_available"] is True
    assert items["O"]["stock_status"] == "OUT_OF_STOCK" and items["O"]["is_available"] is False
    assert items["I"]["stock_status"] == "IN_STOCK"
    assert s["primary_image_url"] == "http://x/2.jpg" and s["has_3d_model"] is True
    assert s["materials"] == ["Oak"] and s["category"]["name"] == "Sofa"
    assert s["dimension"]["length_cm"] == "100.00"
    assert items["O"]["has_3d_model"] is False and items["O"]["primary_image_url"] is None
    assert "stock_quantity" not in s  # exact stock is not public
    assert s["price"] == "1000000.00"


def test_product_detail_has_everything(client, make_category, make_product):
    cat = make_category("Sofa")
    p = make_product(
        cat, name="Detail", description="desc", styles=["Modern"], materials=["Fabric"], colors=["Grey"],
        images=[("http://x/a.jpg", True, ImageType.GALLERY), ("http://x/v1.png", False, ImageType.VIEW_360)],
        models=[("http://x/m.glb", True), ("http://x/old.glb", False)],
    )
    r = client.get(f"{BASE}/products/{p.id}")
    assert r.status_code == 200
    d = r.json()
    assert d["description"] == "desc" and d["category"]["slug"] == "sofa"
    assert [i["image_type"] for i in d["images"]] == ["GALLERY", "VIEW_360"]
    assert len(d["models"]) == 2 and d["dimension"]["height_cm"] == "40.00"
    assert d["styles"] == ["Modern"] and d["colors"] == ["Grey"] and d["materials"] == ["Fabric"]


def test_detail_404_for_missing_and_inactive(client, make_category, make_product):
    cat = make_category("Sofa")
    p = make_product(cat, status=ProductStatus.INACTIVE)
    for pid in (p.id, 9999):
        r = client.get(f"{BASE}/products/{pid}")
        assert r.status_code == 404 and r.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
        assert client.get(f"{BASE}/products/{pid}/assets").status_code == 404


def test_assets_endpoint(client, make_category, make_product):
    cat = make_category("Sofa")
    p = make_product(cat, images=[("http://x/a.jpg", True, ImageType.GALLERY)], models=[("http://x/m.glb", True)])
    d = client.get(f"{BASE}/products/{p.id}/assets").json()
    assert d["product_id"] == p.id and d["images"][0]["url"] == "http://x/a.jpg"
    assert d["models"][0]["glb_url"] == "http://x/m.glb"


# ------------------------------- admin -------------------------------
def payload(cat_id, **over):
    base = {
        "sku": "SOFA-001", "name": "Sofa Bắc Âu", "price": "12990000", "stock_quantity": 5,
        "category_id": cat_id, "dimension": {"length_cm": 200, "width_cm": 90, "height_cm": 85},
        "materials": ["Oak", "oak", " Fabric "], "styles": ["Scandinavian"], "colors": ["Beige"],
    }
    base.update(over)
    return base


def test_admin_requires_manager(client, make_category, customer_headers):
    cat = make_category("Sofa")
    assert client.post(f"{BASE}/admin/products", json=payload(cat.id)).status_code == 401
    assert client.post(f"{BASE}/admin/products", json=payload(cat.id), headers=customer_headers).status_code == 403
    assert client.get(f"{BASE}/admin/products", headers=customer_headers).status_code == 403


def test_admin_create_product(client, make_category, manager_headers):
    cat = make_category("Sofa")
    r = client.post(f"{BASE}/admin/products", json=payload(cat.id), headers=manager_headers)
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["materials"] == ["Fabric", "Oak"]  # deduped case-insensitively, trimmed
    assert d["stock_quantity"] == 5 and d["status"] == "ACTIVE"
    assert d["dimension"]["length_cm"] == "200.00" and d["created_at"]
    assert client.get(f"{BASE}/products/{d['id']}").status_code == 200


def test_admin_create_validation(client, make_category, manager_headers):
    cat = make_category("Sofa")
    inactive = make_category("Old", active=False)
    post = lambda body: client.post(f"{BASE}/admin/products", json=body, headers=manager_headers)  # noqa: E731
    assert post(payload(cat.id, price="0")).status_code == 422
    assert post(payload(cat.id, price="-5")).status_code == 422
    assert post(payload(cat.id, price="10.999")).status_code == 422
    assert post(payload(cat.id, stock_quantity=-1)).status_code == 422
    assert post(payload(cat.id, sku="bad sku!")).status_code == 422
    assert post(payload(cat.id, dimension={"length_cm": 0, "width_cm": 1, "height_cm": 1})).status_code == 422
    body = payload(cat.id)
    body.pop("dimension")
    assert post(body).status_code == 422  # physical dimensions are mandatory
    assert post(payload(cat.id, bogus=1)).status_code == 422
    r = post(payload(9999))
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_CATEGORY"
    assert post(payload(inactive.id)).json()["error"]["code"] == "INVALID_CATEGORY"


def test_admin_create_duplicate_sku(client, make_category, manager_headers):
    cat = make_category("Sofa")
    assert client.post(f"{BASE}/admin/products", json=payload(cat.id), headers=manager_headers).status_code == 201
    r = client.post(f"{BASE}/admin/products", json=payload(cat.id, sku="sofa-001"), headers=manager_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "SKU_ALREADY_EXISTS"


def test_admin_update_product(client, make_category, make_product, manager_headers):
    cat = make_category("Sofa")
    cat2 = make_category("Bàn")
    p = make_product(cat, name="Old", materials=["Oak", "Steel"], styles=["Modern"], colors=["White"])
    r = client.patch(
        f"{BASE}/admin/products/{p.id}", headers=manager_headers,
        json={
            "name": "New  name", "price": "2500000", "stock_quantity": 0, "category_id": cat2.id,
            "dimension": {"height_cm": 99}, "materials": ["oak", "Glass"],
        },
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["name"] == "New name" and d["price"] == "2500000.00" and d["category"]["id"] == cat2.id
    assert d["dimension"]["height_cm"] == "99.00" and d["dimension"]["length_cm"] == "100.00"
    assert sorted(d["materials"]) == ["Glass", "Oak"]  # retained value keeps its stored casing
    assert d["styles"] == ["Modern"] and d["colors"] == ["White"]  # untouched
    assert d["stock_status"] == "OUT_OF_STOCK"


def test_admin_update_clears_attributes_with_empty_list(client, make_category, make_product, manager_headers):
    cat = make_category("Sofa")
    p = make_product(cat, colors=["White"])
    d = client.patch(f"{BASE}/admin/products/{p.id}", headers=manager_headers, json={"colors": []}).json()
    assert d["colors"] == []


def test_admin_update_rejects_bad_input(client, make_category, make_product, manager_headers):
    cat = make_category("Sofa")
    p = make_product(cat)
    patch = lambda body: client.patch(f"{BASE}/admin/products/{p.id}", headers=manager_headers, json=body)  # noqa: E731
    assert patch({"sku": "NEW"}).status_code == 422  # immutable
    assert patch({"price": None}).status_code == 422
    assert patch({"price": 0}).status_code == 422
    assert patch({"category_id": 9999}).json()["error"]["code"] == "INVALID_CATEGORY"
    assert client.patch(f"{BASE}/admin/products/9999", headers=manager_headers, json={"name": "x"}).status_code == 404


def test_admin_soft_delete_and_visibility(client, make_category, make_product, manager_headers):
    cat = make_category("Sofa")
    p = make_product(cat)
    assert client.delete(f"{BASE}/admin/products/{p.id}", headers=manager_headers).status_code == 204
    assert client.get(f"{BASE}/products/{p.id}").status_code == 404
    admin = client.get(f"{BASE}/admin/products/{p.id}", headers=manager_headers)
    assert admin.status_code == 200 and admin.json()["status"] == "INACTIVE"
    # re-activate through PATCH
    assert client.patch(f"{BASE}/admin/products/{p.id}", headers=manager_headers, json={"status": "ACTIVE"}).status_code == 200
    assert client.get(f"{BASE}/products/{p.id}").status_code == 200


def test_admin_list_includes_inactive_and_status_filter(client, make_category, make_product, manager_headers):
    cat = make_category("Sofa")
    make_product(cat, name="on")
    make_product(cat, name="off", status=ProductStatus.INACTIVE)
    h = manager_headers
    assert sorted(names(client.get(f"{BASE}/admin/products", headers=h))) == ["off", "on"]
    assert names(client.get(f"{BASE}/admin/products", headers=h, params={"status": "INACTIVE"})) == ["off"]
    first = client.get(f"{BASE}/admin/products", headers=h).json()["items"][0]
    assert "stock_quantity" in first and "status" in first
