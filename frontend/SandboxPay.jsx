import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api, vnd } from "../api.js";
import { useCart } from "../cart.jsx";

// Giao diện giả lập cổng thanh toán (Payment Sandbox).
export default function SandboxPay() {
  const { paymentId } = useParams();
  const { state } = useLocation();
  const { refresh } = useCart();
  const nav = useNavigate();
  const [pay, setPay] = useState(state?.session || null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api(`/payments/${paymentId}`)
      .then((s) => {
        if (s.status === "SUCCESS") nav(`/orders/${s.order_id}`, { replace: true, state: { placed: s.order_code } });
        else if (s.status !== "PENDING") setResult(s);
      })
      .catch((e) => setError(e.message));
  }, [paymentId, nav]);

  const confirm = async (outcome) => {
    setBusy(true); setError("");
    try {
      const r = await api(`/payments/${paymentId}/sandbox-confirm`, { method: "POST", body: { outcome } });
      await refresh();
      if (r.status === "SUCCESS") nav(`/orders/${r.order_id}`, { replace: true, state: { placed: r.order_code } });
      else setResult(r);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  if (result && result.status !== "PENDING") {
    const refunded = result.status === "REFUNDED";
    return (
      <div className="card narrow">
        <h2>{refunded ? "Không thể tạo đơn hàng" : "Thanh toán không thành công"}</h2>
        <p className="error">{result.failure_reason || "Giao dịch không hoàn tất."}</p>
        <p className="muted">Đơn hàng chưa được xác lập{refunded ? "" : ", giỏ hàng của bạn được giữ nguyên"}.</p>
        <Link className="primary btn" to="/cart">Quay lại giỏ hàng</Link>
      </div>
    );
  }

  return (
    <div className="card narrow">
      <h2>Cổng thanh toán Sandbox</h2>
      <p className="muted">Môi trường thử nghiệm – không phát sinh giao dịch thật.</p>
      {pay && <p>Số tiền: <strong>{vnd(pay.amount)}</strong> · Mã giao dịch: {pay.gateway_ref}</p>}
      {error && <p className="error" role="alert">{error}</p>}
      <div className="actions">
        <button className="primary" disabled={busy} onClick={() => confirm("SUCCESS")}>Xác nhận thanh toán</button>
        <button disabled={busy} onClick={() => confirm("FAILED")}>Giả lập thất bại</button>
        <button disabled={busy} onClick={() => confirm("EXPIRED")}>Giả lập hết hạn</button>
      </div>
    </div>
  );
}
