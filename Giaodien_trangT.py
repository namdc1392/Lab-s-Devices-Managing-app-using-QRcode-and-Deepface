import tkinter as tk
from tkinter import ttk, messagebox

class CapNhatTrangThaiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📝 Cập Nhật Trạng Thái")
        self.root.geometry("400x300")

        tk.Label(root, text="🔖 Nhập mã vật dụng:", font=("Arial", 12)).pack(pady=5)
        self.entry_ma = tk.Entry(root, width=30)
        self.entry_ma.pack(pady=5)

        tk.Label(root, text="📌 Chọn trạng thái mới:", font=("Arial", 12)).pack(pady=5)
        self.trang_thai_combobox = ttk.Combobox(root, values=[
            "Đang sử dụng", "Hư hỏng", "Cần bảo trì", "Không sử dụng"
        ])
        self.trang_thai_combobox.pack(pady=5)

        self.btn_capnhat = tk.Button(root, text="💾 Cập Nhật", command=self.cap_nhat_trang_thai)
        self.btn_capnhat.pack(pady=15)

        self.result_label = tk.Label(root, text="", font=("Arial", 11), fg="green")
        self.result_label.pack()

    def cap_nhat_trang_thai(self):
        ma = self.entry_ma.get()
        trang_thai = self.trang_thai_combobox.get()
        if not ma or not trang_thai:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đầy đủ thông tin.")
            return

        # Giả lập cập nhật
        self.result_label.config(text=f"Đã cập nhật mã '{ma}' thành '{trang_thai}'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CapNhatTrangThaiApp(root)
    root.mainloop()
