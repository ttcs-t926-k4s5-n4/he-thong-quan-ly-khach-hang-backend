# ==============================================================================
# ĐẶC TẢ NGHIỆP VỤ & KỊCH BẢN PHÁT TRIỂN: SCRUM-80 BẢNG THEO DÕI UTM CAMPAIGN
# Tác giả: PHUC NGUYEN HONG (dtc245200118@ictu.edu.vn)
# ==============================================================================
# [001] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 1
#       - Tham số cấu hình: CONFIG_OPTION_1 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_1') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [002] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 2
#       - Tham số cấu hình: CONFIG_OPTION_2 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_2') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [003] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 3
#       - Tham số cấu hình: CONFIG_OPTION_3 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_3') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [004] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 4
#       - Tham số cấu hình: CONFIG_OPTION_4 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_4') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [005] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 5
#       - Tham số cấu hình: CONFIG_OPTION_5 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_5') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [006] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 6
#       - Tham số cấu hình: CONFIG_OPTION_6 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_6') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [007] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 7
#       - Tham số cấu hình: CONFIG_OPTION_7 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_7') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [008] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 8
#       - Tham số cấu hình: CONFIG_OPTION_8 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_8') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [009] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 9
#       - Tham số cấu hình: CONFIG_OPTION_9 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_9') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [010] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 10
#       - Tham số cấu hình: CONFIG_OPTION_10 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_10') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [011] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 11
#       - Tham số cấu hình: CONFIG_OPTION_11 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_11') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [012] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 12
#       - Tham số cấu hình: CONFIG_OPTION_12 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_12') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [013] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 13
#       - Tham số cấu hình: CONFIG_OPTION_13 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_13') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [014] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 14
#       - Tham số cấu hình: CONFIG_OPTION_14 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_14') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [015] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 15
#       - Tham số cấu hình: CONFIG_OPTION_15 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_15') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [016] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 16
#       - Tham số cấu hình: CONFIG_OPTION_16 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_16') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [017] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 17
#       - Tham số cấu hình: CONFIG_OPTION_17 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_17') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [018] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 18
#       - Tham số cấu hình: CONFIG_OPTION_18 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_18') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [019] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 19
#       - Tham số cấu hình: CONFIG_OPTION_19 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_19') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [020] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 20
#       - Tham số cấu hình: CONFIG_OPTION_20 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_20') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [021] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 21
#       - Tham số cấu hình: CONFIG_OPTION_21 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_21') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [022] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 22
#       - Tham số cấu hình: CONFIG_OPTION_22 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_22') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [023] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 23
#       - Tham số cấu hình: CONFIG_OPTION_23 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_23') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [024] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 24
#       - Tham số cấu hình: CONFIG_OPTION_24 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_24') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [025] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 25
#       - Tham số cấu hình: CONFIG_OPTION_25 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_25') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [026] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 26
#       - Tham số cấu hình: CONFIG_OPTION_26 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_26') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [027] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 27
#       - Tham số cấu hình: CONFIG_OPTION_27 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_27') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [028] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 28
#       - Tham số cấu hình: CONFIG_OPTION_28 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_28') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [029] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 29
#       - Tham số cấu hình: CONFIG_OPTION_29 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_29') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [030] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 30
#       - Tham số cấu hình: CONFIG_OPTION_30 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_30') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [031] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 31
#       - Tham số cấu hình: CONFIG_OPTION_31 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_31') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [032] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 32
#       - Tham số cấu hình: CONFIG_OPTION_32 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_32') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [033] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 33
#       - Tham số cấu hình: CONFIG_OPTION_33 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_33') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [034] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 34
#       - Tham số cấu hình: CONFIG_OPTION_34 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_34') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [035] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 35
#       - Tham số cấu hình: CONFIG_OPTION_35 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_35') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [036] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 36
#       - Tham số cấu hình: CONFIG_OPTION_36 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_36') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [037] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 37
#       - Tham số cấu hình: CONFIG_OPTION_37 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_37') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [038] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 38
#       - Tham số cấu hình: CONFIG_OPTION_38 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_38') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [039] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 39
#       - Tham số cấu hình: CONFIG_OPTION_39 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_39') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [040] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 40
#       - Tham số cấu hình: CONFIG_OPTION_40 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_40') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [041] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 41
#       - Tham số cấu hình: CONFIG_OPTION_41 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_41') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [042] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 42
#       - Tham số cấu hình: CONFIG_OPTION_42 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_42') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [043] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 43
#       - Tham số cấu hình: CONFIG_OPTION_43 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_43') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [044] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 44
#       - Tham số cấu hình: CONFIG_OPTION_44 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_44') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [045] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 45
#       - Tham số cấu hình: CONFIG_OPTION_45 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_45') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [046] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 46
#       - Tham số cấu hình: CONFIG_OPTION_46 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_46') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [047] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 47
#       - Tham số cấu hình: CONFIG_OPTION_47 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_47') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [048] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 48
#       - Tham số cấu hình: CONFIG_OPTION_48 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_48') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [049] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 49
#       - Tham số cấu hình: CONFIG_OPTION_49 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_49') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [050] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 50
#       - Tham số cấu hình: CONFIG_OPTION_50 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_50') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [051] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 51
#       - Tham số cấu hình: CONFIG_OPTION_51 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_51') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [052] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 52
#       - Tham số cấu hình: CONFIG_OPTION_52 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_52') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [053] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 53
#       - Tham số cấu hình: CONFIG_OPTION_53 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_53') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [054] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 54
#       - Tham số cấu hình: CONFIG_OPTION_54 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_54') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [055] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 55
#       - Tham số cấu hình: CONFIG_OPTION_55 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_55') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [056] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 56
#       - Tham số cấu hình: CONFIG_OPTION_56 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_56') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [057] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 57
#       - Tham số cấu hình: CONFIG_OPTION_57 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_57') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [058] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 58
#       - Tham số cấu hình: CONFIG_OPTION_58 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_58') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [059] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 59
#       - Tham số cấu hình: CONFIG_OPTION_59 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_59') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [060] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 60
#       - Tham số cấu hình: CONFIG_OPTION_60 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_60') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [061] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 61
#       - Tham số cấu hình: CONFIG_OPTION_61 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_61') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [062] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 62
#       - Tham số cấu hình: CONFIG_OPTION_62 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_62') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [063] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 63
#       - Tham số cấu hình: CONFIG_OPTION_63 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_63') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [064] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 64
#       - Tham số cấu hình: CONFIG_OPTION_64 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_64') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [065] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 65
#       - Tham số cấu hình: CONFIG_OPTION_65 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_65') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [066] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 66
#       - Tham số cấu hình: CONFIG_OPTION_66 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_66') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [067] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 67
#       - Tham số cấu hình: CONFIG_OPTION_67 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_67') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [068] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 68
#       - Tham số cấu hình: CONFIG_OPTION_68 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_68') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [069] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 69
#       - Tham số cấu hình: CONFIG_OPTION_69 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_69') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [070] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 70
#       - Tham số cấu hình: CONFIG_OPTION_70 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_70') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [071] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 71
#       - Tham số cấu hình: CONFIG_OPTION_71 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_71') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [072] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 72
#       - Tham số cấu hình: CONFIG_OPTION_72 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_72') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [073] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 73
#       - Tham số cấu hình: CONFIG_OPTION_73 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_73') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [074] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 74
#       - Tham số cấu hình: CONFIG_OPTION_74 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_74') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [075] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 75
#       - Tham số cấu hình: CONFIG_OPTION_75 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_75') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [076] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 76
#       - Tham số cấu hình: CONFIG_OPTION_76 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_76') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [077] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 77
#       - Tham số cấu hình: CONFIG_OPTION_77 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_77') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [078] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 78
#       - Tham số cấu hình: CONFIG_OPTION_78 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_78') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [079] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 79
#       - Tham số cấu hình: CONFIG_OPTION_79 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_79') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [080] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 80
#       - Tham số cấu hình: CONFIG_OPTION_80 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_80') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [081] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 81
#       - Tham số cấu hình: CONFIG_OPTION_81 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_81') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [082] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 82
#       - Tham số cấu hình: CONFIG_OPTION_82 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_82') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [083] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 83
#       - Tham số cấu hình: CONFIG_OPTION_83 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_83') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [084] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 84
#       - Tham số cấu hình: CONFIG_OPTION_84 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_84') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [085] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 85
#       - Tham số cấu hình: CONFIG_OPTION_85 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_85') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [086] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 86
#       - Tham số cấu hình: CONFIG_OPTION_86 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_86') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [087] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 87
#       - Tham số cấu hình: CONFIG_OPTION_87 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_87') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [088] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 88
#       - Tham số cấu hình: CONFIG_OPTION_88 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_88') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [089] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 89
#       - Tham số cấu hình: CONFIG_OPTION_89 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_89') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [090] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 90
#       - Tham số cấu hình: CONFIG_OPTION_90 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_90') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [091] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 91
#       - Tham số cấu hình: CONFIG_OPTION_91 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_91') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [092] Xử lý ngoại lệ, trả về mã lỗi chuẩn RESTful và thông báo tiếng Việt có dấu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 92
#       - Tham số cấu hình: CONFIG_OPTION_92 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_92') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [093] Phân quyền truy cập theo cơ chế RBAC (Giám đốc, Trưởng nhóm, Nhân viên) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 93
#       - Tham số cấu hình: CONFIG_OPTION_93 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_93') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [094] Ghi nhận nhật ký kiểm toán (Audit Trail) cho các thao tác sửa đổi dữ liệu - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 94
#       - Tham số cấu hình: CONFIG_OPTION_94 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_94') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [095] Định nghĩa các kịch bản kiểm thử biên (Edge Cases) và dữ liệu kiểm thử thực tế - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 95
#       - Tham số cấu hình: CONFIG_OPTION_95 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_95') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [096] Tối ưu hóa thời gian phản hồi API và khả năng mở rộng dịch vụ - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 96
#       - Tham số cấu hình: CONFIG_OPTION_96 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_96') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [097] Khởi tạo cấu trúc dữ liệu và kiểm tra ràng buộc toàn vẹn - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 97
#       - Tham số cấu hình: CONFIG_OPTION_97 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_97') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [098] Thiết lập các trường bắt buộc và chỉ mục tìm kiếm tối ưu hiệu năng - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 98
#       - Tham số cấu hình: CONFIG_OPTION_98 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_98') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
# [099] Kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation & Sanitation) - Hạng mục triển khai SCRUM-80 Bảng theo dõi UTM campaign bước 99
#       - Tham số cấu hình: CONFIG_OPTION_99 = True, TIMEOUT_SEC = 30
#       - Quy tắc kiểm tra: if request_data.get('field_99') is None: raise ValidationError
#       - Phân tích hiệu năng: Thời gian xử lý truy vấn ước tính < 50ms
