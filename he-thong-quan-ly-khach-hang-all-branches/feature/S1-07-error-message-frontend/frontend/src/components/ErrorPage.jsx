import { useNavigate } from 'react-router-dom'

const iconMap = {
  lock: (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <rect x="13" y="27" width="38" height="28" rx="6" />
      <path d="M21 27v-8c0-7 4.5-12 11-12s11 5 11 12v8" />
      <circle cx="32" cy="41" r="3" />
      <path d="M32 44v5" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="28" cy="28" r="15" />
      <path d="m40 40 13 13" />
      <path d="M23 28h10M28 23v10" />
    </svg>
  ),
  server: (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <rect x="10" y="10" width="44" height="16" rx="4" />
      <rect x="10" y="38" width="44" height="16" rx="4" />
      <path d="M18 18h2M18 46h2M28 18h18M28 46h18" />
    </svg>
  ),
}

function ErrorPage({ code, title, description, actionText, icon, retry = false }) {
  const navigate = useNavigate()

  const handleAction = () => {
    if (retry) {
      window.location.reload()
      return
    }
    navigate('/')
  }

  return (
    <section className="error-page" aria-labelledby="error-title">
      <div className="error-card">
        <div className={`error-icon error-icon-${icon}`}>{iconMap[icon]}</div>
        <div className="error-code">{code}</div>
        <h1 id="error-title">{title}</h1>
        <p>{description}</p>

        <div className="error-actions">
          <button className="primary-button" onClick={handleAction}>
            {actionText}
            <span aria-hidden="true">→</span>
          </button>
          <button className="secondary-button" onClick={() => navigate(-1)}>
            ← Quay lại trang trước
          </button>
        </div>

        <div className="help-box">
          <span className="help-dot">i</span>
          <span>Nếu bạn cho rằng đây là lỗi, hãy kiểm tra đường dẫn hoặc liên hệ quản trị viên hệ thống.</span>
        </div>
      </div>
    </section>
  )
}

export default ErrorPage
