import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, fmtDate, STATUS_LABEL, vnd } from "../api.js";

const STEPS = ["CONFIRMED", "PREPARING", "SHIPPING", "COMPLETED"];
const METHOD = { SANDBOX_CARD: "Thẻ (Sandbox)", SANDBOX_WALLET: "Ví điện tử (Sandbox)" };

export default function OrderDetail() {
  const { id } = useParams();
  const { state } = useLocation();
  const [o, setO] = useState(null);
  const [error, setError] = useState("");
  const load = () => { setError(""); api(`/orders/${id}`).then(setO).catch((e) => setError(e.message)); };
  useEffect(load, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return (<><p className="error" role="alert">{error}</p><button onClick={load}>Thử lại</button> <Link to="/orders">Về danh sách</Link></>);
  if (!o) return <p>Đang tải…</p>;
  const reached = new Set(o.history.map((h) => h.status));
  return (
    <>
      {state?.placed && <p className="ok" role="status">Đặt hàng thành công! Mã đơn hàng của bạn: <strong>{state.placed}</strong></p>}
      <h1>Đơn hàng {o.code}</h1>
      <ol className="steps">
        {STEPS.map((s) => <li key={s} className={reached.has(s) ? "done" : ""}>{STATUS_LABEL[s]}</li>)}
      </ol>
      <table className="table">
        <thead><tr><th>Sản phẩm</th><th>Đơn giá</th><th>SL</th><th>Thành tiền</th></tr></thead>
        <tbody>
          {o.items.map((i, idx) => (
            <tr key={idx}><td>{i.product_name}</td><td>{vnd(i.unit_price)}</td><td>{i.quantity}</td><td>{vnd(Number(i.unit_price) * i.quantity)}</td></tr>
          ))}
        </tbody>
      </table>
      <div className="summary"><div>Tổng giá trị đơn hàng: <strong>{vnd(o.total_amount)}</strong></div></div>
      <section className="card">
        <h2>Thông tin nhận hàng</h2>
        <p>{o.recipient_name} · {o.phone}</p><p>{o.shipping_address}</p>
        {o.note && <p className="muted">Ghi chú: {o.note}</p>}
        <p className="muted">Thanh toán: {METHOD[o.payment_method] || o.payment_method} · Đặt lúc {fmtDate(o.created_at)}</p>
      </section>
      <section className="card">
        <h2>Lịch sử trạng thái</h2>
        <ul>{o.history.map((h, i) => <li key={i}>{STATUS_LABEL[h.status]} – {fmtDate(h.created_at)}</li>)}</ul>
      </section>
      <Link to="/orders">← Đơn hàng của tôi</Link>
    </>
  );
}
