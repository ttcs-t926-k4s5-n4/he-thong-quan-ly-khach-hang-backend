/**
 * Xử lý tương tác giao diện Menu Responsive 360px và Chế độ Giả Lập Thiết Bị
 * User Story: SCRUM-16 / SCRUM-30
 */

document.addEventListener('DOMContentLoaded', () => {
  const hamburgerBtn = document.getElementById('hamburger-btn');
  const closeDrawerBtn = document.getElementById('close-drawer-btn');
  const sidebar = document.getElementById('main-sidebar');
  const drawerOverlay = document.getElementById('drawer-overlay');
  const toggle360Btn = document.getElementById('toggle-360-btn');
  const simulatorWrapper = document.getElementById('simulator-wrapper');
  const simulatorBtnLabel = document.getElementById('simulator-btn-label');

  // ========================================================
  // 1. MỞ VÀ ĐÓNG MENU DRAWER TRÊN MÀN HÌNH NHỎ (<= 360px / 768px)
  // ========================================================
  function openDrawer() {
    if (sidebar && drawerOverlay) {
      sidebar.classList.add('open');
      drawerOverlay.classList.add('active');
      document.body.style.overflow = 'hidden'; // Khóa cuộn trang nền khi mở drawer
    }
  }

  function closeDrawer() {
    if (sidebar && drawerOverlay) {
      sidebar.classList.remove('open');
      drawerOverlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  if (hamburgerBtn) {
    hamburgerBtn.addEventListener('click', openDrawer);
  }

  if (closeDrawerBtn) {
    closeDrawerBtn.addEventListener('click', closeDrawer);
  }

  if (drawerOverlay) {
    drawerOverlay.addEventListener('click', closeDrawer);
  }

  // Đóng drawer khi nhấn phím ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
      closeDrawer();
    }
  });

  // Tự động đóng drawer khi click vào link điều hướng (trên mobile)
  const navLinks = document.querySelectorAll('.nav-menu-item');
  navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 768 || (simulatorWrapper && simulatorWrapper.classList.contains('simulator-active'))) {
        closeDrawer();
      }
    });
  });

  // ========================================================
  // 2. TÍNH NĂNG TIỆN LỢI: BẬT / TẮT GIẢ LẬP MÀN HÌNH 360PX
  // Giúp giáo viên/sinh viên kiểm thử trực tiếp chuẩn 360px trên màn hình PC
  // ========================================================
  if (toggle360Btn && simulatorWrapper) {
    toggle360Btn.addEventListener('click', () => {
      const isSimulatorActive = simulatorWrapper.classList.toggle('simulator-active');
      
      if (isSimulatorActive) {
        simulatorBtnLabel.textContent = '✕ Thoát Giả Lập 360px (Mở Rộng)';
        toggle360Btn.style.background = '#38bdf8';
        toggle360Btn.style.color = '#0f172a';
      } else {
        simulatorBtnLabel.textContent = '📱 Giả lập màn hình 360px';
        toggle360Btn.style.background = '';
        toggle360Btn.style.color = '';
        closeDrawer();
      }
    });
  }

  console.log("RBAC Navigation System (SCRUM-16 / SCRUM-30) đã sẵn sàng!");
});
