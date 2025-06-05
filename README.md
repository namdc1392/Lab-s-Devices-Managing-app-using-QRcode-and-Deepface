# Hệ Thống Quản Lý Thiết Bị

## Giới thiệu chung về sản phẩm
Hệ thống Quản lý Thiết bị là một ứng dụng desktop được phát triển để quản lý và theo dõi các thiết bị trong tổ chức. Hệ thống cho phép người dùng thực hiện các thao tác như mượn/trả thiết bị, theo dõi lịch sử sử dụng, quản lý bảo trì và tạo báo cáo một cách hiệu quả.

## Sơ đồ hệ thống
```
┌─────────────────────────────────────────────────────────────┐
│                     Giao diện người dùng                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Xử lý nghiệp vụ                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Quản lý     │  │ Quản lý     │  │ Quản lý            │  │
│  │ thiết bị    │  │ mượn/trả    │  │ bảo trì            │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Lưu trữ dữ liệu                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Thông tin   │  │ Lịch sử     │  │ Báo cáo            │  │
│  │ thiết bị    │  │ mượn/trả    │  │ thống kê           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Mô tả các thành phần:
1. **Giao diện người dùng**
   - Cung cấp giao diện tương tác cho người dùng
   - Hiển thị thông tin và nhận lệnh từ người dùng

2. **Xử lý nghiệp vụ**
   - Quản lý thiết bị: Thêm, sửa, xóa, tìm kiếm thiết bị
   - Quản lý mượn/trả: Xử lý các yêu cầu mượn và trả thiết bị
   - Quản lý bảo trì: Theo dõi và lên lịch bảo trì

3. **Lưu trữ dữ liệu**
   - Lưu trữ thông tin thiết bị
   - Lưu trữ lịch sử mượn/trả
   - Lưu trữ báo cáo và thống kê

## Sơ đồ hệ thống và chức năng

### Các chức năng chính:
1. **Quản lý thiết bị**
   - Thêm thiết bị mới
   - Xem danh sách thiết bị
   - Cập nhật thông tin thiết bị
   - Xóa thiết bị

2. **Quản lý mượn/trả**
   - Đăng ký mượn thiết bị
   - Xác nhận trả thiết bị
   - Theo dõi lịch sử mượn/trả

3. **Quản lý bảo trì**
   - Lên lịch bảo trì
   - Theo dõi trạng thái bảo trì
   - Xem lịch sử bảo trì

4. **Báo cáo và thống kê**
   - Tạo báo cáo tổng hợp
   - Thống kê sử dụng thiết bị
   - Xuất báo cáo

5. **Quét mã QR**
   - Quét mã QR thiết bị
   - Sinh mã QR mới
   - Xem lịch sử quét mã

## Công nghệ và kỹ thuật

### Ngôn ngữ lập trình
- Python 3.x

### Thư viện chính
- `tkinter` và `ttkbootstrap`: Xây dựng giao diện người dùng
- `PIL` (Python Imaging Library): Xử lý hình ảnh
- `qrcode`: Tạo và đọc mã QR
- `opencv-python`: Xử lý hình ảnh và quét mã QR
- `pandas`: Xử lý dữ liệu và tạo báo cáo
- `json`: Lưu trữ dữ liệu

### Cấu trúc dữ liệu
- Sử dụng JSON để lưu trữ thông tin thiết bị
- Quản lý dữ liệu theo cấu trúc phân cấp

## Giao diện người dùng

### Trang chủ
![Trang chủ](app_images/trang_chủ.jpg)

### Quản lý thiết bị
![Thêm thiết bị mới](app_images/thêm_thiết_bị_mới.jpg)

### Quản lý mượn/trả
![Mượn thiết bị](app_images/mượn_thiết_bị.jpg)
![Trả thiết bị](app_images/trả_thiết_bị.jpg)

### Báo cáo và thống kê
![Tạo báo cáo](app_images/tạo_báo_cáo.jpg)

### Quét mã QR
![Giao diện quét mã](app_images/giao_diện_sau_khi_bấm_nút_quét_và_sinh_mã.jpg)
![Kết quả quét mã](app_images/sau_khi_quét_mã.jpg)

## Cài đặt và sử dụng

### Yêu cầu hệ thống
- Python 3.x
- Webcam (cho chức năng quét mã QR)
- Các thư viện Python được liệt kê trong requirements.txt

### Cài đặt
1. Clone repository
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Chạy ứng dụng:
   ```bash
   python main.py
   ```
