// Client REST tối thiểu. Token lưu trong sessionStorage (Phase 1 có thể thay bằng cơ chế sẵn có).
const TOKEN_KEY = "ef_token";
export const getToken = () => { try { return sessionStorage.getItem(TOKEN_KEY); } catch { return null; } };
export const setToken = (t) => { try { t ? sessionStorage.setItem(TOKEN_KEY, t) : sessionStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ } };

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : detail?.message || "Đã xảy ra lỗi");
    this.status = status;
    this.code = detail?.code;
    this.detail = detail;
  }
}

// Envelope lỗi của backend: {"error": {"code", "message", "details", "request_id"}}
function toApiError(status, data) {
  const e = data?.error;
  if (!e) return new ApiError(status, { message: "Đã xảy ra lỗi" });
  let message = e.message;
  if (e.code === "VALIDATION_ERROR" && Array.isArray(e.details))
    message = e.details.map((d) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ");
  return new ApiError(status, { code: e.code, message, details: e.details });
}

export async function api(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(`/api/v1${path}`, {
      method,
      headers: { "Content-Type": "application/json", ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Không thể kết nối tới máy chủ. Vui lòng thử lại.");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw toApiError(res.status, data);
  return data;
}

// Backend trả tiền dạng chuỗi Decimal (vd "4990000.00")
export const vnd = (n) => new Intl.NumberFormat("vi-VN").format(Number(n)) + " ₫";
export const fmtDate = (s) => new Date(s).toLocaleString("vi-VN");
export const STATUS_LABEL = {
  CONFIRMED: "Đã xác nhận", PREPARING: "Đang chuẩn bị hàng", SHIPPING: "Đang giao", COMPLETED: "Hoàn tất",
};
export const ISSUE_LABEL = {
  PRODUCT_UNAVAILABLE: "Sản phẩm không còn khả dụng", OUT_OF_STOCK: "Đã hết hàng",
  INSUFFICIENT_STOCK: "Vượt quá số lượng tồn kho",
};
