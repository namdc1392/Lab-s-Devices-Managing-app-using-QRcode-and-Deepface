import ttkbootstrap as ttk
from ttkbootstrap import Style
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
from datetime import datetime, timedelta
import json
import os
from GiaodienSQL import DanhMucVatDung
from Giaodien_trangT import CapNhatTrangThaiApp
from Giaodien_Kientr import KiemTraPhanLoaiApp
from GiaodienMa import LabManagerGUI
from Giaodien_Baocao import ReportGeneratorApp
from PIL import Image, ImageTk

class LabManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧪 Quản Lý Vật Dụng Phòng Lab")
        self.root.geometry("1400x900")
        
        # Áp dụng Blue theme
        self.style = Style(theme='litera')
        
        # Tạo gradient background
        self.create_gradient_background()
        
        # Frame chính
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill='both', expand=True)
        
        # Header với card style
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill='x', pady=(0, 20))
        
        # Title card
        self.title_card = ttk.LabelFrame(self.header_frame, text="", padding=15, bootstyle="primary")
        self.title_card.pack(fill='x')
        
        title_frame = ttk.Frame(self.title_card)
        title_frame.pack(fill='x')
        
        logo = ttk.Label(title_frame, text="🏛️", font=("Arial", 24))
        logo.pack(side='left', padx=(0, 15))
        
        title = ttk.Label(title_frame, text="Hệ Thống Quản Lý Phòng Lab Bằng Mã Barcode", 
                         font=("Arial", 18, "bold"))
        title.pack(side='left')
        
        # Menu buttons frame
        self.menu_frame = ttk.LabelFrame(self.main_frame, text="Chức năng", padding=15)
        self.menu_frame.pack(fill='x', pady=(0, 20))
        
        # Table frame
        self.table_frame = ttk.LabelFrame(self.main_frame, text="Danh sách thiết bị", padding=15)
        self.table_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Log frame
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Nhật ký hệ thống", padding=15)
        self.log_frame.pack(fill='x')
        
        # Mật khẩu và thời gian
        self.password = "admin@"
        self.login_timeout = timedelta(minutes=5)
        self.last_login_time = None
        
        self.create_widgets()
        self.load_device_list()
        self.log("[INFO] Hệ thống sẵn sàng. Vui lòng chọn chức năng để bắt đầu.")

    def create_gradient_background(self):
        """Tạo gradient background từ xanh đậm đến xanh nhạt"""
        # Tạo Canvas để vẽ gradient
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        def update_gradient(event=None):
            width = self.bg_canvas.winfo_width()
            height = self.bg_canvas.winfo_height()
            
            # Xóa gradient cũ
            self.bg_canvas.delete("gradient")
            
            # Tạo gradient từ xanh navy (#1e3a8a) đến xanh nhạt (#bfdbfe)
            start_color = (30, 58, 138)    # #1e3a8a - xanh navy
            end_color = (191, 219, 254)     # #bfdbfe - xanh nhạt
            
            # Vẽ gradient theo chiều dọc
            steps = height
            for i in range(steps):
                # Tính toán màu cho từng dải
                ratio = i / steps
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Vẽ dải màu
                self.bg_canvas.create_rectangle(
                    0, i, width, i + 1, 
                    fill=color, outline=color, tags="gradient"
                )
        
        # Bind sự kiện resize để cập nhật gradient
        self.bg_canvas.bind('<Configure>', update_gradient)
        self.root.after(100, update_gradient)  # Cập nhật gradient lần đầu

    def create_widgets(self):
        # Menu buttons với bootstrap styling
        buttons = [
            ("🔍 Quét & Sinh Mã", self.open_detection_gui, "info"),
            ("➕ Thêm Mới", self.verify_and_add, "success"), 
            ("🗑️ Xóa Đã Chọn", self.delete_selected, "danger"),
            ("🔄 Làm Mới", self.refresh_list, "warning"),
            ("📊 Báo Cáo", self.send_report, "info"),
            ("📋 Danh sách mượn", self.open_borrow_list, "secondary"),
            ("❌ Thoát", self.root.quit, "danger")
        ]
        
        # Tạo grid layout cho buttons
        button_frame = ttk.Frame(self.menu_frame)
        button_frame.pack(fill='x')
        
        for i, (text, command, style) in enumerate(buttons):
            row = i // 4
            col = i % 4
            button = ttk.Button(button_frame, text=text, command=command, 
                               bootstyle=style, width=15)
            button.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Configure grid weights
        for col in range(4):
            button_frame.grid_columnconfigure(col, weight=1)

        # Device table với bootstrap styling
        self.create_device_table()

        # Log area với scrollbar
        log_container = ttk.Frame(self.log_frame)
        log_container.pack(fill='both', expand=True)
        
        self.status_text = ttk.Text(log_container, height=6, font=("Courier", 10))
        scrollbar_log = ttk.Scrollbar(log_container, orient='vertical', command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar_log.set)
        
        self.status_text.pack(side='left', fill='both', expand=True)
        scrollbar_log.pack(side='right', fill='y')

    def create_device_table(self):
        # Table container
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill='both', expand=True)
        
        # Treeview với bootstrap styling
        columns = ("ID", "Loại", "Tên", "Trạng thái")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", bootstyle="info")
        
        # Configure headings
        self.tree.heading("ID", text="Mã thiết bị")
        self.tree.heading("Loại", text="Loại thiết bị")
        self.tree.heading("Tên", text="Tên thiết bị")
        self.tree.heading("Trạng thái", text="Trạng thái")
        
        # Configure columns
        self.tree.column("ID", width=120, minwidth=100)
        self.tree.column("Loại", width=180, minwidth=150)
        self.tree.column("Tên", width=250, minwidth=200)
        self.tree.column("Trạng thái", width=120, minwidth=100)
        
        # Scrollbar for table
        scrollbar_table = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_table.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar_table.pack(side='right', fill='y')
        
        self.tree.configure(selectmode="extended")

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.load_device_list()
        self.log("[REFRESH] Đã cập nhật danh sách thiết bị")

    def load_device_list(self):
        try:
            if os.path.exists("danh_sach_vat_dung.json"):
                with open("danh_sach_vat_dung.json", "r", encoding="utf-8") as f:
                    devices = json.load(f)
                    for device in devices:
                        if isinstance(device, dict):
                            so_luong_da_muon = sum(record.get("so_luong", 0) for record in device.get("ban_ghi_muon", []))
                            so_luong_con_lai = device.get("so_luong_tong", 0) - so_luong_da_muon
                            trang_thai = device.get("trang_thai", "Có sẵn")
                            self.tree.insert("", "end", values=(
                                device.get("id", ""),
                                device.get("loai", ""),
                                device.get("ten", ""),
                                trang_thai
                            ))
                        elif isinstance(device, list):
                            if len(device) >= 6:
                                self.tree.insert("", "end", values=(
                                    device[0],
                                    device[5],
                                    device[1],
                                    device[2]
                                ))
                self.log("[SUCCESS] Đã tải danh sách thiết bị thành công")
        except Exception as e:
            self.log(f"[ERROR] Lỗi khi tải danh sách thiết bị: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách thiết bị: {str(e)}")

    def delete_selected(self):
        if self.verify_password():
            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn thiết bị cần xóa!")
                return
            if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa các thiết bị đã chọn?"):
                try:
                    with open("danh_sach_vat_dung.json", "r", encoding="utf-8") as f:
                        devices = json.load(f)
                    ids_to_delete = [int(self.tree.item(item)["values"][0]) for item in selected_items]
                    devices = [device for device in devices if device["id"] not in ids_to_delete]
                    with open("danh_sach_vat_dung.json", "w", encoding="utf-8") as f:
                        json.dump(devices, f, ensure_ascii=False, indent=2)
                    self.refresh_list()
                    self.log(f"[SUCCESS] Đã xóa {len(ids_to_delete)} thiết bị thành công")
                except Exception as e:
                    self.log(f"[ERROR] Lỗi khi xóa thiết bị: {str(e)}")
                    messagebox.showerror("Lỗi", f"Không thể xóa thiết bị: {str(e)}")

    def verify_password(self):
        if self.last_login_time and (datetime.now() - self.last_login_time) < self.login_timeout:
            return True
        
        # Tạo dialog với bootstrap styling
        password_dialog = ttk.Toplevel(self.root)
        password_dialog.title("Xác thực mật khẩu")
        password_dialog.geometry("400x250")
        password_dialog.resizable(False, False)
        
        main_frame = ttk.Frame(password_dialog, padding=30)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔐 Xác thực mật khẩu", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Password frame
        pass_frame = ttk.LabelFrame(main_frame, text="Nhập mật khẩu", padding=15)
        pass_frame.pack(fill='x', pady=(0, 20))
        
        password_entry = ttk.Entry(pass_frame, show="*", font=("Arial", 12))
        password_entry.pack(fill='x')
        password_entry.focus()
        
        result = {"verified": False}
        
        def check_password():
            if password_entry.get() == self.password:
                result["verified"] = True
                self.last_login_time = datetime.now()
                password_dialog.destroy()
            else:
                messagebox.showerror("Lỗi", "Mật khẩu không đúng!")
                password_entry.delete(0, 'end')
                password_entry.focus()
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        cancel_btn = ttk.Button(button_frame, text="Hủy", command=password_dialog.destroy,
                               bootstyle="secondary")
        cancel_btn.pack(side='right', padx=(10, 0))
        
        confirm_btn = ttk.Button(button_frame, text="Xác nhận", command=check_password,
                               bootstyle="primary")
        confirm_btn.pack(side='right')
        
        # Bind Enter key
        password_entry.bind('<Return>', lambda e: check_password())
        
        self.root.wait_window(password_dialog)
        return result["verified"]

    def verify_and_add(self):
        if self.verify_password():
            add_window = ttk.Toplevel(self.root)
            app = LabManagerGUI(add_window)
            app.add_new_device()
            self.refresh_list()
            self.log("[SUCCESS] Đã mở cửa sổ thêm thiết bị mới")

    def log(self, message):
        time_str = datetime.now().strftime("[%H:%M:%S]")
        self.status_text.insert('end', f"{time_str} {message}\n")
        self.status_text.see('end')

    def open_detection_gui(self):
        self.log("[INFO] Mở giao diện quét & sinh mã thiết bị...")
        try:
            subprocess.Popen(["python", "GiaodienMa.py"])
            self.root.after(2000, self.refresh_list)
        except:
            messagebox.showerror("Lỗi", "Không tìm thấy file GiaodienMa.py")

    def send_report(self):
        if self.verify_password():
            self.log("[INFO] Đang mở giao diện báo cáo...")
            try:
                subprocess.Popen(["python", "Giaodien_Baocao.py"])
            except:
                messagebox.showerror("Lỗi", "Không tìm thấy file Giaodien_Baocao.py")

    def open_borrow_list(self):
        borrow_window = ttk.Toplevel(self.root)
        borrow_window.title("Danh sách mượn thiết bị")
        borrow_window.geometry("1200x700")
        
        main_frame = ttk.Frame(borrow_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title frame
        title_frame = ttk.LabelFrame(main_frame, text="Quản lý mượn thiết bị", padding=15, bootstyle="info")
        title_frame.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="📋 Danh sách mượn thiết bị", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side='left')
        
        refresh_button = ttk.Button(title_frame, text="🔄 Làm mới", 
                                  command=lambda: self.refresh_borrow_list(tree),
                                  bootstyle="warning")
        refresh_button.pack(side='right')
        
        # Table frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True)
        
        columns = ("Người mượn", "Số điện thoại", "Địa chỉ", "Thời gian mượn", 
                  "Thời gian trả", "Trạng thái")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", bootstyle="info")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.column("Người mượn", width=150)
        tree.column("Số điện thoại", width=120)
        tree.column("Địa chỉ", width=200)
        tree.column("Thời gian mượn", width=150)
        tree.column("Thời gian trả", width=150)
        tree.column("Trạng thái", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.refresh_borrow_list(tree)

    def refresh_borrow_list(self, tree):
        for item in tree.get_children():
            tree.delete(item)
        try:
            with open("danh_sach_vat_dung.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if isinstance(item, dict):
                    for record in item.get("ban_ghi_muon", []):
                        if not record.get("da_tra", False):
                            trang_thai = "Đang mượn"
                            if record.get("ngay_tra"):
                                try:
                                    ngay_tra = datetime.strptime(record["ngay_tra"], "%Y-%m-%d")
                                    if ngay_tra < datetime.now():
                                        trang_thai = "Quá hạn"
                                except:
                                    pass
                            tree.insert("", "end", values=(
                                record.get("nguoi_muon", ""),
                                record.get("so_dien_thoai", ""),
                                record.get("dia_chi", ""),
                                record.get("ngay_muon", ""),
                                record.get("ngay_tra", ""),
                                trang_thai
                            ))
                elif isinstance(item, list):
                    if len(item) > 3 and item[3]:
                        nguoi_muon = item[3]
                        so_dt = item[7] if len(item) > 7 else ""
                        dia_chi = item[8] if len(item) > 8 else ""
                        thoi_gian_muon = item[9] if len(item) > 9 else ""
                        thoi_gian_tra = item[10] if len(item) > 10 else ""
                        trang_thai = ""
                        tree.insert("", "end", values=(
                            nguoi_muon,
                            so_dt,
                            dia_chi,
                            thoi_gian_muon,
                            thoi_gian_tra,
                            trang_thai
                        ))
        except Exception as e:
            print(f"Lỗi đọc dữ liệu: {e}")
            messagebox.showerror("Lỗi", "Không thể đọc dữ liệu mượn thiết bị")

    def show_maintenance(self):
        if not self.check_login():
            return
        self.log("🔧 Mở danh sách bảo trì...")
        from GiaodienMa import LabManagerGUI
        maintenance_window = ttk.Toplevel(self.root)
        app = LabManagerGUI(maintenance_window)
        app.show_maintenance_list()
        self.refresh_device_list()

    def check_login(self):
        return self.verify_password()

if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = LabManagerApp(root)
    root.mainloop()