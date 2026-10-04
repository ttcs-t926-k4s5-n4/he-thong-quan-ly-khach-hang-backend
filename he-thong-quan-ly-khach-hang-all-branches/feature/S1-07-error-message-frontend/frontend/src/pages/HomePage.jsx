import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <section className="home-page">
      <div className="hero">
        <div className="hero-badge">S1-07 · Xử lý thông báo lỗi</div>
        <h1>Trang báo lỗi dùng chung</h1>
        <p>
          Giao diện thống nhất cho các tình huống người dùng truy cập nhầm,
          không đủ quyền hoặc hệ thống gặp sự cố.
        </p>
      </div>

      <div className="section-heading">
        <h2>Các tình huống đã triển khai</h2>
        <span>3 loại lỗi</span>
      </div>

      <div className="error-grid">
        <Link to="/403" className="error-demo-card">
          <span className="mini-code">403</span>
          <h3>Không có quyền</h3>
          <p>Thông báo khi người dùng truy cập chức năng không được phép.</p>
          <span className="card-link">Xem trang →</span>
        </Link>
        <Link to="/404" className="error-demo-card">
          <span className="mini-code">404</span>
          <h3>Không tìm thấy</h3>
          <p>Thông báo khi đường dẫn hoặc tài nguyên không tồn tại.</p>
          <span className="card-link">Xem trang →</span>
        </Link>
        <Link to="/500" className="error-demo-card">
          <span className="mini-code">500</span>
          <h3>Lỗi hệ thống</h3>
          <p>Thông báo khi máy chủ gặp sự cố trong quá trình xử lý.</p>
          <span className="card-link">Xem trang →</span>
        </Link>
      </div>
    </section>
  )
}

export default HomePage
