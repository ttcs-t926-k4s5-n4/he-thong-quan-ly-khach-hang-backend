import { Link, Route, Routes } from 'react-router-dom'
import ErrorPage from './components/ErrorPage'
import HomePage from './pages/HomePage'
import './app.css'

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand-mark">CRM</span>
          <span>Hệ thống quản lý khách hàng</span>
        </Link>
        <nav className="topnav" aria-label="Điều hướng chính">
          <Link to="/">Trang chủ</Link>
          <Link to="/403">403</Link>
          <Link to="/404">404</Link>
          <Link to="/500">500</Link>
        </nav>
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/403"
            element={
              <ErrorPage
                code="403"
                title="Bạn không có quyền truy cập"
                description="Tài khoản hiện tại không có quyền xem nội dung này. Hãy quay lại trang trước hoặc trở về trang chủ để tiếp tục làm việc."
                actionText="Về trang chủ"
                icon="lock"
              />
            }
          />
          <Route
            path="/404"
            element={
              <ErrorPage
                code="404"
                title="Không tìm thấy trang"
                description="Trang bạn đang tìm có thể đã được chuyển, bị xóa hoặc đường dẫn không chính xác. Bạn có thể quay lại luồng làm việc của mình."
                actionText="Về trang chủ"
                icon="search"
              />
            }
          />
          <Route
            path="/500"
            element={
              <ErrorPage
                code="500"
                title="Đã xảy ra lỗi"
                description="Hệ thống gặp sự cố khi xử lý yêu cầu. Vui lòng thử lại hoặc quay về trang chủ để tiếp tục sử dụng ứng dụng."
                actionText="Thử lại"
                icon="server"
                retry
              />
            }
          />
          <Route
            path="*"
            element={
              <ErrorPage
                code="404"
                title="Không tìm thấy trang"
                description="Đường dẫn bạn truy cập không tồn tại trong ứng dụng."
                actionText="Về trang chủ"
                icon="search"
              />
            }
          />
        </Routes>
      </main>

      <footer className="footer">
        <span>Hệ thống quản lý khách hàng</span>
        <span>•</span>
        <span>Trang báo lỗi dùng chung</span>
      </footer>
    </div>
  )
}

export default App
