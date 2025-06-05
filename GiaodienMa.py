import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import cv2
from pyzbar import pyzbar
import json
from datetime import datetime, timedelta
import os
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import shutil
from deepface import DeepFace

# Đường dẫn tệp và thư mục
DATA_FILE = "danh_sach_vat_dung.json"
HISTORY_FILE = "lich_su_quet.json"
IMAGE_DIR = "device_images"
FACE_IMAGE_DIR = "face_images"

# Tạo thư mục nếu chưa tồn tại
for directory in [IMAGE_DIR, FACE_IMAGE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Hàm chụp ảnh từ camera
def capture_face_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(FACE_IMAGE_DIR, f"face_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        cap.release()
        return image_path
    cap.release()
    return None

# Hàm so sánh khuôn mặt
def verify_face(image_path1, image_path2):
    try:
        result = DeepFace.verify(image_path1, image_path2, model_name="Facenet", distance_metric="euclidean_l2")
        return result["verified"]
    except Exception as e:
        print(f"Lỗi khi so sánh khuôn mặt: {e}")
        return False

class LabManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Vật Dụng Phòng Lab")
        self.root.geometry("1200x800")
        self.root.resizable(False, False)
        self.root.configure(bg="#FFFFFF")

        # Tạo frame chính
        self.main_frame = tk.Frame(root, bg="#FFFFFF")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Tiêu đề
        header_frame = tk.Frame(self.main_frame, bg="#003087")
        header_frame.pack(fill=tk.X)
        title_label = tk.Label(header_frame, text="🧪 Quản Lý Vật Dụng Phòng Lab", 
                             font=("Arial", 16, "bold"), bg="#003087", fg="#FFFFFF")
        title_label.pack(pady=10)

        # Frame cho các nút
        button_frame = tk.Frame(self.main_frame, bg="#FFFFFF")
        button_frame.pack(pady=10)

        # Định nghĩa style cho nút
        button_style = {
            "font": ("Arial", 11, "bold"),
            "relief": "flat",
            "padx": 10,
            "pady": 6,
            "fg": "white"
        }

        # Các nút chức năng
        buttons = [
            ("Quét mã", self.scan_code, "#003087"),
            ("Lịch sử quét", self.show_history, "#003087"),
            ("Mượn thiết bị", self.borrow_device, "#003087"),
            ("Trả thiết bị", self.return_device, "#003087"),
            ("Danh sách bảo trì", self.show_maintenance_list, "#003087"),
            ("Lịch sử mượn", self.show_borrow_history, "#003087"),
            ("Gửi Telegram", self.send_telegram, "#FFC107"),
            ("Thêm thiết bị mới", self.add_new_device, "#FFC107")
        ]

        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, command=command, bg=color, **button_style)
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg="#004D99" if c == "#003087" else "#FF8F00"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

        # Frame cho thông tin thiết bị và ảnh
        device_info_frame = tk.Frame(self.main_frame, bg="#FFFFFF", bd=2, relief="groove")
        device_info_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Frame bên trái cho thông tin thiết bị
        left_frame = tk.Frame(device_info_frame, bg="#FFFFFF")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        # Label thông tin thiết bị
        info_label = tk.Label(left_frame, text="Thông tin thiết bị:", 
                            font=("Arial", 12, "bold"), bg="#FFFFFF", fg="#2c3e50")
        info_label.pack(pady=5)

        # Text widget hiển thị thông tin
        self.info_text = tk.Text(left_frame, height=8, width=50, 
                               font=("Courier", 10), bg="#F0F8FF")
        self.info_text.pack(pady=5)

        # Thêm frame cho danh sách người mượn
        borrowers_label = tk.Label(left_frame, text="Danh sách người mượn:", font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#2c3e50")
        borrowers_label.pack(pady=(10, 0))
        
        # Frame cho Treeview và nút trả
        borrowers_frame = tk.Frame(left_frame, bg="#FFFFFF")
        borrowers_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Tạo Treeview
        self.borrowers_tree = ttk.Treeview(borrowers_frame, 
                                          columns=("Người mượn", "Số điện thoại", "Địa chỉ", "Ngày mượn", "Ngày trả", "Trạng thái", "Trả thiết bị"), 
                                          show="headings", 
                                          height=4)
        
        # Cấu hình các cột
        for col in ("Người mượn", "Số điện thoại", "Địa chỉ", "Ngày mượn", "Ngày trả", "Trạng thái", "Trả thiết bị"):
            self.borrowers_tree.heading(col, text=col)
            if col == "Địa chỉ":
                self.borrowers_tree.column(col, width=120)
            elif col == "Trả thiết bị":
                self.borrowers_tree.column(col, width=80)
            else:
                self.borrowers_tree.column(col, width=90)
        
        # Thêm thanh cuộn
        scrollbar = ttk.Scrollbar(borrowers_frame, orient="vertical", command=self.borrowers_tree.yview)
        self.borrowers_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.borrowers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click event cho Treeview
        self.borrowers_tree.bind('<ButtonRelease-1>', self.on_tree_click)

        # Frame bên phải cho ảnh
        right_frame = tk.Frame(device_info_frame, bg="#FFFFFF")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20)

        # Frame chứa ảnh
        image_container = tk.Frame(right_frame, bg="#F0F8FF", width=300, height=150)
        image_container.pack_propagate(False)
        image_container.pack(pady=0)

        # Label hiển thị ảnh thiết bị
        self.image_label = tk.Label(image_container, bg="#F0F8FF")
        self.image_label.pack(expand=True, fill=tk.BOTH)

        # Label thông báo ảnh
        self.image_info = tk.Label(right_frame, text="Chưa có ảnh", 
                                 font=("Arial", 10), bg="#FFFFFF", fg="#666666")
        self.image_info.pack(pady=0)

        # Biến lưu mã thiết bị hiện tại
        self.current_device_code = None
        self.return_popup = None  # Biến kiểm soát popup trả thiết bị, chỉ cho phép 1 popup

    def scan_code(self):
        cap = cv2.VideoCapture(0)
        found_code = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                try:
                    barcode_data = barcode.data.decode("utf-8")
                except:
                    try:
                        barcode_data = barcode.data.decode("latin-1")
                    except:
                        barcode_data = str(barcode.data)

                found_code = None
                try:
                    import re
                    numbers = re.findall(r'\d+', barcode_data)
                    if numbers:
                        found_code = numbers[0]
                except:
                    pass

                if found_code:
                    device_info = self.find_device_info(found_code)
                    if device_info:
                        cv2.rectangle(frame, (barcode.rect.left, barcode.rect.top),
                                    (barcode.rect.left + barcode.rect.width, 
                                     barcode.rect.top + barcode.rect.height),
                                    (0, 255, 0), 2)
                        cv2.putText(frame, f"Mã: {found_code}", 
                                  (barcode.rect.left, barcode.rect.top - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        break
                    else:
                        cv2.rectangle(frame, (barcode.rect.left, barcode.rect.top),
                                    (barcode.rect.left + barcode.rect.width, 
                                     barcode.rect.top + barcode.rect.height),
                                    (0, 0, 255), 2)
                        cv2.putText(frame, "Mã không hợp lệ", 
                                  (barcode.rect.left, barcode.rect.top - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            cv2.imshow("Quet ma QR - Nhan ESC de thoat", frame)

            key = cv2.waitKey(1)
            if key == 27 or found_code:
                break

        cap.release()
        cv2.destroyAllWindows()

        if found_code:
            self.show_device_info(found_code)
            self.save_scan_history(found_code)
        else:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "⚠️ Không nhận diện được mã\n")

    def show_device_info(self, ma_vat_dung):
        self.current_device_code = ma_vat_dung
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"Mã: {ma_vat_dung}\n")

        info = self.find_device_info(ma_vat_dung)
        if info:
            self.info_text.insert(tk.END, f"Tên thiết bị: {info.get('ten', '')}\n")
            self.info_text.insert(tk.END, f"Trạng thái: {info.get('trang_thai', '')}\n")
            self.info_text.insert(tk.END, f"Loại: {info.get('loai', '')}\n")
            so_luong_tong = info.get('so_luong_tong', 0)
            ban_ghi_muon = info.get('ban_ghi_muon', [])
            so_luong_da_muon = sum(record.get('so_luong', 0) for record in ban_ghi_muon if not record.get('da_tra', False))
            so_luong_con_lai = so_luong_tong - so_luong_da_muon
            
            self.info_text.insert(tk.END, f"Số lượng còn lại: {so_luong_con_lai}\n")
            self.info_text.insert(tk.END, f"Tổng số lượng: {so_luong_tong}\n")

            hinh_anh = info.get('hinh_anh', '')
            if hinh_anh and hinh_anh.strip():
                try:
                    image_paths = [
                        hinh_anh,
                        os.path.join(IMAGE_DIR, hinh_anh)
                    ]
                    
                    image_path = None
                    for path in image_paths:
                        if os.path.exists(path):
                            image_path = path
                            break
                    
                    if image_path:
                        image = Image.open(image_path)
                        container_width = 400
                        container_height = 200
                        original_width, original_height = image.size
                        width_ratio = container_width / original_width
                        height_ratio = container_height / original_height
                        ratio = min(width_ratio, height_ratio)
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        self.image_label.configure(image=photo)
                        self.image_label.image = photo
                        self.image_info.configure(text="")
                    else:
                        self.image_label.configure(image='')
                        self.image_label.image = None
                        self.image_info.configure(text="Không tìm thấy ảnh")
                except Exception as e:
                    print(f"Lỗi hiển thị ảnh: {e}")
                    self.image_label.configure(image='')
                    self.image_label.image = None
                    self.image_info.configure(text="Lỗi hiển thị ảnh")
            else:
                self.image_label.configure(image='')
                self.image_label.image = None
                self.image_info.configure(text="Thiết bị chưa có ảnh")
        else:
            self.info_text.insert(tk.END, "⚠️ Không tìm thấy thông tin thiết bị\n")
            self.image_label.configure(image='')
            self.image_label.image = None
            self.image_info.configure(text="Không tìm thấy thiết bị")
            
        self.refresh_borrowers_list_inline()

    def refresh_borrowers_list_inline(self):
        for item in self.borrowers_tree.get_children():
            self.borrowers_tree.delete(item)
            
        if not self.current_device_code:
            return
            
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            for item in data:
                if isinstance(item, dict) and str(item.get("id")) == str(self.current_device_code):
                    if item.get("ban_ghi_muon"):
                        for record in item["ban_ghi_muon"]:
                            trang_thai = "Đang mượn" if not record.get("da_tra") else "Đã trả"
                            tra_thiet_bi = "🔄 Trả" if not record.get("da_tra") else ""
                            self.borrowers_tree.insert("", "end", values=(
                                record["nguoi_muon"],
                                record["so_dien_thoai"],
                                record["dia_chi"],
                                record["ngay_muon"],
                                record.get("ngay_tra", ""),
                                trang_thai,
                                tra_thiet_bi
                            ))
                    break
        except FileNotFoundError:
            messagebox.showerror("Lỗi", "Không tìm thấy file dữ liệu!")
        except json.JSONDecodeError:
            messagebox.showerror("Lỗi", "File dữ liệu không hợp lệ!")

    def borrow_device(self):
        if not self.current_device_code:
            messagebox.showwarning("Cảnh báo", "Vui lòng quét mã thiết bị trước khi mượn")
            return

        device_info = self.find_device_info(self.current_device_code)
        if not device_info:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin thiết bị")
            return

        so_luong_da_muon = sum(record["so_luong"] for record in device_info["ban_ghi_muon"] if not record.get("da_tra", False))
        so_luong_con_lai = device_info["so_luong_tong"] - so_luong_da_muon
        
        if so_luong_con_lai <= 0:
            messagebox.showwarning("Cảnh báo", "Thiết bị không còn sẵn để mượn")
            return

        borrow_window = tk.Toplevel(self.root)
        borrow_window.title("Thông tin mượn thiết bị")
        borrow_window.geometry("650x550")
        borrow_window.resizable(False, False)
        borrow_window.configure(bg="#FFFFFF")
        borrow_window.update_idletasks()
        width = borrow_window.winfo_width()
        height = borrow_window.winfo_height()
        x = (borrow_window.winfo_screenwidth() // 2) - (width // 2)
        y = (borrow_window.winfo_screenheight() // 2) - (height // 2)
        borrow_window.geometry(f'{width}x{height}+{x}+{y}')
        borrow_window.transient(self.root)
        borrow_window.grab_set()
        borrow_window.focus_set()

        # Tiêu đề
        header_frame = tk.Frame(borrow_window, bg="#003087")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Thông tin mượn thiết bị", font=("Arial", 16, "bold"), bg="#003087", fg="#FFFFFF").pack(pady=10)

        # Nội dung chia 2 cột
        content_frame = tk.Frame(borrow_window, bg="#FFFFFF")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1, minsize=180)
        content_frame.grid_columnconfigure(1, weight=2, minsize=300)

        # Bên trái: Quét khuôn mặt
        left_frame = tk.Frame(content_frame, bg="#FFFFFF")
        left_frame.grid(row=0, column=0, sticky="n", padx=(0, 0))
        face_img_label = tk.Label(left_frame, bg="#F0F0F0", width=120, height=7)
        face_img_label.pack(pady=(0,10))
        face_image_path = [None]
        def quet_khuon_mat():
            from face_recognition import capture_face_image
            from PIL import Image, ImageTk
            img_path = capture_face_image()
            if img_path:
                face_image_path[0] = img_path
                img = Image.open(img_path)
                img = img.resize((120, 120))
                img_tk = ImageTk.PhotoImage(img)
                face_img_label.config(image=img_tk, width=120, height=120)
                face_img_label.image = img_tk
            else:
                messagebox.showerror("Lỗi", "Không thể chụp ảnh khuôn mặt!")
        btn_quet_mat = tk.Button(
            left_frame,
            text="Quét khuôn mặt",
            command=quet_khuon_mat,
            bg="#003087",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            width=12
        )
        btn_quet_mat.pack(pady=(2, 0))

        # Bên phải: Trường nhập thông tin
        right_frame = tk.Frame(content_frame, bg="#FFFFFF")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(20,0))
        right_frame.grid_columnconfigure(1, weight=1)
        tk.Label(right_frame, text="Họ tên:", bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(right_frame, width=30)
        name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        tk.Label(right_frame, text="Số điện thoại:", bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=5)
        phone_entry = tk.Entry(right_frame, width=30)
        phone_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        tk.Label(right_frame, text="Địa chỉ:", bg="#FFFFFF").grid(row=2, column=0, sticky="w", pady=5)
        address_entry = tk.Entry(right_frame, width=30)
        address_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        tk.Label(right_frame, text="Ngày mượn:", bg="#FFFFFF").grid(row=3, column=0, sticky="w", pady=5)
        borrow_date_entry = DateEntry(right_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        borrow_date_entry.set_date(datetime.now())
        borrow_date_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        tk.Label(right_frame, text="Ngày trả:", bg="#FFFFFF").grid(row=4, column=0, sticky="w", pady=5)
        return_date_entry = DateEntry(right_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        return_date_entry.set_date(datetime.now() + timedelta(days=7))
        return_date_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)

        # Nút xác nhận mượn ở dưới cùng
        def confirm_borrow():
            try:
                name = name_entry.get().strip()
                phone = phone_entry.get().strip()
                address = address_entry.get().strip()
                borrow_date = borrow_date_entry.get_date().strftime("%Y-%m-%d")
                return_date = return_date_entry.get_date().strftime("%Y-%m-%d")
                if not all([name, phone, address]):
                    messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin")
                    return
                if not face_image_path[0]:
                    messagebox.showwarning("Cảnh báo", "Vui lòng quét khuôn mặt trước khi xác nhận mượn!")
                    return
                if not os.path.exists(DATA_FILE):
                    messagebox.showerror("Lỗi", "Không tìm thấy file dữ liệu")
                    return
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                device_found = False
                for item in data:
                    if isinstance(item, dict) and str(item.get("id")) == str(self.current_device_code):
                        if "ban_ghi_muon" not in item:
                            item["ban_ghi_muon"] = []
                        item["ban_ghi_muon"].append({
                            "nguoi_muon": name,
                            "so_luong": 1,
                            "so_dien_thoai": phone,
                            "dia_chi": address,
                            "ngay_muon": borrow_date,
                            "ngay_tra": return_date,
                            "da_tra": False,
                            "anh_nguoi_muon": face_image_path[0]
                        })
                        device_found = True
                        break
                if not device_found:
                    messagebox.showerror("Lỗi", "Không tìm thấy thông tin thiết bị trong dữ liệu")
                    return
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Thành công", "Đã ghi nhận thông tin mượn thiết bị")
                borrow_window.destroy()
                self.show_device_info(self.current_device_code)
            except Exception as e:
                messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

        confirm_button = tk.Button(borrow_window, text="Xác nhận mượn", command=confirm_borrow, bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat")
        confirm_button.pack(side=tk.BOTTOM, pady=10, fill=tk.X)
        confirm_button.bind("<Enter>", lambda e: confirm_button.config(bg="#004D99"))
        confirm_button.bind("<Leave>", lambda e: confirm_button.config(bg="#003087"))
        name_entry.focus_set()

    def return_device(self):
        return_window = tk.Toplevel(self.root)
        return_window.title("Trả thiết bị")
        return_window.geometry("650x550")
        return_window.resizable(False, False)
        return_window.configure(bg="#FFFFFF")
        return_window.update_idletasks()
        width = return_window.winfo_width()
        height = return_window.winfo_height()
        x = (return_window.winfo_screenwidth() // 2) - (width // 2)
        y = (return_window.winfo_screenheight() // 2) - (height // 2)
        return_window.geometry(f'{width}x{height}+{x}+{y}')
        return_window.transient(self.root)
        return_window.grab_set()
        return_window.focus_set()

        # Tiêu đề
        header_frame = tk.Frame(return_window, bg="#003087")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="↩️ Trả thiết bị", 
                font=("Arial", 14, "bold"), bg="#003087", fg="#FFFFFF").pack(pady=10)

        # Nội dung chia 2 cột
        content_frame = tk.Frame(return_window, bg="#FFFFFF")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1, minsize=180)
        content_frame.grid_columnconfigure(1, weight=2, minsize=300)

        # Bên trái: Quét khuôn mặt
        left_frame = tk.Frame(content_frame, bg="#FFFFFF")
        left_frame.grid(row=0, column=0, sticky="n", padx=(0, 0))
        face_img_label = tk.Label(left_frame, bg="#F0F0F0", width=120, height=7)
        face_img_label.pack(pady=(0,10))
        face_image_path = [None]
        def quet_khuon_mat():
            from face_recognition import capture_face_image
            from PIL import Image, ImageTk
            img_path = capture_face_image()
            if img_path:
                face_image_path[0] = img_path
                img = Image.open(img_path)
                img = img.resize((120, 120))
                img_tk = ImageTk.PhotoImage(img)
                face_img_label.config(image=img_tk, width=120, height=120)
                face_img_label.image = img_tk
            else:
                messagebox.showerror("Lỗi", "Không thể chụp ảnh khuôn mặt!")
        btn_quet_mat = tk.Button(
            left_frame,
            text="Quét khuôn mặt",
            command=quet_khuon_mat,
            bg="#003087",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            width=12
        )
        btn_quet_mat.pack(pady=(2, 0))

        # Bên phải: Chọn thiết bị và người mượn
        right_frame = tk.Frame(content_frame, bg="#FFFFFF")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(20,0))
        right_frame.grid_columnconfigure(1, weight=1)

        tk.Label(right_frame, text="Thiết bị:", bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=5)
        device_var = tk.StringVar()
        device_combo = ttk.Combobox(right_frame, textvariable=device_var, state="readonly", width=30)
        device_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        borrower_frame = tk.Frame(right_frame, bg="#FFFFFF")
        borrower_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        borrower_frame.grid_columnconfigure(0, weight=1)

        columns = ("Người mượn", "Số điện thoại", "Ngày mượn", "Ngày trả")
        borrower_tree = ttk.Treeview(borrower_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            borrower_tree.heading(col, text=col)
            borrower_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(borrower_frame, orient="vertical", command=borrower_tree.yview)
        borrower_tree.configure(yscrollcommand=scrollbar.set)
        
        borrower_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        status_frame = tk.Frame(right_frame, bg="#FFFFFF")
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        tk.Label(status_frame, text="Tình trạng:", bg="#FFFFFF").pack(side=tk.LEFT, padx=5)
        status_var = tk.StringVar(value="good")
        ttk.Radiobutton(status_frame, text="Còn nguyên", variable=status_var, 
                       value="good", bg="#FFFFFF").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(status_frame, text="Hỏng", variable=status_var, 
                       value="broken", bg="#FFFFFF").pack(side=tk.LEFT, padx=10)

        def load_devices():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                borrowed_devices = []
                for item in data:
                    if isinstance(item, dict) and item.get("ban_ghi_muon"):
                        has_active_borrowers = any(not record.get("da_tra") for record in item["ban_ghi_muon"])
                        if has_active_borrowers:
                            borrowed_devices.append(f"{item['id']} - {item['ten']}")
                device_combo['values'] = borrowed_devices
                if borrowed_devices:
                    device_combo.set(borrowed_devices[0])
            except Exception as e:
                messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

        def update_borrowers_list(*args):
            for item in borrower_tree.get_children():
                borrower_tree.delete(item)

            try:
                selected = device_combo.get()
                if selected:
                    device_id = selected.split(" - ")[0]
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    for item in data:
                        if isinstance(item, dict) and str(item.get("id")) == device_id:
                            for record in item.get("ban_ghi_muon", []):
                                if not record.get("da_tra"):
                                    borrower_tree.insert("", "end", values=(
                                        record["nguoi_muon"],
                                        record["so_dien_thoai"],
                                        record["ngay_muon"],
                                        record["ngay_tra"]
                                    ))
            except Exception as e:
                messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

        def process_return_device():
            try:
                if not face_image_path[0]:
                    messagebox.showwarning("Cảnh báo", "Vui lòng quét khuôn mặt trước khi xác nhận trả!")
                    return

                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                device_found = False
                for item in data:
                    if isinstance(item, dict) and str(item.get("id")) == str(self.current_device_code):
                        values = borrower_tree.item(borrower_tree.selection()[0])["values"]
                        nguoi_muon = values[0]
                        for record in item.get("ban_ghi_muon", []):
                            if record["nguoi_muon"] == nguoi_muon and not record.get("da_tra"):
                                borrower_image = record.get("anh_nguoi_muon")
                                if borrower_image and verify_face(borrower_image, face_image_path[0]):
                                    # Khuôn mặt khớp
                                    record["da_tra"] = True
                                    record["ngay_tra_thuc_te"] = datetime.now().strftime("%Y-%m-%d")
                                    record["anh_nguoi_tra"] = face_image_path[0]
                                    if status_var.get() == "broken":
                                        item["trang_thai"] = "Đang bảo trì"
                                    self.save_borrow_history(item, record)
                                    item["ban_ghi_muon"].remove(record)
                                    messagebox.showinfo("Thành công", f"Người trả là {nguoi_muon}. Đã cập nhật trạng thái trả.")
                                else:
                                    # Khuôn mặt không khớp
                                    returner_info_window = tk.Toplevel(self.root)
                                    returner_info_window.title("Thông tin người trả")
                                    returner_info_window.geometry("400x300")
                                    returner_info_window.resizable(False, False)
                                    returner_info_window.configure(bg="#FFFFFF")

                                    returner_frame = tk.Frame(returner_info_window, bg="#FFFFFF")
                                    returner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

                                    tk.Label(returner_frame, text="Người trả không phải người mượn ban đầu", 
                                            font=("Arial", 12, "bold"), bg="#FFFFFF").pack(pady=10)

                                    tk.Label(returner_frame, text="Tên người trả:", bg="#FFFFFF").pack(anchor="w")
                                    returner_name_entry = tk.Entry(returner_frame, width=30)
                                    returner_name_entry.pack(pady=5)

                                    tk.Label(returner_frame, text="Số điện thoại:", bg="#FFFFFF").pack(anchor="w")
                                    returner_phone_entry = tk.Entry(returner_frame, width=30)
                                    returner_phone_entry.pack(pady=5)

                                    tk.Label(returner_frame, text="Địa chỉ:", bg="#FFFFFF").pack(anchor="w")
                                    returner_address_entry = tk.Entry(returner_frame, width=30)
                                    returner_address_entry.pack(pady=5)

                                    def save_returner_info():
                                        returner_name = returner_name_entry.get().strip()
                                        returner_phone = returner_phone_entry.get().strip()
                                        returner_address = returner_address_entry.get().strip()

                                        if not all([returner_name, returner_phone, returner_address]):
                                            messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin")
                                            return

                                        record["da_tra"] = True
                                        record["ngay_tra_thuc_te"] = datetime.now().strftime("%Y-%m-%d")
                                        record["anh_nguoi_tra"] = face_image_path[0]
                                        record["nguoi_tra"] = returner_name
                                        record["so_dien_thoai_tra"] = returner_phone
                                        record["dia_chi_tra"] = returner_address
                                        if status_var.get() == "broken":
                                            item["trang_thai"] = "Đang bảo trì"

                                        with open(DATA_FILE, "w", encoding="utf-8") as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)

                                        messagebox.showinfo("Thành công", "Đã lưu thông tin người trả mới")
                                        returner_info_window.destroy()
                                        return_window.destroy()
                                        self.refresh_borrowers_list_inline()
                                        self.show_device_info(self.current_device_code)

                                    confirm_returner_btn = tk.Button(returner_frame, text="Lưu thông tin", 
                                                                   command=save_returner_info,
                                                                   bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat")
                                    confirm_returner_btn.pack(pady=10)
                                    returner_info_window.transient(self.root)
                                    returner_info_window.grab_set()
                                    return

                                device_found = True
                                break
                        break

                if device_found:
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    return_window.destroy()
                    self.refresh_borrowers_list_inline()
                    self.show_device_info(self.current_device_code)
                else:
                    messagebox.showerror("Lỗi", "Không tìm thấy bản ghi mượn phù hợp")

            except Exception as e:
                messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

        confirm_button = tk.Button(return_window, text="Xác nhận trả thiết bị", 
                                 command=process_return_device,
                                 bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat")
        confirm_button.pack(pady=10)
        confirm_button.bind("<Enter>", lambda e: confirm_button.config(bg="#004D99"))
        confirm_button.bind("<Leave>", lambda e: confirm_button.config(bg="#003087"))

        device_combo.bind('<<ComboboxSelected>>', update_borrowers_list)

        load_devices()
        if device_combo.get():
            update_borrowers_list()

    def on_tree_click(self, event):
        region = self.borrowers_tree.identify_region(event.x, event.y)
        if region == "cell":
            item_id = self.borrowers_tree.identify_row(event.y)
            column = self.borrowers_tree.identify_column(event.x)
            column_name = self.borrowers_tree.heading(column)["text"]
            
            if column_name == "Trả thiết bị":
                values = self.borrowers_tree.item(item_id)["values"]
                nguoi_muon = values[0]
                
                with open(DATA_FILE, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                for item in data:
                    if isinstance(item, dict) and item.get("ban_ghi_muon"):
                        for record in item["ban_ghi_muon"]:
                            if record["nguoi_muon"] == nguoi_muon and not record.get("da_tra"):
                                self.return_device_from_list(item["id"], self.borrowers_tree, item_id)

    def return_device_from_list(self, ma_vat_dung, tree, item_id):
        if self.return_popup is not None and self.return_popup.winfo_exists():
            self.return_popup.lift()
            return
        status_window = tk.Toplevel(self.root)
        self.return_popup = status_window
        status_window.title("Xác nhận trả thiết bị")
        status_window.geometry("500x400")
        status_window.resizable(False, False)
        status_window.configure(bg="#FFFFFF")

        def on_close():
            self.return_popup = None
            status_window.destroy()
        status_window.protocol("WM_DELETE_WINDOW", on_close)

        main_frame = tk.Frame(status_window, bg="#FFFFFF")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header_frame = tk.Frame(main_frame, bg="#003087")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Xác nhận trả thiết bị", 
                font=("Arial", 14, "bold"), bg="#003087", fg="#FFFFFF").pack(pady=10)

        face_frame = tk.Frame(main_frame, bg="#FFFFFF")
        face_frame.pack(fill=tk.X, pady=5)
        face_img_label = tk.Label(face_frame, bg="#F0F0F0", width=120, height=7)
        face_img_label.pack(pady=(0,10))
        face_image_path = [None]
        def quet_khuon_mat():
            from face_recognition import capture_face_image
            from PIL import Image, ImageTk
            img_path = capture_face_image()
            if img_path:
                face_image_path[0] = img_path
                img = Image.open(img_path)
                img = img.resize((120, 120))
                img_tk = ImageTk.PhotoImage(img)
                face_img_label.config(image=img_tk, width=120, height=120)
                face_img_label.image = img_tk
            else:
                messagebox.showerror("Lỗi", "Không thể chụp ảnh khuôn mặt!")
        btn_quet_mat = tk.Button(
            face_frame,
            text="Quét khuôn mặt",
            command=quet_khuon_mat,
            bg="#003087",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            width=12
        )
        btn_quet_mat.pack(pady=(2, 0))

        options_frame = tk.Frame(main_frame, bg="#FFFFFF")
        options_frame.pack(fill=tk.X, pady=10)
        status_var = tk.StringVar(value="good")
        tk.Radiobutton(options_frame, text="Thiết bị còn nguyên", 
                      variable=status_var, value="good",
                      bg="#FFFFFF").pack(anchor="w", pady=5)
        tk.Radiobutton(options_frame, text="Thiết bị bị hỏng", 
                      variable=status_var, value="damaged",
                      bg="#FFFFFF").pack(anchor="w", pady=5)

        def process_return_device():
            try:
                if not face_image_path[0]:
                    messagebox.showwarning("Cảnh báo", "Vui lòng quét khuôn mặt trước khi xác nhận trả!")
                    return

                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                device_found = False
                for item in data:
                    if isinstance(item, dict) and str(item.get("id")) == str(ma_vat_dung):
                        values = tree.item(item_id)["values"]
                        nguoi_muon = values[0]
                        for record in item.get("ban_ghi_muon", []):
                            if record["nguoi_muon"] == nguoi_muon and not record.get("da_tra"):
                                borrower_image = record.get("anh_nguoi_muon")
                                if borrower_image and verify_face(borrower_image, face_image_path[0]):
                                    # Khuôn mặt khớp
                                    record["da_tra"] = True
                                    record["ngay_tra_thuc_te"] = datetime.now().strftime("%Y-%m-%d")
                                    record["anh_nguoi_tra"] = face_image_path[0]
                                    if status_var.get() == "damaged":
                                        item["trang_thai"] = "Đang bảo trì"
                                    self.save_borrow_history(item, record)
                                    item["ban_ghi_muon"].remove(record)
                                    messagebox.showinfo("Thành công", f"Người trả là {nguoi_muon}. Đã cập nhật trạng thái trả.")
                                else:
                                    # Khuôn mặt không khớp
                                    returner_info_window = tk.Toplevel(self.root)
                                    returner_info_window.title("Thông tin người trả")
                                    returner_info_window.geometry("400x300")
                                    returner_info_window.resizable(False, False)
                                    returner_info_window.configure(bg="#FFFFFF")

                                    returner_frame = tk.Frame(returner_info_window, bg="#FFFFFF")
                                    returner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

                                    tk.Label(returner_frame, text="Người trả không phải người mượn ban đầu", 
                                            font=("Arial", 12, "bold"), bg="#FFFFFF").pack(pady=10)

                                    tk.Label(returner_frame, text="Tên người trả:", bg="#FFFFFF").pack(anchor="w")
                                    returner_name_entry = tk.Entry(returner_frame, width=30)
                                    returner_name_entry.pack(pady=5)

                                    tk.Label(returner_frame, text="Số điện thoại:", bg="#FFFFFF").pack(anchor="w")
                                    returner_phone_entry = tk.Entry(returner_frame, width=30)
                                    returner_phone_entry.pack(pady=5)

                                    tk.Label(returner_frame, text="Địa chỉ:", bg="#FFFFFF").pack(anchor="w")
                                    returner_address_entry = tk.Entry(returner_frame, width=30)
                                    returner_address_entry.pack(pady=5)

                                    def save_returner_info():
                                        returner_name = returner_name_entry.get().strip()
                                        returner_phone = returner_phone_entry.get().strip()
                                        returner_address = returner_address_entry.get().strip()

                                        if not all([returner_name, returner_phone, returner_address]):
                                            messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin")
                                            return

                                        record["da_tra"] = True
                                        record["ngay_tra_thuc_te"] = datetime.now().strftime("%Y-%m-%d")
                                        record["anh_nguoi_tra"] = face_image_path[0]
                                        record["nguoi_tra"] = returner_name
                                        record["so_dien_thoai_tra"] = returner_phone
                                        record["dia_chi_tra"] = returner_address
                                        if status_var.get() == "damaged":
                                            item["trang_thai"] = "Đang bảo trì"

                                        with open(DATA_FILE, "w", encoding="utf-8") as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)

                                        messagebox.showinfo("Thành công", "Đã lưu thông tin người trả mới")
                                        returner_info_window.destroy()
                                        status_window.destroy()
                                        self.refresh_borrowers_list_inline()
                                        self.show_device_info(ma_vat_dung)

                                    confirm_returner_btn = tk.Button(returner_frame, text="Lưu thông tin", 
                                                                   command=save_returner_info,
                                                                   bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat")
                                    confirm_returner_btn.pack(pady=10)
                                    returner_info_window.transient(self.root)
                                    returner_info_window.grab_set()
                                    return

                                device_found = True
                                break
                        break

                if device_found:
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    status_window.destroy()
                    self.refresh_borrowers_list_inline()
                    self.show_device_info(ma_vat_dung)
                else:
                    messagebox.showerror("Lỗi", "Không tìm thấy bản ghi mượn phù hợp")

            except Exception as e:
                messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

        confirm_button = tk.Button(status_window, text="Xác nhận", 
                                 command=process_return_device,
                                 bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat")
        confirm_button.pack(pady=20)
        confirm_button.bind("<Enter>", lambda e: confirm_button.config(bg="#004D99"))
        confirm_button.bind("<Leave>", lambda e: confirm_button.config(bg="#003087"))

    def find_device_info(self, ma):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data:
                if isinstance(item, dict) and str(item.get("id", "")) == str(ma):
                    return item
                        
        except FileNotFoundError:
            print(f"Không tìm thấy file {DATA_FILE}")
        except json.JSONDecodeError:
            print(f"File {DATA_FILE} không đúng định dạng JSON")
        except Exception as e:
            print(f"Lỗi đọc file: {e}")
        return None

    def save_scan_history(self, ma_vat_dung):
        try:
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = []

            device_info = self.find_device_info(ma_vat_dung)
            
            new_record = {
                "ma": str(ma_vat_dung),
                "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ten_thiet_bi": device_info.get("ten", "Không tìm thấy"),
                "trang_thai": device_info.get("trang_thai", "Không tìm thấy")
            }
            history.append(new_record)

            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi lưu lịch sử: {e}")

    def show_history(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            history_window = tk.Toplevel(self.root)
            history_window.title("Lịch sử quét mã")
            history_window.geometry("800x600")
            history_window.configure(bg="#FFFFFF")

            header_frame = tk.Frame(history_window, bg="#003087")
            header_frame.pack(fill=tk.X)
            tk.Label(header_frame, text="📋 Lịch sử quét mã", 
                    font=("Arial", 14, "bold"), bg="#003087", fg="#FFFFFF").pack(pady=10)

            tree = ttk.Treeview(history_window, columns=("Thời gian", "Mã", "Tên thiết bị", "Trạng thái"), 
                              show="headings")
            
            tree.heading("Thời gian", text="Thời gian")
            tree.heading("Mã", text="Mã")
            tree.heading("Tên thiết bị", text="Tên thiết bị")
            tree.heading("Trạng thái", text="Trạng thái")

            tree.column("Thời gian", width=150)
            tree.column("Mã", width=100)
            tree.column("Tên thiết bị", width=300)
            tree.column("Trạng thái", width=150)

            for record in reversed(history):
                tree.insert("", "end", values=(
                    record["thoi_gian"],
                    record["ma"],
                    record.get("ten_thiet_bi", "Không tìm thấy"),
                    record.get("trang_thai", "Không tìm thấy")
                ))

            scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        except Exception as e:
            messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

    def send_telegram(self):
        self.info_text.insert(tk.END, "→ Đang gửi thông tin lên Telegram...\n")

    def show_maintenance_list(self):
        maintenance_window = tk.Toplevel(self.root)
        maintenance_window.title("Danh sách thiết bị đang bảo trì")
        maintenance_window.geometry("800x500")
        maintenance_window.resizable(False, False)
        maintenance_window.configure(bg="#FFFFFF")

        main_frame = tk.Frame(maintenance_window, bg="#FFFFFF")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header_frame = tk.Frame(main_frame, bg="#003087")
        header_frame.pack(fill=tk.X)
        title_label = tk.Label(header_frame, 
                             text="🔧 Danh sách thiết bị đang bảo trì", 
                             font=("Arial", 16, "bold"), 
                             bg="#003087", 
                             fg="#FFFFFF")
        title_label.pack(pady=10)

        guide_label = tk.Label(main_frame, 
                             text="(Kéo thả chuột để chọn nhiều thiết bị)", 
                             font=("Arial", 10, "italic"), 
                             bg="#FFFFFF", 
                             fg="#666666")
        guide_label.pack(pady=(0, 10))

        tree = ttk.Treeview(main_frame, 
                           columns=("Mã", "Tên thiết bị", "Trạng thái"), 
                           show="headings",
                           selectmode="extended")
        
        tree.heading("Mã", text="Mã")
        tree.heading("Tên thiết bị", text="Tên thiết bị")
        tree.heading("Trạng thái", text="Trạng thái")

        tree.column("Mã", width=100)
        tree.column("Tên thiết bị", width=400)
        tree.column("Trạng thái", width=200)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(main_frame, bg="#FFFFFF")
        button_frame.pack(fill=tk.X, pady=10)

        complete_btn = tk.Button(button_frame, 
                               text="Hoàn thành bảo trì", 
                               command=lambda: self.complete_maintenance(tree),
                               bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat")
        complete_btn.pack(side=tk.LEFT, padx=5)
        complete_btn.bind("<Enter>", lambda e: complete_btn.config(bg="#004D99"))
        complete_btn.bind("<Leave>", lambda e: complete_btn.config(bg="#003087"))

        refresh_btn = tk.Button(button_frame, 
                              text="Làm mới", 
                              command=lambda: self.refresh_maintenance_list(tree),
                              bg="#FFC107", fg="white", font=("Arial", 11, "bold"), relief="flat")
        refresh_btn.pack(side=tk.LEFT, padx=5)
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(bg="#FF8F00"))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(bg="#FFC107"))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_maintenance_list(tree)

    def refresh_maintenance_list(self, tree):
        try:
            for item in tree.get_children():
                tree.delete(item)

            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data:
                if isinstance(item, dict) and item.get("trang_thai") == "Đang bảo trì":
                    tree.insert("", "end", values=(
                        item.get("id", ""),
                        item.get("ten", ""),
                        item.get("trang_thai", "")
                    ))
        except Exception as e:
            messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

    def complete_maintenance(self, tree):
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một thiết bị")
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            updated_count = 0
            for item_id in selected_items:
                device_code = tree.item(item_id)['values'][0]
                for device in data:
                    if isinstance(device, dict) and str(device.get("id")) == str(device_code):
                        if device.get("trang_thai") == "Đang bảo trì":
                            device["trang_thai"] = "Có sẵn"
                            updated_count += 1
                        break

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.refresh_maintenance_list(tree)
            self.refresh_borrowers_list_inline()
            if self.current_device_code:
                self.show_device_info(self.current_device_code)
            messagebox.showinfo("Thành công", f"Đã hoàn thành bảo trì {updated_count} thiết bị")

        except Exception as e:
            messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

    def add_new_device(self):
        input_window = NhapThongTinVatDung(self.root)
        input_window.transient(self.root)
        input_window.grab_set()
        self.root.wait_window(input_window)

    def save_borrow_history(self, device, record):
        try:
            try:
                with open("lich_su_muon.json", "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = []
            entry = {
                "id": device.get("id"),
                "ten_thiet_bi": device.get("ten"),
                "nguoi_muon": record.get("nguoi_muon"),
                "so_dien_thoai": record.get("so_dien_thoai"),
                "dia_chi": record.get("dia_chi"),
                "ngay_muon": record.get("ngay_muon"),
                "ngay_tra_du_kien": record.get("ngay_tra"),
                "ngay_tra_thuc_te": record.get("ngay_tra_thuc_te", ""),
                "trang_thai_tra": "Hỏng" if record.get("trang_thai_tra") == "damaged" else "Còn nguyên",
                "anh_nguoi_muon": record.get("anh_nguoi_muon", ""),
                "anh_nguoi_tra": record.get("anh_nguoi_tra", ""),
                "nguoi_tra": record.get("nguoi_tra", record.get("nguoi_muon")),
                "so_dien_thoai_tra": record.get("so_dien_thoai_tra", record.get("so_dien_thoai")),
                "dia_chi_tra": record.get("dia_chi_tra", record.get("dia_chi"))
            }
            history.append(entry)
            with open("lich_su_muon.json", "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi lưu lịch sử mượn: {e}")

    def show_borrow_history(self):
        try:
            with open("lich_su_muon.json", "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
        window = tk.Toplevel(self.root)
        window.title("Lịch sử mượn thiết bị")
        window.geometry("950x550")
        window.configure(bg="#FFFFFF")
        header_frame = tk.Frame(window, bg="#003087")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="📜 Lịch sử mượn thiết bị", font=("Arial", 14, "bold"), bg="#003087", fg="#FFFFFF").pack(pady=10)
        # --- Thêm ô tìm kiếm ---
        search_frame = tk.Frame(window, bg="#FFFFFF")
        search_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        tk.Label(search_frame, text="🔍 Tìm kiếm:", font=("Arial", 11), bg="#FFFFFF").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=40, font=("Arial", 11))
        search_entry.pack(side=tk.LEFT, padx=8)
        # --- Bảng lịch sử ---
        columns = ("Mã", "Tên thiết bị", "Người mượn", "SĐT mượn", "Địa chỉ mượn", "Ngày mượn", "Ngày trả dự kiến", "Ngày trả thực tế", "Người trả", "SĐT trả", "Địa chỉ trả", "Trạng thái trả")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110 if col!="Tên thiết bị" else 180)
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        # --- Hàm lọc và hiển thị ---
        def update_tree():
            keyword = search_var.get().lower()
            tree.delete(*tree.get_children())
            for record in reversed(history):
                row = [str(record.get(k, "")) for k in ["id", "ten_thiet_bi", "nguoi_muon", "so_dien_thoai", "dia_chi", "ngay_muon", "ngay_tra_du_kien", "ngay_tra_thuc_te", "nguoi_tra", "so_dien_thoai_tra", "dia_chi_tra", "trang_thai_tra"]]
                if not keyword or any(keyword in str(cell).lower() for cell in row):
                    tree.insert("", "end", values=row)
        search_var.trace_add("write", lambda *args: update_tree())
        update_tree()

class NhapThongTinVatDung(tk.Toplevel):
    def __init__(self, master, on_submit=None):
        super().__init__(master)
        self.title("Nhập Thông Tin Vật Dụng")
        self.geometry("600x450")
        self.resizable(False, False)
        self.configure(bg="#FFFFFF")
        
        main_frame = tk.Frame(self, bg="#FFFFFF", padx=10, pady=5)
        main_frame.grid(row=0, column=0, sticky="nsew")

        header_frame = tk.Frame(main_frame, bg="#003087")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(header_frame, text="📋 Nhập Thông Tin Vật Dụng", 
                font=("Arial", 14, "bold"), bg="#003087", fg="#FFFFFF").pack(pady=10)

        loai_thiet_bi_list = self.get_device_types_from_json()

        labels = ["Mã:", "Tên vật dụng:", "Trạng thái:", "Người mượn:", "Số lượng:", "Loại thiết bị:"]
        self.entries = []

        for i, label in enumerate(labels):
            tk.Label(main_frame, text=label, bg="#FFFFFF").grid(row=i+1, column=0, sticky="e", padx=5, pady=3)
            if label == "Trạng thái:":
                entry = ttk.Combobox(main_frame, values=["Có sẵn", "Đang mượn", "Đang bảo trì"], state="readonly", width=30)
                entry.set("Có sẵn")
            elif label == "Số lượng:":
                entry = tk.Entry(main_frame, width=32)
                entry.insert(0, "1")
            elif label == "Loại thiết bị:":
                entry = ttk.Combobox(main_frame, values=loai_thiet_bi_list, state="readonly", width=30)
                if loai_thiet_bi_list:
                    entry.set(loai_thiet_bi_list[0])
                else:
                    entry.set("")
            else:
                entry = tk.Entry(main_frame, width=32)
            entry.grid(row=i+1, column=1, sticky="w", padx=5, pady=3)
            self.entries.append(entry)

        tk.Label(main_frame, text="Ảnh thiết bị:", bg="#FFFFFF").grid(row=len(labels)+1, column=0, sticky="e", padx=5, pady=3)
        image_frame = tk.Frame(main_frame, bg="#FFFFFF")
        image_frame.grid(row=len(labels)+1, column=1, sticky="w", padx=5, pady=3)
        self.image_path = tk.StringVar()
        self.image_path.set("Chưa chọn ảnh")
        self.image_label = tk.Label(image_frame, textvariable=self.image_path, bg="#FFFFFF")
        self.image_label.grid(row=0, column=0, padx=5)
        tk.Button(image_frame, text="Chọn ảnh", command=self.choose_image,
                 bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat").grid(row=0, column=1)

        tk.Button(main_frame, text="Lưu", command=self.save_data, width=12,
                  bg="#003087", fg="white", font=("Arial", 11, "bold"), relief="flat").grid(row=len(labels)+2, column=1, sticky="e", padx=5, pady=15)

    def choose_image(self):
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh thiết bị",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_path.set(file_path)

    def save_data(self):
        values = [entry.get().strip() for entry in self.entries]
        
        if not values[0] or not values[1]:
            messagebox.showwarning("Thiếu thông tin", "Mã và tên vật dụng là bắt buộc.")
            return

        try:
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []

            image_filename = ""
            if self.image_path.get() != "Chưa chọn ảnh":
                file_ext = os.path.splitext(self.image_path.get())[1]
                image_filename = f"device_{values[0]}{file_ext}"
                
                if not os.path.exists(IMAGE_DIR):
                    os.makedirs(IMAGE_DIR)
                
                shutil.copy2(self.image_path.get(), os.path.join(IMAGE_DIR, image_filename))

            new_device = {
                "id": int(values[0]),
                "ten": values[1],
                "trang_thai": values[2],
                "so_luong_tong": int(values[4]),
                "loai": values[5],
                "hinh_anh": image_filename,
                "ban_ghi_muon": []
            }

            data.append(new_device)

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("Thành công", "Đã lưu thông tin thiết bị mới")
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Lỗi", "Mã thiết bị và số lượng phải là số")
        except Exception as e:
            messagebox.showerror("Lỗi", "Đã xảy ra lỗi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại!")

    def get_device_types_from_json(self):
        try:
            if not os.path.exists("danh_muc_loai_thiet_bi.json"):
                return ["Laptop", "Máy tính", "Chuột", "Bàn phím", "Tai nghe"]
            with open("danh_muc_loai_thiet_bi.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
            return ["Laptop", "Máy tính", "Chuột", "Bàn phím", "Tai nghe"]
        except Exception:
            return ["Laptop", "Máy tính", "Chuột", "Bàn phím", "Tai nghe"]

if __name__ == "__main__":
    root = tk.Tk()
    app = LabManagerGUI(root)
    root.mainloop()