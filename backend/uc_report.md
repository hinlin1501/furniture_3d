# Báo cáo kiểm tra Use Case

| UC | PASS | FAIL | SKIP | Kết luận |
|---|---|---|---|---|
| UC-C20 | 8 | 0 | 0 | Hoàn thiện |

## Chi tiết

| UC | Yêu cầu | Kết quả | Ghi chú |
|---|---|---|---|
| UC-C20 | Chưa đăng nhập 401; Manager 403 | PASS |  |
| UC-C20 | Chưa có đơn -> danh sách rỗng (Alternative Flow) | PASS |  |
| UC-C20 | Danh sách đơn của tôi: đủ trường, mới nhất trước (FR-25) | PASS |  |
| UC-C20 | Chi tiết đơn: sản phẩm, giá trị, nhận hàng, trạng thái, lịch sử | PASS |  |
| UC-C20 | Đơn lưu giá tại thời điểm mua (không đổi khi giá sản phẩm đổi) | PASS |  |
| UC-C20 | Chỉ xem được đơn của chính mình (BR) — đơn người khác 404 | PASS |  |
| UC-C20 | Phân trang và giới hạn page_size | PASS |  |
| UC-C20 | Phản hồi <= 2 giây | PASS | 20 ms |