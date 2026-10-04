# HỆ THỐNG MENU ĐIỀU HƯỚNG PHÂN QUYỀN (RBAC NAVIGATION SYSTEM)
> **Mã User Story:** SCRUM-16 / SCRUM-30  
> **Ngôn ngữ thực hiện:** Python (Flask Framework) + Modern Responsive HTML5/CSS3/Vanilla JS  
> **Môi trường chạy:** Visual Studio Code (VS Code) trên Windows  

---

## 🎯 1. NỘI DUNG YÊU CẦU & TIÊU CHÍ CHẤP NHẬN (ACCEPTANCE CRITERIA)

| Tiêu Chí | Yêu Cầu Của Đề Bài | Cách Hệ Thống Đáp Ứng |
| :--- | :--- | :--- |
| **Tiêu chí 1** | *Mục menu không thuộc quyền thì không hiển thị* | Hàm `get_user_menu(user)` lọc danh sách menu trước khi render ra giao diện. Các mục ngoài quyền **bị xóa hoàn toàn khỏi DOM**, không chỉ bị ẩn CSS. Backend có `@require_permission` chặn truy cập trực tiếp. |
| **Tiêu chí 2** | *Hiển thị tên, vai trò và nhóm kinh doanh đang thuộc về* | Thẻ **User Profile Card** hiển thị nổi bật: **Họ và tên**, **Badge vai trò** (Giám đốc / Trưởng nhóm / Chuyên viên / Thực tập) và **Tên Nhóm kinh doanh**. |
| **Tiêu chí 3** | *Dùng được thuận tiện trên màn hình 360px* | Thiết kế chuẩn **Mobile-First**: Thanh Navigation chuyển thành Drawer trượt cảm ứng (off-canvas), nút bấm chuẩn touch target $\ge 44\text{px}$, không vỡ layout, tích hợp sẵn nút **Giả lập khung 360px** ngay trên web. |

---

## 🚀 2. HƯỚNG DẪN CÀI ĐẶT & CHẠY TRÊN VISUAL STUDIO CODE

### Bước 1: Mở thư mục dự án trong VS Code
1. Mở Visual Studio Code.
2. Chọn **File** -> **Open Folder...** (hoặc `Ctrl + K, Ctrl + O`).
3. Chọn thư mục:

### Bước 2: Mở Terminal trong VS Code
- Nhấn tổ hợp phím: `Ctrl + ~` (hoặc vào menu **Terminal** -> **New Terminal**).

### Bước 3: Cài đặt thư viện (nếu chưa cài)
```bash
py -m pip install flask
```
*(Nếu máy dùng lệnh `python` thay vì `py`, bạn gõ `python -m pip install flask`)*

### Bước 4: Khởi chạy ứng dụng
```bash
py app.py
```
*(hoặc `python app.py`)*

Terminal sẽ hiển thị:
```text
============================================================
 HỆ THỐNG MENU ĐIỀU HƯỚNG PHÂN QUYỀN (RBAC NAVIGATION SYSTEM)
 User Story: SCRUM-16 / SCRUM-30
 Đang chạy tại: http://127.0.0.1:5000
============================================================
```

### Bước 5: Mở trên trình duyệt
- Mở trình duyệt (Chrome, Edge) và truy cập: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 3. HƯỚNG DẪN KIỂM THỬ VÀ BÁO CÁO

### A. Kiểm tra Tiêu chí 1: Ẩn menu không thuộc quyền
Ở thanh điều hướng (hoặc góc dưới sidebar), có 4 nút đổi vai trò để thử nghiệm nhanh:
1. **Giám đốc kinh doanh:** Thấy toàn bộ **7 mục menu** (Bảng điều khiển, Khách hàng, Đơn hàng, Báo cáo nhóm, Chỉ tiêu nhóm, Quản lý nhân viên, Cấu hình).
2. **Trưởng nhóm kinh doanh:** Thấy **5 mục menu** (Không thấy "Quản lý nhân viên" và "Cấu hình").
3. **Chuyên viên kinh doanh:** Thấy **3 mục menu** (Chỉ thấy Bảng điều khiển, Khách hàng của tôi, Đơn hàng).
4. **Thực tập sinh kinh doanh:** Chỉ thấy duy nhất **1 mục menu** (Bảng điều khiển).

### B. Kiểm tra Tiêu chí 2: Hiển thị Tên, Vai trò, Nhóm kinh doanh
- Nhìn vào khối thông tin cá nhân trên thanh điều hướng hoặc góc phải trên cùng:
  - **Tên:** Ví dụ `Lê Hoàng Phúc`
  - **Vai trò:** `Chuyên viên kinh doanh`
  - **Nhóm kinh doanh:** `Nhóm Bán Lẻ Khu Vực Miền Bắc`

### C. Kiểm tra Tiêu chí 3: Tương thích màn hình 360px
- **Cách 1 (Nhanh nhất):** Bấm nút **"📱 Giả lập màn hình 360px"** màu xanh ở góc trên cùng bên phải. Giao diện sẽ tự động co về khung điện thoại chuẩn 360px có viền điện thoại để bạn kiểm tra nút Hamburger 3 gạch và Menu Drawer.
- **Cách 2 (Chuẩn Developer Tools):**
  1. Nhấn phím `F12` trên Chrome hoặc Edge.
  2. Nhấn `Ctrl + Shift + M` (Toggle device toolbar).
  3. Chọn kích thước chiều rộng là **360px** (ví dụ 360 x 740 hoặc 360 x 640).
  4. Bấm vào nút Hamburger ☰ ở góc trái trên cùng để mở Drawer điều hướng mượt mà.

---

## 🛡️ 4. CHẠY BỘ KIỂM THỬ TỰ ĐỘNG (UNIT TESTS)

Dự án có sẵn bộ test chuẩn `unittest` kiểm thử logic phân quyền và an toàn bảo mật route:
```bash
py -m unittest tests/test_rbac.py
```
Kết quả chạy:
```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.098s

OK
```

---

## 📂 5. CẤU TRÚC DỰ ÁN

```text
rbac_navigation_system/
├── app.py                   # File chính: Backend Flask, phân quyền RBAC, lọc menu, route
├── static/
│   ├── style.css            # Toàn bộ CSS giao diện: Responsive chuẩn 360px, Mobile Drawer, Glassmorphism
│   └── script.js           # Xử lý mở/đóng menu cảm ứng trên 360px & nút giả lập thiết bị
├── templates/
│   ├── base.html            # Khung giao diện master: Sidebar, User card, Header 360px, Hamburger
│   └── pages/
│       ├── dashboard.html   # Bảng điều khiển & Ma trận đối chiếu phân quyền trực quan
│       ├── customers.html   # Quản lý khách hàng (CRM)
│       ├── deals.html       # Đơn hàng & Hợp đồng
│       ├── team_reports.html# Báo cáo doanh số nhóm
│       ├── team_targets.html# Chỉ tiêu & KPI nhóm
│       ├── users.html       # Quản lý nhân viên
│       └── settings.html    # Cấu hình hệ thống
├── tests/
│   └── test_rbac.py         # 7 kịch bản kiểm thử tự động xác thực các tiêu chí của User Story
└── README.md                # Tài liệu hướng dẫn sử dụng chi tiết
```
