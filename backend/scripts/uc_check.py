#!/usr/bin/env python
"""Chạy từng Use Case qua HTTP thật và in báo cáo PASS / FAIL / SKIP theo từng yêu cầu.

Chạy (trong thư mục backend, đã bật .venv, server đang chạy: py -m uvicorn app.main:app --reload):
    py scripts\\uc_check.py                      # mặc định http://localhost:8000/api/v1
    py scripts\\uc_check.py --base http://localhost:8000/api/v1 --keep
    py scripts\\uc_check.py --only C18,C19,C20   # chỉ chạy một số UC

Script tạo dữ liệu có tiền tố "uccheck"/"UCCHK-" (user, danh mục, sản phẩm, đơn hàng) và XÓA khi
chạy xong (trừ khi dùng --keep). Chỉ dùng thư viện chuẩn + import code của dự án để tạo dữ liệu nền.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from decimal import Decimal

sys.path.insert(0, os.getcwd())  # cho phép import `app` khi chạy từ thư mục backend

TAG = "uccheck" + uuid.uuid4().hex[:6]
PASSWORD = "Passw0rd123"
RESULTS: list[dict] = []
ONLY: set[str] = set()
BASE = ""
PREFIX = ""
OPENAPI: dict = {}


# ----------------------------------------------------------------- khung kiểm thử
class Skip(Exception):
    pass


def t(uc, req, fn):
    """Chạy một kiểm tra. fn() trả None => PASS; raise AssertionError(msg) => FAIL; raise Skip(msg) => SKIP."""
    if ONLY and uc.replace("UC-", "") not in ONLY:
        return
    try:
        note = fn()
        status, note = "PASS", note or ""
    except Skip as e:
        status, note = "SKIP", str(e)
    except AssertionError as e:
        status, note = "FAIL", str(e)
    except Exception as e:  # noqa: BLE001
        status, note = "FAIL", f"{type(e).__name__}: {e}"
    RESULTS.append({"uc": uc, "req": req, "status": status, "note": note})
    mark = {"PASS": "  ok ", "FAIL": " FAIL", "SKIP": " skip"}[status]
    print(f"[{mark}] {uc:<8} {req}" + (f"\n          -> {note}" if note and status != "PASS" else ""))


def expect(cond, msg):
    if not cond:
        raise AssertionError(msg)


def expect_status(r, *codes, what=""):
    s, data = r[0], r[1]
    if s not in codes:
        raise AssertionError(f"{what} mong đợi HTTP {'/'.join(map(str, codes))}, nhận {s}: {short(data)}")


def short(x, n=300):
    s = json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else x
    return s if len(s) <= n else s[:n] + "…"


def err_code(data):
    try:
        return data["error"]["code"]
    except Exception:  # noqa: BLE001
        return None


# ----------------------------------------------------------------- HTTP
def call(method, path, body=None, token=None, form=False, query=None, headers=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    h = {"Accept": "application/json"}
    data = None
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode() or "null"
            return resp.status, _json(raw), resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode() or "null"
        return e.code, _json(raw), e.headers


def _json(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def items_of(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("items", "data", "results"):
            if isinstance(data.get(k), list):
                return data[k]
    return []


# ----------------------------------------------------------------- dò endpoint qua openapi
def load_openapi():
    global OPENAPI, PREFIX
    root = BASE.split("/", 3)
    origin = "/".join(root[:3])
    PREFIX = "/" + root[3] if len(root) > 3 else ""
    with urllib.request.urlopen(origin + "/openapi.json", timeout=20) as r:
        OPENAPI = json.loads(r.read().decode())


def find(method, regex):
    """Trả về danh sách đường dẫn (đã bỏ prefix) có `method` khớp regex."""
    out = []
    for p, ops in OPENAPI.get("paths", {}).items():
        rel = p[len(PREFIX):] if PREFIX and p.startswith(PREFIX) else p
        if method.lower() in ops and re.search(regex, rel):
            out.append(rel)
    return sorted(out, key=len)


def need(method, regex, label):
    found = find(method, regex)
    if not found:
        raise Skip(f"không tìm thấy endpoint {label} ({method} ~ {regex}) trong openapi.json")
    return found[0]


def body_props(method, rel):
    ops = OPENAPI["paths"].get(PREFIX + rel, {}).get(method.lower(), {})
    content = ops.get("requestBody", {}).get("content", {})
    ctype = "application/json" if "application/json" in content else next(iter(content), None)
    schema = content.get(ctype, {}).get("schema", {}) if ctype else {}
    if "$ref" in schema:
        schema = OPENAPI["components"]["schemas"].get(schema["$ref"].split("/")[-1], {})
    return set(schema.get("properties", {})), ctype


def build(method, rel, values):
    """Chỉ gửi các field mà schema của endpoint thực sự có -> tránh lỗi extra_forbidden do đoán sai."""
    props, ctype = body_props(method, rel)
    return {k: v for k, v in values.items() if (not props or k in props)}, (ctype and "form" in ctype)


# ----------------------------------------------------------------- dữ liệu nền (DB trực tiếp)
class Env:
    db = None


def open_db():
    from app.database.session import get_db
    gen = get_db()
    Env.db = next(gen)
    Env.gen = gen


def mk_user(email, role="CUSTOMER"):
    from app.core.security import create_access_token, hash_password
    from app.models import User, UserRole
    u = User(email=email, password_hash=hash_password(PASSWORD), full_name="UC Check",
             phone="0901234567", role=UserRole(role))
    Env.db.add(u)
    Env.db.commit()
    token, _ = create_access_token(u.id)
    return u, token


def mk_category(name):
    from app.models import Category
    c = Category(name=name, slug=name.lower())
    Env.db.add(c)
    Env.db.commit()
    return c


def mk_product(cat, n, price, stock, status="ACTIVE", image=False):
    from app.models import ImageType, Product, ProductDimension, ProductImage, ProductStatus
    p = Product(sku=f"UCCHK-{TAG}-{n}", name=f"{TAG} Product {n}", price=Decimal(price), stock_quantity=stock,
                status=ProductStatus(status), category_id=cat.id,
                dimension=ProductDimension(length_cm=100, width_cm=50, height_cm=40))
    if image:
        p.images.append(ProductImage(url=f"http://img/{n}.jpg", is_primary=True,
                                     image_type=ImageType.GALLERY, display_order=0))
    Env.db.add(p)
    Env.db.commit()
    return p


def stock_of(pid):
    from sqlalchemy import select
    from app.models import Product
    Env.db.rollback()
    return Env.db.scalar(select(Product.stock_quantity).where(Product.id == pid))


def set_product(pid, **kw):
    from app.models import Product
    Env.db.rollback()
    p = Env.db.get(Product, pid)
    for k, v in kw.items():
        setattr(p, k, v)
    Env.db.commit()


def count_orders(user_id):
    from sqlalchemy import func, select
    from app.models import Order
    Env.db.rollback()
    return Env.db.scalar(select(func.count()).select_from(Order).where(Order.user_id == user_id))


def cleanup():
    from sqlalchemy import select
    from app.models import Cart, Category, Order, Payment, Product, User
    db = Env.db
    db.rollback()
    uids = list(db.scalars(select(User.id).where(User.email.like("uccheck%"))))
    for o in db.scalars(select(Order).where(Order.user_id.in_(uids))):
        db.delete(o)
    db.flush()
    for p in db.scalars(select(Payment).where(Payment.user_id.in_(uids))):
        db.delete(p)
    for c in db.scalars(select(Cart).where(Cart.user_id.in_(uids))):
        db.delete(c)
    db.flush()
    for p in db.scalars(select(Product).where(Product.sku.like("UCCHK-%"))):
        db.delete(p)
    db.flush()
    for c in db.scalars(select(Category).where(Category.name.like(f"{TAG}%"))):
        db.delete(c)
    for u in db.scalars(select(User).where(User.id.in_(uids))):
        db.delete(u)
    db.commit()


# ================================================================= PHASE 2
def phase2():
    print("\n===== PHASE 2: tài khoản, danh mục, sản phẩm (dò endpoint qua openapi.json) =====")
    email = f"{TAG}-c1@example.com"
    ctx = {}

    def register(em, pw=PASSWORD, **extra):
        rel = need("post", r"/register$", "đăng ký")
        values = {"email": em, "password": pw, "full_name": "UC Check", "phone": "0901234567", **extra}
        body, form = build("post", rel, values)
        return call("POST", rel, body, form=form)

    def login(em, pw=PASSWORD):
        rel = need("post", r"/login$", "đăng nhập")
        props, ctype = body_props("post", rel)
        if ctype and "form" in ctype:
            return call("POST", rel, {"username": em, "password": pw}, form=True)
        return call("POST", rel, {"email": em, "password": pw})

    def token_of(r):
        d = r[1] if isinstance(r[1], dict) else {}
        return d.get("access_token") or (d.get("data") or {}).get("access_token")

    # ---- UC-C01
    def c01_ok():
        r = register(email)
        expect_status(r, 200, 201, what="đăng ký hợp lệ")
        d = json.dumps(r[1]).lower()
        expect("password" not in d and "hash" not in d, f"response lộ thông tin mật khẩu: {short(r[1])}")
        ctx["registered"] = True
    t("UC-C01", "Đăng ký hợp lệ -> tạo tài khoản, không lộ mật khẩu/hash", c01_ok)

    def c01_dup():
        if not ctx.get("registered"):
            raise Skip("đăng ký ban đầu thất bại")
        r = register(email)
        expect(r[0] in (400, 409, 422), f"email trùng phải bị từ chối, nhận {r[0]}")
        r2 = register(email.upper())
        expect(r2[0] in (400, 409, 422), f"email trùng khác hoa/thường phải bị từ chối, nhận {r2[0]}")
    t("UC-C01", "Email trùng (kể cả khác hoa/thường) bị từ chối", c01_dup)

    def c01_bad_email():
        r = register("khong-phai-email")
        expect(r[0] in (400, 422), f"email sai định dạng phải bị từ chối, nhận {r[0]}")
    t("UC-C01", "Email sai định dạng bị từ chối", c01_bad_email)

    def c01_weak():
        r = register(f"{TAG}-weak@example.com", pw="123")
        expect(r[0] in (400, 422), f"mật khẩu yếu phải bị từ chối, nhận {r[0]}")
    t("UC-C01", "Mật khẩu không đạt yêu cầu bảo mật bị từ chối", c01_weak)

    def c01_role():
        r = register(f"{TAG}-role@example.com", role="STORE_MANAGER")
        if r[0] in (400, 422):
            return "server từ chối field role (ổn)"
        expect_status(r, 200, 201)
        role = (r[1] or {}).get("role") if isinstance(r[1], dict) else None
        expect(role in (None, "CUSTOMER"), f"tự đăng ký được vai trò {role} — lỗ hổng phân quyền")
    t("UC-C01", "Không thể tự đăng ký vai trò quản lý (FR-04)", c01_role)

    # ---- UC-C02
    def c02_login():
        r = login(email)
        expect_status(r, 200, what="đăng nhập đúng")
        tok = token_of(r)
        expect(tok, f"không có access_token: {short(r[1])}")
        ctx["token"] = tok
    t("UC-C02", "Đăng nhập đúng -> nhận access token", c02_login)

    def c02_wrong():
        r = login(email, "SaiMatKhau1")
        expect(r[0] == 401, f"sai mật khẩu phải 401, nhận {r[0]}")
        r2 = login(f"{TAG}-none@example.com")
        expect(r2[0] == 401, f"email không tồn tại phải 401, nhận {r2[0]}")
        expect(short(r[1]) == short(r2[1]) or err_code(r[1]) == err_code(r2[1]),
               "thông báo lỗi khác nhau giữa 'sai mật khẩu' và 'email không tồn tại' (lộ tài khoản có tồn tại)")
    t("UC-C02", "Sai thông tin -> 401, thông báo không lộ email có tồn tại", c02_wrong)

    me_get = lambda: need("get", r"/me$", "xem hồ sơ")

    def c02_protected():
        rel = me_get()
        expect(call("GET", rel)[0] == 401, "không token phải 401")
        expect(call("GET", rel, token="abc.def.ghi")[0] == 401, "token rác phải 401")
    t("UC-C02", "Không token / token sai -> 401", c02_protected)

    # ---- UC-C03
    def c03_view():
        if not ctx.get("token"):
            raise Skip("chưa có token")
        r = call("GET", me_get(), token=ctx["token"])
        expect_status(r, 200)
        expect(r[1].get("email") == email.lower(), f"email hồ sơ sai: {short(r[1])}")
        expect("password_hash" not in r[1], "hồ sơ lộ password_hash")
    t("UC-C03", "Xem hồ sơ cá nhân", c03_view)

    def upd(values):
        rel = me_get()
        method = "patch" if find("patch", re.escape(rel) + "$") else "put"
        if not find(method, re.escape(rel) + "$"):
            raise Skip("không có endpoint PATCH/PUT cập nhật hồ sơ")
        body, _ = build(method, rel, values)
        return call(method.upper(), rel, body, token=ctx["token"])

    def c03_update():
        if not ctx.get("token"):
            raise Skip("chưa có token")
        r = upd({"full_name": "Ten Moi", "phone": "0912345678", "shipping_address": "99 Nguyen Hue, Q1"})
        expect_status(r, 200, what="cập nhật hồ sơ")
        g = call("GET", me_get(), token=ctx["token"])[1]
        expect(g.get("full_name") == "Ten Moi" and g.get("shipping_address") == "99 Nguyen Hue, Q1",
               f"dữ liệu không được lưu: {short(g)}")
    t("UC-C03", "Cập nhật họ tên / SĐT / địa chỉ giao hàng và lưu thành công", c03_update)

    def c03_invalid():
        if not ctx.get("token"):
            raise Skip("chưa có token")
        r = upd({"phone": "abc"})
        expect(r[0] in (400, 422), f"SĐT sai phải bị từ chối, nhận {r[0]}")
        g = call("GET", me_get(), token=ctx["token"])[1]
        expect(g.get("phone") != "abc", "dữ liệu không hợp lệ vẫn bị lưu")
    t("UC-C03", "Dữ liệu không hợp lệ bị từ chối, giữ nguyên thông tin cũ", c03_invalid)

    def c03_protected_fields():
        if not ctx.get("token"):
            raise Skip("chưa có token")
        upd({"role": "STORE_MANAGER", "is_active": False, "id": 999999})
        g = call("GET", me_get(), token=ctx["token"])
        expect_status(g, 200, what="vẫn đăng nhập được sau khi gửi field cấm")
        expect(g[1].get("role", "CUSTOMER") == "CUSTOMER", f"đổi được role: {short(g[1])}")
        expect(g[1].get("id") != 999999, "đổi được id")
    t("UC-C03", "Không đổi được role / id / trạng thái tài khoản", c03_protected_fields)

    def c03_email_verify():
        if not ctx.get("token"):
            raise Skip("chưa có token")
        new = f"{TAG}-newmail@example.com"
        r = upd({"email": new})
        if r[0] in (400, 422):
            raise Skip("endpoint không nhận field email (BR2 'đổi email có xác minh' chưa hiện thực)")
        g = call("GET", me_get(), token=ctx["token"])[1]
        expect(g.get("email") != new, "email đổi NGAY không qua xác minh — vi phạm BR2 của UC-C03")
    t("UC-C03", "Đổi email phải được xác minh trước khi có hiệu lực (BR2)", c03_email_verify)

    # ---- dữ liệu cho C04-C07 / SM
    open_db()
    mgr, mgr_token = mk_user(f"{TAG}-mgr@example.com", "STORE_MANAGER")
    cat_a, cat_b = mk_category(f"{TAG}-CatA"), mk_category(f"{TAG}-CatB")
    pa1 = mk_product(cat_a, "a1", "1000000", 5, image=True)
    pa2 = mk_product(cat_a, "a2", "5000000", 0)
    pb1 = mk_product(cat_b, "b1", "3000000", 7)
    p_off = mk_product(cat_b, "off", "900000", 5, status="INACTIVE")
    ctx.update(mgr_token=mgr_token, cat_a=cat_a, cat_b=cat_b, pa1=pa1, pa2=pa2, pb1=pb1, p_off=p_off)
    plist = lambda: need("get", r"^/products$", "danh sách sản phẩm")

    # ---- UC-C04
    def c04_cats():
        rel = need("get", r"^/categories$", "danh mục")
        r = call("GET", rel)
        expect_status(r, 200)
        names = json.dumps(r[1])
        expect(f"{TAG}-CatA" in names, "danh mục vừa tạo không xuất hiện trong danh sách")
    t("UC-C04", "Xem danh sách danh mục", c04_cats)

    def c04_by_cat():
        r = call("GET", plist(), query={"category_id": cat_a.id, "page_size": 100})
        expect_status(r, 200)
        ids = {i["id"] for i in items_of(r[1])}
        expect(pa1.id in ids and pa2.id in ids, f"thiếu sản phẩm của danh mục A: {ids}")
        expect(pb1.id not in ids, "lọt sản phẩm của danh mục khác")
    t("UC-C04", "Xem sản phẩm theo danh mục (hiển thị đúng danh mục)", c04_by_cat)

    def c04_fields():
        r = call("GET", plist(), query={"category_id": cat_a.id})
        it = next(i for i in items_of(r[1]) if i["id"] == pa1.id)
        missing = [k for k in ("name", "price", "primary_image_url") if k not in it]
        expect(not missing, f"thiếu trường hiển thị {missing}")
        expect(it["primary_image_url"], "không có ảnh chính dù sản phẩm có ảnh")
    t("UC-C04", "Mỗi sản phẩm hiển thị hình ảnh, tên, giá", c04_fields)

    def c04_time():
        t0 = time.time()
        call("GET", plist(), query={"category_id": cat_a.id})
        dt = time.time() - t0
        expect(dt <= 2, f"mất {dt:.2f}s > 2s")
        return f"{dt*1000:.0f} ms"
    t("UC-C04", "Phản hồi <= 2 giây (NFR-01)", c04_time)

    # ---- UC-C05
    def c05_found():
        r = call("GET", plist(), query={"q": f"{TAG} Product a1"})
        expect_status(r, 200)
        ids = {i["id"] for i in items_of(r[1])}
        expect(pa1.id in ids, "tìm theo tên không ra sản phẩm")
        expect(pb1.id not in ids, "kết quả lẫn sản phẩm không khớp từ khóa")
    t("UC-C05", "Tìm theo từ khóa (tên) trả đúng sản phẩm", c05_found)

    def c05_sku():
        r = call("GET", plist(), query={"q": pa1.sku})
        expect(pa1.id in {i["id"] for i in items_of(r[1])}, "tìm theo SKU không ra")
    t("UC-C05", "Tìm theo SKU", c05_sku)

    def c05_none():
        r = call("GET", plist(), query={"q": "zzzkhongtontai" + TAG})
        expect_status(r, 200)
        expect(items_of(r[1]) == [], f"không có sản phẩm khớp nhưng vẫn trả: {short(r[1])}")
    t("UC-C05", "Không khớp -> danh sách rỗng (200)", c05_none)

    def c05_like():
        r = call("GET", plist(), query={"q": "%"})
        expect(r[0] in (200, 422), f"ký tự LIKE '%' gây lỗi {r[0]}")
        if r[0] == 200:
            expect(all("%" in json.dumps(i) for i in items_of(r[1])),
                   "q='%' khớp mọi sản phẩm (chưa escape ký tự LIKE)")
    t("UC-C05", "Ký tự đặc biệt (%) không gây lỗi / không khớp tất cả", c05_like)

    # ---- UC-C06
    def c06_price():
        r = call("GET", plist(), query={"category_id": cat_a.id, "min_price": 2000000, "max_price": 9000000})
        ids = {i["id"] for i in items_of(r[1])}
        expect(pa2.id in ids and pa1.id not in ids, f"lọc giá sai: {ids}")
    t("UC-C06", "Lọc theo khoảng giá", c06_price)

    def c06_sort():
        up = [Decimal(str(i["price"])) for i in items_of(call("GET", plist(), query={"q": TAG, "sort": "price_asc"})[1])]
        dn = [Decimal(str(i["price"])) for i in items_of(call("GET", plist(), query={"q": TAG, "sort": "price_desc"})[1])]
        expect(len(up) >= 2, "không đủ dữ liệu để kiểm tra sắp xếp")
        expect(up == sorted(up), f"price_asc sai: {up}")
        expect(dn == sorted(dn, reverse=True), f"price_desc sai: {dn}")
    t("UC-C06", "Sắp xếp giá tăng / giảm", c06_sort)

    def c06_stock():
        r = call("GET", plist(), query={"category_id": cat_a.id, "in_stock_only": "true"})
        ids = {i["id"] for i in items_of(r[1])}
        expect(pa1.id in ids and pa2.id not in ids, f"in_stock_only sai: {ids}")
    t("UC-C06", "Chỉ hiển thị còn hàng", c06_stock)

    def c06_range():
        r = call("GET", plist(), query={"min_price": 9000000, "max_price": 1000})
        expect(r[0] == 422, f"min_price > max_price phải 422, nhận {r[0]}")
    t("UC-C06", "Khoảng giá không hợp lệ bị từ chối", c06_range)

    def c06_page():
        r = call("GET", plist(), query={"q": TAG, "page_size": 1, "page": 1})
        expect_status(r, 200)
        expect(len(items_of(r[1])) == 1, f"page_size=1 trả {len(items_of(r[1]))} dòng")
        expect(call("GET", plist(), query={"page_size": 100000})[0] == 422, "page_size quá lớn phải bị từ chối")
    t("UC-C06", "Phân trang và giới hạn page_size", c06_page)

    # ---- UC-C07
    def pdetail(pid):
        return re.sub(r"\{[^}]+\}", str(pid), need("get", r"^/products/\{[^}]+\}$", "chi tiết sản phẩm"))

    def c07_detail():
        r = call("GET", pdetail(pa1.id))
        expect_status(r, 200)
        miss = [k for k in ("name", "description", "price", "images", "dimension", "stock_status") if k not in r[1]]
        expect(not miss, f"thiếu trường chi tiết {miss}")
        expect(r[1]["dimension"] is not None, "thiếu kích thước vật lý")
    t("UC-C07", "Chi tiết: tên, mô tả, giá, hình ảnh, kích thước, tồn kho", c07_detail)

    def c07_404():
        expect(call("GET", pdetail(99999999))[0] == 404, "sản phẩm không tồn tại phải 404")
    t("UC-C07", "Sản phẩm không tồn tại -> 404", c07_404)

    def c07_inactive():
        expect(call("GET", pdetail(p_off.id))[0] == 404, "sản phẩm ngừng kinh doanh vẫn xem được")
    t("UC-C07", "Sản phẩm ngừng kinh doanh không hiển thị cho khách", c07_inactive)

    # ---- UC-SM01
    new_sku = f"UCCHK-{TAG}-new"

    def prod_body(**kw):
        base = dict(sku=new_sku, name=f"{TAG} New", price="1500000.00", stock_quantity=4,
                    category_id=cat_a.id, dimension={"length_cm": 100, "width_cm": 50, "height_cm": 40},
                    description="d", currency="VND", materials=["oak"], styles=[], colors=[])
        base.update(kw)
        return base

    def create_rel():
        return need("post", r"/products$", "tạo sản phẩm")

    def sm01_create():
        r = call("POST", create_rel(), prod_body(), token=ctx["mgr_token"])
        expect_status(r, 200, 201, what="manager tạo sản phẩm")
        ctx["new_id"] = r[1]["id"]
    t("UC-SM01", "Store Manager thêm sản phẩm mới", sm01_create)

    def sm01_forbidden():
        if not ctx.get("token"):
            raise Skip("chưa có token customer")
        expect(call("POST", create_rel(), prod_body(sku=new_sku + "x"), token=ctx["token"])[0] == 403,
               "customer phải bị 403 khi tạo sản phẩm")
        expect(call("POST", create_rel(), prod_body(sku=new_sku + "y"))[0] == 401, "không token phải 401")
    t("UC-SM01", "Customer 403 / chưa đăng nhập 401 (NFR-14)", sm01_forbidden)

    def sm01_invalid():
        r = call("POST", create_rel(), prod_body(sku=new_sku + "z", price="0"), token=ctx["mgr_token"])
        expect(r[0] == 422, f"giá 0 phải 422, nhận {r[0]}")
        r = call("POST", create_rel(), prod_body(sku=new_sku + "w", dimension=None), token=ctx["mgr_token"])
        expect(r[0] == 422, f"thiếu kích thước phải 422, nhận {r[0]}")
    t("UC-SM01", "Dữ liệu thiếu/sai (giá 0, thiếu kích thước) bị từ chối", sm01_invalid)

    def sm01_dup():
        r = call("POST", create_rel(), prod_body(), token=ctx["mgr_token"])
        expect(r[0] in (409, 422), f"SKU trùng phải bị từ chối, nhận {r[0]}")
    t("UC-SM01", "SKU trùng bị từ chối", sm01_dup)

    def sm01_update():
        if not ctx.get("new_id"):
            raise Skip("chưa tạo được sản phẩm")
        rels = find("patch", r"/products/\{[^}]+\}$") or find("put", r"/products/\{[^}]+\}$")
        if not rels:
            raise Skip("không có endpoint cập nhật sản phẩm")
        method = "PATCH" if find("patch", r"/products/\{[^}]+\}$") else "PUT"
        path = re.sub(r"\{[^}]+\}", str(ctx["new_id"]), rels[0])
        r = call(method, path, {"price": "1750000.00", "stock_quantity": 9}, token=ctx["mgr_token"])
        expect_status(r, 200, what="cập nhật sản phẩm")
        d = call("GET", pdetail(ctx["new_id"]))[1]
        expect(Decimal(str(d["price"])) == Decimal("1750000"), f"giá không cập nhật: {d.get('price')}")
    t("UC-SM01", "Cập nhật giá / tồn kho", sm01_update)

    # ---- UC-SM02
    def sm02():
        found = find("post", r"(images|assets|models)")
        if not found:
            raise Skip("chưa có endpoint tải ảnh / mô hình 3D (UC-SM02 chưa hiện thực)")
        return "có endpoint: " + ", ".join(found[:4]) + " (chưa kiểm tra upload thực tế)"
    t("UC-SM02", "Có endpoint quản lý hình ảnh / mô hình 3D", sm02)

    # ---- UC-SM03
    def sm03_create():
        rel = need("post", r"/categories$", "tạo danh mục")
        body, _ = build("post", rel, {"name": f"{TAG}-CatNew", "slug": f"{TAG}-catnew".lower(), "description": "x"})
        r = call("POST", rel, body, token=ctx["mgr_token"])
        expect_status(r, 200, 201, what="tạo danh mục")
        ctx["cat_new"] = r[1]["id"]
        r2 = call("POST", rel, body, token=ctx["mgr_token"])
        expect(r2[0] in (409, 422), f"tên danh mục trùng phải bị từ chối, nhận {r2[0]}")
        e = build("post", rel, {"name": "", "description": "x"})[0]
        expect(call("POST", rel, e, token=ctx["mgr_token"])[0] in (400, 422), "tên rỗng phải bị từ chối (400/422)")
    t("UC-SM03", "Tạo danh mục; trùng tên / tên rỗng bị từ chối", sm03_create)

    def sm03_delete_rule():
        rels = find("delete", r"/categories/\{[^}]+\}$")
        if not rels:
            raise Skip("không có endpoint xóa danh mục")
        path = re.sub(r"\{[^}]+\}", str(cat_a.id), rels[0])
        r = call("DELETE", path, token=ctx["mgr_token"])
        expect(r[0] in (409, 422), f"xóa danh mục đang có sản phẩm phải bị từ chối, nhận {r[0]}")
        if ctx.get("cat_new"):
            r = call("DELETE", re.sub(r"\{[^}]+\}", str(ctx["cat_new"]), rels[0]), token=ctx["mgr_token"])
            expect(r[0] in (200, 204), f"xóa danh mục rỗng phải thành công, nhận {r[0]}")
    t("UC-SM03", "Không xóa danh mục đang có sản phẩm; xóa danh mục rỗng được", sm03_delete_rule)

    def sm03_forbidden():
        if not ctx.get("token"):
            raise Skip("chưa có token customer")
        rel = need("post", r"/categories$", "tạo danh mục")
        r = call("POST", rel, {"name": f"{TAG}-x"}, token=ctx["token"])
        expect(r[0] == 403, f"customer tạo danh mục phải 403, nhận {r[0]}")
    t("UC-SM03", "Customer không tạo được danh mục (403)", sm03_forbidden)


# ================================================================= PHASE 4
def phase4():
    print("\n===== PHASE 4: giỏ hàng, thanh toán, đơn hàng =====")
    if Env.db is None:
        open_db()
    from app.models import Order  # noqa: F401
    cat = mk_category(f"{TAG}-P4")
    p1 = mk_product(cat, "p1", "10000000", 5, image=True)
    p2 = mk_product(cat, "p2", "2000000", 3)
    p_out = mk_product(cat, "out", "500000", 0)
    p_off = mk_product(cat, "inactive", "700000", 9, status="INACTIVE")
    ua, ta = mk_user(f"{TAG}-a@example.com")
    ub, tb = mk_user(f"{TAG}-b@example.com")
    um, tm = mk_user(f"{TAG}-m4@example.com", "STORE_MANAGER")
    ue, te = mk_user(f"{TAG}-empty@example.com")
    SHIP = {"recipient_name": "Nguyen Van A", "phone": "0901234567", "address": "12 Le Loi, Q1, TP.HCM"}

    add = lambda tok, pid, q=1: call("POST", "/cart/items", {"product_id": pid, "quantity": q}, token=tok)
    cart = lambda tok: call("GET", "/cart", token=tok)
    start = lambda tok, ship=SHIP, m="SANDBOX_CARD": call("POST", "/checkout", {"shipping": ship, "payment_method": m}, token=tok)
    confirm = lambda tok, pid, o="SUCCESS": call("POST", f"/payments/{pid}/sandbox-confirm", {"outcome": o}, token=tok)
    clear = lambda tok: call("DELETE", "/cart", token=tok)

    # ---------------- UC-C18
    t("UC-C18", "Chưa đăng nhập -> 401; Store Manager -> 403",
      lambda: (expect(call("GET", "/cart")[0] == 401, "không token phải 401"),
               expect(cart(tm)[0] == 403, "manager phải 403")) and None)

    def c18_empty():
        r = cart(te)
        expect_status(r, 200)
        expect(r[1]["items"] == [] and Decimal(r[1]["subtotal"]) == 0, f"giỏ rỗng sai: {short(r[1])}")
    t("UC-C18", "Giỏ rỗng: items=[] và tổng tiền 0", c18_empty)

    def c18_add():
        r = add(ta, p1.id, 2)
        expect_status(r, 200, 201, what="thêm vào giỏ")
        r = add(ta, p2.id, 1)
        d = r[1]
        expect(Decimal(d["subtotal"]) == Decimal("22000000"), f"tổng tạm tính sai: {d['subtotal']}")
        expect(d["total_quantity"] == 3, f"tổng số lượng sai: {d['total_quantity']}")
        expect(d["items"][0]["image_url"] == "http://img/p1.jpg", "thiếu ảnh sản phẩm trong giỏ")
    t("UC-C18", "Thêm sản phẩm; tổng tiền tạm tính và ảnh đúng (FR-19)", c18_add)

    def c18_merge():
        d = add(ta, p1.id, 1)[1]
        lines = [i for i in d["items"] if i["product_id"] == p1.id]
        expect(len(lines) == 1 and lines[0]["quantity"] == 3, f"không cộng dồn: {short(lines)}")
    t("UC-C18", "Thêm sản phẩm đã có -> cộng dồn, không tạo dòng trùng", c18_merge)

    def c18_stock():
        r = add(ta, p2.id, 3)  # đã có 1, +3 = 4 > 3
        expect(r[0] == 409 and err_code(r[1]) == "INSUFFICIENT_STOCK", f"vượt tồn kho (cộng dồn) sai: {r[0]} {short(r[1])}")
        expect(r[1]["error"]["details"] == {"available_stock": 3}, "thiếu details.available_stock")
        r = add(ta, p_out.id)
        expect(r[0] == 409 and err_code(r[1]) == "OUT_OF_STOCK", f"hết hàng sai: {r[0]} {short(r[1])}")
        r = add(ta, p_off.id)
        expect(r[0] == 409 and err_code(r[1]) == "PRODUCT_UNAVAILABLE", f"ngừng bán sai: {r[0]} {short(r[1])}")
        expect(add(ta, 99999999)[0] == 404, "sản phẩm không tồn tại phải 404")
    t("UC-C18", "Vượt tồn kho / hết hàng / ngừng bán / không tồn tại bị từ chối (Exception Flow, BR)", c18_stock)

    def c18_invalid_qty():
        expect(add(ta, p1.id, 0)[0] == 422, "quantity=0 phải 422")
        expect(add(ta, p1.id, -1)[0] == 422, "quantity=-1 phải 422")
        r = add(ta, p1.id, 1000)
        expect(r[0] in (409, 422), f"quantity quá lớn phải bị từ chối, nhận {r[0]}")
    t("UC-C18", "Số lượng không hợp lệ (0, âm, quá lớn) bị từ chối", c18_invalid_qty)

    def c18_update():
        lines = cart(ta)[1]["items"]
        it = next(i for i in lines if i["product_id"] == p2.id)
        r = call("PATCH", f"/cart/items/{it['id']}", {"quantity": 3}, token=ta)
        expect_status(r, 200)
        expect(Decimal(r[1]["subtotal"]) == Decimal("36000000"), f"tổng sau cập nhật sai: {r[1]['subtotal']}")
        r = call("PATCH", f"/cart/items/{it['id']}", {"quantity": 4}, token=ta)
        expect(r[0] == 409, f"cập nhật vượt tồn kho phải 409, nhận {r[0]}")
        r = call("PATCH", f"/cart/items/{it['id']}", {"quantity": 0}, token=ta)
        expect(r[0] == 422, f"cập nhật quantity=0 phải 422, nhận {r[0]}")
    t("UC-C18", "Cập nhật số lượng; tính lại tổng; chặn vượt tồn kho (FR-20)", c18_update)

    def c18_ownership():
        it = cart(ta)[1]["items"][0]
        expect(call("PATCH", f"/cart/items/{it['id']}", {"quantity": 1}, token=tb)[0] == 404, "sửa dòng giỏ của người khác phải 404")
        expect(call("DELETE", f"/cart/items/{it['id']}", token=tb)[0] == 404, "xóa dòng giỏ của người khác phải 404")
        expect(len(cart(ta)[1]["items"]) >= 1, "dòng giỏ bị thay đổi bởi người khác")
    t("UC-C18", "Không thao tác được giỏ của người khác (404)", c18_ownership)

    def c18_live():
        set_product(p2.id, stock_quantity=1, price=Decimal("2500000"))
        d = cart(ta)[1]
        it = next(i for i in d["items"] if i["product_id"] == p2.id)
        expect(d["has_issues"] and it["issue"] == "INSUFFICIENT_STOCK", f"không cảnh báo tồn kho giảm: {short(it)}")
        expect(Decimal(it["unit_price"]) == Decimal("2500000"), "giá trong giỏ không theo giá hiện hành")
        set_product(p2.id, stock_quantity=3, price=Decimal("2000000"))
    t("UC-C18", "Giỏ nhất quán với dữ liệu hiện hành: cờ issue + giá mới", c18_live)

    def c18_remove():
        it = next(i for i in cart(ta)[1]["items"] if i["product_id"] == p2.id)
        r = call("DELETE", f"/cart/items/{it['id']}", token=ta)
        expect_status(r, 200)
        expect(all(i["product_id"] != p2.id for i in r[1]["items"]), "dòng chưa bị xóa")
        d = clear(ta)[1]
        expect(d["items"] == [], "clear giỏ không xóa hết")
    t("UC-C18", "Xóa sản phẩm / xóa toàn bộ giỏ", c18_remove)

    # ---------------- UC-C19
    t("UC-C19", "Giỏ rỗng -> validate 422 CART_EMPTY",
      lambda: (lambda r: expect(r[0] == 422 and err_code(r[1]) == "CART_EMPTY", f"nhận {r[0]} {short(r[1])}"))(
          call("POST", "/checkout/validate", token=te)))

    def c19_ship():
        add(ta, p1.id, 2)
        for bad in ({**SHIP, "phone": "123"}, {**SHIP, "address": "  "}, {**SHIP, "recipient_name": ""}):
            r = start(ta, bad)
            expect(r[0] == 422, f"thông tin giao hàng sai phải 422, nhận {r[0]} với {bad}")
        expect(call("POST", "/checkout", {"shipping": SHIP, "payment_method": "BITCOIN"}, token=ta)[0] == 422,
               "phương thức không hỗ trợ phải 422")
    t("UC-C19", "Thông tin nhận hàng / phương thức không hợp lệ bị từ chối (FR-22)", c19_ship)

    state = {}

    def c19_start():
        r = start(ta)
        expect_status(r, 201, 200, what="khởi tạo thanh toán")
        d = r[1]
        expect(d["status"] == "PENDING" and Decimal(d["amount"]) == Decimal("20000000"), f"phiên sai: {short(d)}")
        expect(stock_of(p1.id) == 5, "tồn kho bị trừ trước khi thanh toán thành công")
        expect(count_orders(ua.id) == 0, "đơn đã được tạo trước khi thanh toán")
        state["pay1"] = d["payment_id"]
    t("UC-C19", "Khởi tạo giao dịch: PENDING, đúng số tiền, chưa trừ kho, chưa có đơn (FR-23)", c19_start)

    def c19_fail():
        r = confirm(ta, state["pay1"], "FAILED")
        expect(r[1]["status"] == "FAILED" and r[1]["order_id"] is None, f"{short(r[1])}")
        expect(stock_of(p1.id) == 5, "thanh toán thất bại nhưng tồn kho bị trừ")
        expect(count_orders(ua.id) == 0, "thanh toán thất bại nhưng có đơn")
        expect(len(cart(ta)[1]["items"]) == 1, "giỏ hàng không được giữ nguyên")
    t("UC-C19", "Thanh toán thất bại: không đơn, không trừ kho, giữ giỏ (Exception Flow)", c19_fail)

    def c19_expired():
        d = start(ta)[1]
        r = confirm(ta, d["payment_id"], "EXPIRED")
        expect(r[1]["status"] == "EXPIRED" and stock_of(p1.id) == 5, f"{short(r[1])}")
    t("UC-C19", "Giao dịch hết hạn: không đơn, không trừ kho", c19_expired)

    def c19_success():
        d = start(ta)[1]
        r = confirm(ta, d["payment_id"])
        expect_status(r, 200)
        expect(r[1]["status"] == "SUCCESS" and r[1]["order_code"], f"{short(r[1])}")
        expect(stock_of(p1.id) == 3, f"tồn kho phải còn 3, thực tế {stock_of(p1.id)}")
        expect(cart(ta)[1]["items"] == [], "giỏ chưa được dọn sau khi đặt")
        state["order"], state["code"] = r[1]["order_id"], r[1]["order_code"]
        state["pay_ok"] = d["payment_id"]
    t("UC-C19", "Thanh toán thành công: tạo đơn + mã đơn, trừ kho đúng, dọn giỏ (FR-24)", c19_success)

    def c19_idem():
        r = confirm(ta, state["pay_ok"])
        expect(r[1]["order_id"] == state["order"], "xác nhận lặp tạo đơn khác")
        expect(stock_of(p1.id) == 3, f"xác nhận lặp trừ kho lần 2: còn {stock_of(p1.id)}")
        expect(count_orders(ua.id) == 1, f"số đơn phải là 1, thực tế {count_orders(ua.id)}")
    t("UC-C19", "Xác nhận lặp không tạo đơn / không trừ kho lần 2 (NFR-12)", c19_idem)

    def c19_invalid_cart():
        add(ta, p2.id, 3)
        set_product(p2.id, stock_quantity=1)
        r = start(ta)
        expect(r[0] == 409 and err_code(r[1]) == "CART_INVALID", f"giỏ có lỗi phải bị chặn: {r[0]} {short(r[1])}")
        expect(call("POST", "/checkout/validate", token=ta)[1]["valid"] is False, "validate phải valid=false")
        set_product(p2.id, stock_quantity=3)
        clear(ta)
    t("UC-C19", "Giỏ có sản phẩm thiếu tồn kho bị chặn đặt hàng (FR-21)", c19_invalid_cart)

    def c19_sold_out():
        set_product(p2.id, stock_quantity=3)
        add(ta, p2.id, 3)
        pa = start(ta)[1]["payment_id"]
        add(tb, p2.id, 3)
        pb = start(tb)[1]["payment_id"]
        expect(confirm(tb, pb)[1]["status"] == "SUCCESS", "người B phải mua được")
        r = confirm(ta, pa)
        expect(r[1]["status"] == "REFUNDED" and r[1]["order_id"] is None, f"{short(r[1])}")
        expect(stock_of(p2.id) == 0, f"tồn kho phải 0, thực tế {stock_of(p2.id)} (âm/trừ lặp?)")
        clear(ta); clear(tb)
    t("UC-C19", "Hết hàng giữa lúc thanh toán: hoàn tiền, không tạo đơn, kho không âm", c19_sold_out)

    def c19_partial():
        set_product(p1.id, stock_quantity=5); set_product(p2.id, stock_quantity=5)
        add(tb, p1.id, 2); add(tb, p2.id, 3)
        pid = start(tb)[1]["payment_id"]
        set_product(p2.id, stock_quantity=1)
        r = confirm(tb, pid)
        expect(r[1]["status"] == "REFUNDED", f"{short(r[1])}")
        expect(stock_of(p1.id) == 5, f"p1 bị trừ dở dang: {stock_of(p1.id)} (phải hoàn tác)")
        clear(tb)
    t("UC-C19", "Thiếu hàng ở 1 sản phẩm: hoàn tác trừ kho của toàn đơn (transaction)", c19_partial)

    def c19_webhook():
        set_product(p1.id, stock_quantity=5)
        add(tb, p1.id, 1)
        d = start(tb)[1]
        body = {"gateway_ref": d["gateway_ref"], "result": "SUCCESS", "amount": d["amount"]}
        r = call("POST", "/payments/webhook", body, headers={"X-Signature": "bad"})
        expect(r[0] == 401, f"chữ ký sai phải 401, nhận {r[0]}")
        expect(stock_of(p1.id) == 5, "chữ ký sai nhưng kho bị trừ")
        try:
            from app.services.payment_gateway import sign_result
        except Exception as e:  # noqa: BLE001
            raise Skip(f"không import được sign_result: {e}")
        sig = sign_result(d["gateway_ref"], "SUCCESS", Decimal(d["amount"]))
        r = call("POST", "/payments/webhook", body, headers={"X-Signature": sig})
        expect(r[0] == 200 and r[1]["status"] == "SUCCESS", f"webhook hợp lệ phải SUCCESS: {r[0]} {short(r[1])}")
        expect(stock_of(p1.id) == 4, f"kho phải còn 4, thực tế {stock_of(p1.id)}")
    t("UC-C19", "Webhook cổng thanh toán: chữ ký sai 401, chữ ký đúng tạo đơn", c19_webhook)

    def c19_webhook_amount():
        add(tb, p1.id, 1)
        d = start(tb)[1]
        from app.services.payment_gateway import sign_result
        sig = sign_result(d["gateway_ref"], "SUCCESS", Decimal("1.00"))
        r = call("POST", "/payments/webhook", {"gateway_ref": d["gateway_ref"], "result": "SUCCESS", "amount": "1.00"},
                 headers={"X-Signature": sig})
        expect(r[1]["status"] == "FAILED", f"sai số tiền phải FAILED, nhận {short(r[1])}")
    t("UC-C19", "Số tiền thanh toán không khớp -> FAILED, không tạo đơn", c19_webhook_amount)

    def c19_other():
        d = start(tb)[1]
        expect(confirm(ta, d["payment_id"])[0] == 404, "xác nhận giao dịch của người khác phải 404")
        expect(call("GET", f"/payments/{d['payment_id']}", token=ta)[0] == 404, "xem giao dịch người khác phải 404")
    t("UC-C19", "Không truy cập được giao dịch của người khác (404)", c19_other)

    # ---------------- UC-C20
    # Khi chạy riêng (--only C20) UC-C19 bị bỏ qua nên chưa có đơn: tự đặt 1 đơn (2 x p1) để có dữ liệu kiểm tra
    if "order" not in state and (not ONLY or "C20" in ONLY):
        try:
            add(ta, p1.id, 2)
            r0 = confirm(ta, start(ta)[1]["payment_id"])
            state["order"], state["code"] = r0[1]["order_id"], r0[1]["order_code"]
        except Exception as e:  # noqa: BLE001
            print(f"  (không tạo được đơn mồi cho C20: {e})")

    t("UC-C20", "Chưa đăng nhập 401; Manager 403",
      lambda: (expect(call("GET", "/orders")[0] == 401, "phải 401"), expect(call("GET", "/orders", token=tm)[0] == 403, "phải 403")) and None)

    def c20_empty():
        r = call("GET", "/orders", token=te)
        expect(r[0] == 200 and r[1]["items"] == [] and r[1]["total"] == 0, f"{short(r[1])}")
    t("UC-C20", "Chưa có đơn -> danh sách rỗng (Alternative Flow)", c20_empty)

    def c20_list():
        r = call("GET", "/orders", token=ta)
        expect_status(r, 200)
        expect(r[1]["total"] >= 1, "thiếu đơn vừa đặt")
        o = r[1]["items"][0]
        for k in ("id", "code", "status", "total_amount", "item_count", "created_at"):
            expect(k in o, f"thiếu trường {k}")
        ids = [i["id"] for i in r[1]["items"]]
        expect(ids == sorted(ids, reverse=True), "đơn không xếp mới nhất trước")
    t("UC-C20", "Danh sách đơn của tôi: đủ trường, mới nhất trước (FR-25)", c20_list)

    def c20_detail():
        r = call("GET", f"/orders/{state['order']}", token=ta)
        expect_status(r, 200)
        d = r[1]
        expect(d["code"] == state["code"] and d["status"] == "CONFIRMED", f"{short(d)}")
        expect(Decimal(d["total_amount"]) == Decimal("20000000"), f"tổng tiền sai {d['total_amount']}")
        expect(d["items"][0]["product_name"] and d["recipient_name"] == SHIP["recipient_name"], "thiếu thông tin chi tiết")
        expect(d["history"] and d["history"][0]["status"] == "CONFIRMED", "thiếu lịch sử trạng thái")
    t("UC-C20", "Chi tiết đơn: sản phẩm, giá trị, nhận hàng, trạng thái, lịch sử", c20_detail)

    def c20_snapshot():
        set_product(p1.id, price=Decimal("99999999"))
        d = call("GET", f"/orders/{state['order']}", token=ta)[1]
        set_product(p1.id, price=Decimal("10000000"))
        expect(Decimal(d["total_amount"]) == Decimal("20000000") and Decimal(d["items"][0]["unit_price"]) == Decimal("10000000"),
               "giá đơn hàng thay đổi theo giá sản phẩm hiện tại")
    t("UC-C20", "Đơn lưu giá tại thời điểm mua (không đổi khi giá sản phẩm đổi)", c20_snapshot)

    def c20_isolation():
        r = call("GET", f"/orders/{state['order']}", token=tb)
        expect(r[0] == 404 and err_code(r[1]) == "ORDER_NOT_FOUND", f"xem đơn người khác phải 404, nhận {r[0]}")
        ids = [i["id"] for i in call("GET", "/orders", token=tb)[1]["items"]]
        expect(state["order"] not in ids, "danh sách đơn lọt đơn của người khác")
        expect(call("GET", "/orders/99999999", token=ta)[0] == 404, "đơn không tồn tại phải 404")
    t("UC-C20", "Chỉ xem được đơn của chính mình (BR) — đơn người khác 404", c20_isolation)

    def c20_page():
        for _ in range(2):
            add(ta, p1.id, 1)
            confirm(ta, start(ta)[1]["payment_id"])
        r = call("GET", "/orders", token=ta, query={"page": 2, "page_size": 2})
        expect(r[0] == 200 and r[1]["total"] >= 3 and len(r[1]["items"]) >= 1, f"phân trang sai: {short(r[1])}")
        expect(call("GET", "/orders", token=ta, query={"page_size": 500})[0] == 422, "page_size quá lớn phải 422")
    t("UC-C20", "Phân trang và giới hạn page_size", c20_page)

    def c20_time():
        t0 = time.time()
        call("GET", "/orders", token=ta)
        dt = time.time() - t0
        expect(dt <= 2, f"mất {dt:.2f}s")
        return f"{dt*1000:.0f} ms"
    t("UC-C20", "Phản hồi <= 2 giây", c20_time)


# ================================================================= báo cáo
def report():
    print("\n" + "=" * 78 + "\nTỔNG HỢP THEO USE CASE\n" + "=" * 78)
    ucs = sorted({r["uc"] for r in RESULTS}, key=lambda x: (x.startswith("UC-SM"), x))
    lines = ["| UC | PASS | FAIL | SKIP | Kết luận |", "|---|---|---|---|---|"]
    for uc in ucs:
        rs = [r for r in RESULTS if r["uc"] == uc]
        p = sum(r["status"] == "PASS" for r in rs); f = sum(r["status"] == "FAIL" for r in rs); s = sum(r["status"] == "SKIP" for r in rs)
        verdict = "Hoàn thiện" if f == 0 and s == 0 else ("Chưa hiện thực / chưa kiểm tra được" if p == 0 and f == 0 else ("Còn lỗi" if f else "Đạt phần đã kiểm tra"))
        lines.append(f"| {uc} | {p} | {f} | {s} | {verdict} |")
    print("\n".join(lines))
    tot = {k: sum(r["status"] == k for r in RESULTS) for k in ("PASS", "FAIL", "SKIP")}
    print(f"\nTổng: {tot['PASS']} PASS, {tot['FAIL']} FAIL, {tot['SKIP']} SKIP / {len(RESULTS)} kiểm tra")
    md = ["# Báo cáo kiểm tra Use Case\n", *lines, "\n## Chi tiết\n", "| UC | Yêu cầu | Kết quả | Ghi chú |", "|---|---|---|---|"]
    md += [f"| {r['uc']} | {r['req']} | {r['status']} | {r['note'].replace('|', '/')} |" for r in RESULTS]
    with open("uc_report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    print("Đã ghi uc_report.md")


def main():
    global BASE, ONLY
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.getenv("UC_BASE", "http://localhost:8000/api/v1"))
    ap.add_argument("--only", default="", help="vd: C18,C19,SM01")
    ap.add_argument("--keep", action="store_true", help="không xóa dữ liệu thử")
    ap.add_argument("--skip-phase2", action="store_true")
    a = ap.parse_args()
    BASE = a.base.rstrip("/")
    ONLY = {x.strip() for x in a.only.split(",") if x.strip()}
    print(f"Base: {BASE}   Tag dữ liệu: {TAG}")
    try:
        load_openapi()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Không đọc được openapi.json ({e}). Server đã chạy chưa? Thử --base đúng prefix.")
    try:
        if not a.skip_phase2:
            phase2()
        phase4()
    finally:
        if Env.db is not None and not a.keep:
            try:
                cleanup()
                print("\nĐã dọn dữ liệu thử.")
            except Exception as e:  # noqa: BLE001
                print(f"\nCẢNH BÁO: dọn dữ liệu lỗi ({e}); xóa tay các bản ghi có tiền tố uccheck/UCCHK-")
    report()


if __name__ == "__main__":
    main()