# HLK E-Furniture Platform – Backend

FastAPI + SQLAlchemy 2 + PostgreSQL. Modular monolith (api → services → repositories → models).

**Trạng thái:** Phase 1 (nền tảng tối thiểu) + **Phase 2 (Core E-Commerce)** đã hoàn thành.
Các phase 3–9 (assets/3D, giỏ hàng & thanh toán, spatial, AI, chatbot, QR, admin logs...) **chưa được hiện thực**.

## Chạy nhanh (local)

```bash
cd backend
pip install -r requirements-dev.txt
cp .env.example .env            # điền DATABASE_URL và JWT_SECRET_KEY (>= 32 ký tự)
alembic upgrade head            # tạo schema
SEED_MANAGER_EMAIL=manager@example.com SEED_MANAGER_PASSWORD='<mật khẩu>' \
  python -m scripts.seed --demo # tạo tài khoản STORE_MANAGER (+ vài sản phẩm DEMO-*)
uvicorn app.main:app --reload   # http://localhost:8000/docs
```

Docker: tạo `.env` có `POSTGRES_PASSWORD` và `JWT_SECRET_KEY`, rồi `docker compose up --build`,
sau đó `docker compose exec backend alembic upgrade head`. (*Cấu hình Docker chưa được chạy thử trong môi trường phát triển.*)

## Test

```bash
pytest                                                    # SQLite in-memory
TEST_DATABASE_URL=postgresql+psycopg2://u:p@host/db_test pytest   # PostgreSQL (DB test bị drop/create mỗi test!)
```

## Biến môi trường

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `DATABASE_URL` | ✔ | SQLAlchemy URL, vd `postgresql+psycopg2://...` |
| `JWT_SECRET_KEY` | ✔ | ≥ 32 ký tự, không có giá trị mặc định |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | mặc định 60 |
| `CORS_ORIGINS` | | JSON list, mặc định `["http://localhost:5173"]` |
| `ENVIRONMENT` | | `production` sẽ tắt `/docs` |
| `LOG_LEVEL` | | mặc định `INFO` |

## API (prefix `/api/v1`)

| Method | Path | Quyền | FR |
|---|---|---|---|
| POST | `/auth/register` | public | FR-01 |
| POST | `/auth/login` | public | FR-02 |
| GET / PATCH | `/users/me` | đăng nhập | FR-03 |
| GET | `/categories`, `/categories/{id}` | public | FR-05 |
| GET | `/products` | public | FR-06, FR-07 |
| GET | `/products/{id}`, `/products/{id}/assets` | public | FR-08 |
| GET/POST | `/admin/categories` | STORE_MANAGER | FR-27 |
| PATCH/DELETE | `/admin/categories/{id}` | STORE_MANAGER | FR-27 |
| GET/POST | `/admin/products` | STORE_MANAGER | FR-26 (cơ bản) |
| GET/PATCH/DELETE | `/admin/products/{id}` | STORE_MANAGER | FR-26 (DELETE = soft delete) |
| GET | `/health`, `/health/ready` | public | |

`GET /products` hỗ trợ: `q`, `category_id` (+`include_subcategories`), `min_price`, `max_price`, `material`, `style`, `color`
(lặp tham số để chọn nhiều giá trị: OR trong cùng loại, AND giữa các loại), `min/max_length_cm|width_cm|height_cm`,
`in_stock_only`, `sort` (`newest|price_asc|price_desc|name_asc`), `page`, `page_size` (≤ 100).

## Quy ước

- Lỗi luôn có dạng `{"error": {"code": "...", "message": "...", "details": ...}}`.
- Danh sách trả về `{items, total, page, page_size, pages}`.
- **Tiền tệ (`price`) được serialize dạng chuỗi** (`"12990000.00"`) để tránh sai số float – frontend cần parse.
- Role và trạng thái active luôn lấy từ DB, không tin vào token. Đăng ký luôn tạo `CUSTOMER`; manager chỉ được tạo qua `scripts/seed.py`.
- Public API chỉ trả sản phẩm `ACTIVE` và không lộ `stock_quantity` (chỉ `stock_status`).

## Quyết định thiết kế đáng chú ý

- Enum lưu dạng `VARCHAR + CHECK` (không dùng native PG enum) để migration đơn giản.
- Thuộc tính vật liệu/phong cách/màu nằm trong bảng `product_attributes` (type + value) để lọc linh hoạt và dùng lại cho AI ở Phase 6.
- Không xoá cứng sản phẩm; không xoá danh mục còn sản phẩm (kể cả sản phẩm INACTIVE – hãy vô hiệu hoá danh mục).
- Migration được sinh bằng autogenerate **trên PostgreSQL** (sinh trên SQLite sẽ lệch `server_default`).

## Hạn chế đã biết

- Chưa có đổi email có xác minh (UC-C03 BR2), refresh token, đổi/quên mật khẩu, rate-limit đăng nhập.
- Tìm kiếm dùng `ILIKE '%...%'` (không bỏ dấu tiếng Việt, quét tuần tự). Khi dữ liệu lớn: bật `pg_trgm` + `unaccent`.
- Chưa có API upload/đăng ký asset (ảnh, GLB) – bảng `product_images`/`product_models` đã có và được đọc ra, nhưng ghi dữ liệu thuộc Phase 3.
- Chưa có bảng `Review`, `UserPreference`... (các phase sau).
