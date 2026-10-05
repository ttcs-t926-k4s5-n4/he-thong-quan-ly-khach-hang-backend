// ActivationPage.jsx — Kích hoạt tài khoản qua link email (S1-08)
import { useEffect, useState } from "react";
import { apiActivateUser } from "../api/index.js";

export default function ActivationPage({ token, onGoLogin }) {
  const [state, setState] = useState("loading"); // loading | success | error
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiActivateUser(token)
      .then(res => { setMessage(res.message); setState("success"); })
      .catch(err => { setMessage(err.data?.message || "Kích hoạt thất bại."); setState("error"); });
  }, [token]);

  return (
    <div style={{
      minHeight: "100vh", display: "grid", placeItems: "center",
      background: "linear-gradient(135deg, var(--indigo-900) 0%, var(--violet-600) 100%)",
      padding: 24,
    }}>
      <div style={{
        background: "white", borderRadius: 24, padding: "48px 40px",
        width: "min(460px,100%)", textAlign: "center", boxShadow: "0 25px 60px rgba(0,0,0,.25)",
        animation: "scaleIn .3s ease",
      }}>
        {state === "loading" && (
          <>
            <div className="spinner spinner-dark" style={{ margin: "0 auto 20px", width: 40, height: 40, borderWidth: 3 }} />
            <h2 style={{ marginBottom: 8 }}>Đang kích hoạt...</h2>
            <p style={{ color: "var(--gray-500)" }}>Vui lòng chờ trong giây lát.</p>
          </>
        )}
        {state === "success" && (
          <>
            <div style={{ fontSize: "4rem", marginBottom: 16 }}>🎉</div>
            <h2 style={{ marginBottom: 8, color: "var(--gray-900)" }}>Kích hoạt thành công!</h2>
            <p style={{ color: "var(--gray-600)", marginBottom: 24 }}>{message}</p>
            <button className="btn btn-primary" onClick={onGoLogin}>Đăng nhập ngay →</button>
          </>
        )}
        {state === "error" && (
          <>
            <div style={{ fontSize: "4rem", marginBottom: 16 }}>⚠️</div>
            <h2 style={{ marginBottom: 8, color: "var(--gray-900)" }}>Kích hoạt thất bại</h2>
            <p style={{ color: "var(--error)", marginBottom: 24 }}>{message}</p>
            <button className="btn btn-secondary" onClick={onGoLogin}>Quay lại đăng nhập</button>
          </>
        )}
      </div>
    </div>
  );
}
