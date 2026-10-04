import { useEffect, useState } from "react";
import { activateUser } from "./api";

export default function ActivationPage({ token }) {
  const [state, setState] = useState({
    loading: true,
    success: false,
    message: "Đang kích hoạt tài khoản...",
  });

  useEffect(() => {
    activateUser(token)
      .then((result) => {
        setState({
          loading: false,
          success: true,
          message: result.message || "Kích hoạt tài khoản thành công.",
        });
      })
      .catch((error) => {
        setState({
          loading: false,
          success: false,
          message:
            error.data?.message ||
            "Liên kết kích hoạt không hợp lệ hoặc đã hết hạn.",
        });
      });
  }, [token]);

  return (
    <main className="activationPage">
      <section className="activationCard">
        <div className={state.success ? "activationIcon ok" : "activationIcon"}>
          {state.loading ? "…" : state.success ? "✓" : "!"}
        </div>
        <h1>{state.success ? "Kích hoạt tài khoản" : "Xác nhận tài khoản"}</h1>
        <p>{state.message}</p>
        {!state.loading && (
          <a className="primaryButton activationButton" href="/">
            Về trang quản lý
          </a>
        )}
      </section>
    </main>
  );
}
