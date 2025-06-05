import tkinter as tk
from tkinter import messagebox

class KiemTraPhanLoaiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Kiểm Tra & Phân Loại")
        self.root.geometry("400x250")

        label = tk.Label(root, text="🔍 Kiểm tra mã vật dụng", font=("Arial", 14))
        label.pack(pady=10)

        self.entry_ma = tk.Entry(root, width=30)
        self.entry_ma.pack(pady=5)

        self.btn_kiemtra = tk.Button(root, text="🧪 Phân Loại Trạng Thái", command=self.phan_loai)
        self.btn_kiemtra.pack(pady=10)

        self.result_label = tk.Label(root, text="", font=("Arial", 12), fg="blue")
        self.result_label.pack()

    def phan_loai(self):
        ma = self.entry_ma.get()
        if not ma:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập mã vật dụng!")
            return
        
        # Giả lập phân loại
        trang_thai = "Đang sử dụng"  # Có thể thay bằng AI model
        self.result_label.config(text=f"Mã '{ma}' được phân loại là: {trang_thai}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KiemTraPhanLoaiApp(root)
    root.mainloop()
