import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import asyncio
import telegram
import io

# Đường dẫn đến các file dữ liệu
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, "danh_sach_vat_dung.json")
HISTORY_FILE = os.path.join(CURRENT_DIR, "lich_su_quet.json")
CATEGORY_FILE = os.path.join(CURRENT_DIR, "danh_muc_loai_thiet_bi.json")
OUTPUT_CHART = os.path.join(CURRENT_DIR, "report_chart.png")
OUTPUT_PDF = os.path.join(CURRENT_DIR, "report.pdf")

class ReportGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Tạo Báo Cáo")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#FFFFFF")

        # Khung chính
        self.main_frame = tk.Frame(self.root, bg="#FFFFFF")
        self.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Tiêu đề
        header_frame = tk.Frame(self.main_frame, bg="#003087")
        header_frame.pack(fill=tk.X)
        self.title_label = tk.Label(header_frame, 
                                  text="📊 Tạo Báo Cáo và Biểu Đồ", 
                                  font=("Arial", 16, "bold"), 
                                  bg="#003087", 
                                  fg="#FFFFFF")
        self.title_label.pack(pady=10)

        # Frame cho bộ lọc
        self.filter_frame = tk.Frame(self.main_frame, bg="#FFFFFF")
        self.filter_frame.pack(fill=tk.X, pady=10)

        # Loại báo cáo
        tk.Label(self.filter_frame, text="Loại báo cáo:", font=("Arial", 11), bg="#FFFFFF").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.report_type_combobox = ttk.Combobox(self.filter_frame, 
                                               values=[
                                                   "Biểu đồ Tròn - Trạng thái thiết bị",
                                                   "Biểu đồ Cột - Số lượng theo loại thiết bị",
                                                   "Biểu đồ Đường - Tần suất quét mã"
                                               ], 
                                               width=30, 
                                               state="readonly")
        self.report_type_combobox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.report_type_combobox.set("Biểu đồ Tròn - Trạng thái thiết bị")
        self.report_type_combobox.bind("<<ComboboxSelected>>", self.update_filters)

        # Khoảng thời gian (cho biểu đồ đường)
        tk.Label(self.filter_frame, text="Từ ngày:", font=("Arial", 11), bg="#FFFFFF").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.start_date = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', date_pattern='yyyy-mm-dd')
        self.start_date.set_date(datetime.now() - timedelta(days=30))
        self.start_date.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(self.filter_frame, text="Đến ngày:", font=("Arial", 11), bg="#FFFFFF").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.end_date = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', date_pattern='yyyy-mm-dd')
        self.end_date.set_date(datetime.now())
        self.end_date.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Loại thiết bị (cho biểu đồ cột)
        tk.Label(self.filter_frame, text="Loại thiết bị:", font=("Arial", 11), bg="#FFFFFF").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.category_combobox = ttk.Combobox(self.filter_frame, width=30, state="readonly")
        self.category_combobox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.category_combobox['values'] = ["Tất cả"] + self.load_data(CATEGORY_FILE)
        self.category_combobox.set("Tất cả")

        # Trạng thái thiết bị (cho biểu đồ tròn)
        tk.Label(self.filter_frame, text="Trạng thái:", font=("Arial", 11), bg="#FFFFFF").grid(row=2, column=2, sticky="e", padx=5, pady=5)
        self.status_combobox = ttk.Combobox(self.filter_frame, 
                                          values=["Tất cả", "Có sẵn", "Đang mượn", "Đang bảo trì"], 
                                          width=15, 
                                          state="readonly")
        self.status_combobox.grid(row=2, column=3, sticky="w", padx=5, pady=5)
        self.status_combobox.set("Tất cả")

        # Frame cho nút và thanh tiến trình
        self.action_frame = tk.Frame(self.main_frame, bg="#FFFFFF")
        self.action_frame.pack(fill=tk.X, pady=10)

        # Nút hiển thị số liệu
        self.show_data_button = tk.Button(self.action_frame, 
                                        text="📋 Hiển thị số liệu", 
                                        command=self.show_data, 
                                        bg="#003087", 
                                        fg="white", 
                                        font=("Arial", 11), 
                                        width=15)
        self.show_data_button.pack(side=tk.LEFT, padx=5)
        self.show_data_button.bind("<Enter>", lambda e: self.show_data_button.config(bg="#004D99"))
        self.show_data_button.bind("<Leave>", lambda e: self.show_data_button.config(bg="#003087"))

        # Nút vẽ biểu đồ
        self.plot_button = tk.Button(self.action_frame, 
                                   text="📈 Vẽ biểu đồ", 
                                   command=self.plot_chart, 
                                   bg="#003087", 
                                   fg="white", 
                                   font=("Arial", 11), 
                                   width=15)
        self.plot_button.pack(side=tk.LEFT, padx=5)
        self.plot_button.bind("<Enter>", lambda e: self.plot_button.config(bg="#004D99"))
        self.plot_button.bind("<Leave>", lambda e: self.plot_button.config(bg="#003087"))

        # Nút gửi báo cáo
        self.send_button = tk.Button(self.action_frame, 
                                   text="📤 Gửi báo cáo", 
                                   command=self.send_report, 
                                   bg="#003087", 
                                   fg="white", 
                                   font=("Arial", 11), 
                                   width=15)
        self.send_button.pack(side=tk.LEFT, padx=5)
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(bg="#004D99"))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(bg="#003087"))

        # Thanh tiến trình
        self.progress = ttk.Progressbar(self.action_frame, length=200, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=5)

        # Frame cho bảng số liệu
        self.table_frame = tk.Frame(self.main_frame, bg="#FFFFFF")
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Treeview cho bảng số liệu
        self.tree = ttk.Treeview(self.table_frame, show="headings", height=10)
        self.tree_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Cập nhật bộ lọc ban đầu
        self.update_filters()

    def load_data(self, file_path):
        """Đọc dữ liệu từ file JSON"""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file {file_path}: {str(e)}")
            return []

    def update_filters(self, event=None):
        """Cập nhật bộ lọc dựa trên loại báo cáo"""
        report_type = self.report_type_combobox.get()
        if "Tròn" in report_type:
            self.start_date.grid_remove()
            self.end_date.grid_remove()
            self.category_combobox.grid_remove()
            self.status_combobox.grid()
        elif "Cột" in report_type:
            self.start_date.grid_remove()
            self.end_date.grid_remove()
            self.status_combobox.grid_remove()
            self.category_combobox.grid()
        else:  # Đường
            self.start_date.grid()
            self.end_date.grid()
            self.status_combobox.grid_remove()
            self.category_combobox.grid_remove()

    def show_data(self):
        """Hiển thị số liệu trong bảng Treeview"""
        self.progress.start()
        report_type = self.report_type_combobox.get()
        self.tree.delete(*self.tree.get_children())

        if report_type == "Biểu đồ Tròn - Trạng thái thiết bị":
            # Đọc dữ liệu thiết bị
            data = self.load_data(DATA_FILE)
            if not data:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu thiết bị")
                self.progress.stop()
                return

            # Đếm số lượng thiết bị theo trạng thái
            status_counts = {}
            selected_status = self.status_combobox.get()
            for item in data:
                trang_thai = item.get("trang_thai", "Không xác định") if isinstance(item, dict) else item[2] if len(item) > 2 else "Không xác định"
                if selected_status == "Tất cả" or trang_thai == selected_status:
                    status_counts[trang_thai] = status_counts.get(trang_thai, 0) + 1

            # Cấu hình Treeview
            self.tree["columns"] = ("Trạng thái", "Số lượng")
            self.tree.heading("Trạng thái", text="Trạng thái")
            self.tree.heading("Số lượng", text="Số lượng")
            self.tree.column("Trạng thái", width=200)
            self.tree.column("Số lượng", width=100)

            # Thêm dữ liệu vào Treeview
            for status, count in status_counts.items():
                self.tree.insert("", "end", values=(status, count))

        elif report_type == "Biểu đồ Cột - Số lượng theo loại thiết bị":
            # Đọc dữ liệu thiết bị
            data = self.load_data(DATA_FILE)
            categories = self.load_data(CATEGORY_FILE)
            if not data:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu thiết bị")
                self.progress.stop()
                return

            # Đếm số lượng thiết bị theo loại
            type_counts = {cat: 0 for cat in categories}
            type_counts["Không xác định"] = 0
            selected_category = self.category_combobox.get()
            for item in data:
                loai = item.get("loai", "Không xác định") if isinstance(item, dict) else item[5] if len(item) > 5 else "Không xác định"
                if selected_category == "Tất cả" or loai == selected_category:
                    type_counts[loai] = type_counts.get(loai, 0) + 1

            # Cấu hình Treeview
            self.tree["columns"] = ("Loại thiết bị", "Số lượng")
            self.tree.heading("Loại thiết bị", text="Loại thiết bị")
            self.tree.heading("Số lượng", text="Số lượng")
            self.tree.column("Loại thiết bị", width=200)
            self.tree.column("Số lượng", width=100)

            # Thêm dữ liệu vào Treeview
            for category, count in type_counts.items():
                if count > 0:
                    self.tree.insert("", "end", values=(category, count))

        elif report_type == "Biểu đồ Đường - Tần suất quét mã":
            # Đọc dữ liệu lịch sử quét
            history = self.load_data(HISTORY_FILE)
            if not history:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu lịch sử quét")
                self.progress.stop()
                return

            # Lọc theo khoảng thời gian
            start_date = self.start_date.get_date()
            end_date = self.end_date.get_date()
            date_counts = {}
            for record in history:
                record_date = datetime.strptime(record["thoi_gian"], "%Y-%m-%d %H:%M:%S").date()
                if start_date <= record_date <= end_date:
                    date_counts[record_date] = date_counts.get(record_date, 0) + 1

            # Cấu hình Treeview
            self.tree["columns"] = ("Ngày", "Số lần quét")
            self.tree.heading("Ngày", text="Ngày")
            self.tree.heading("Số lần quét", text="Số lần quét")
            self.tree.column("Ngày", width=200)
            self.tree.column("Số lần quét", width=100)

            # Thêm dữ liệu vào Treeview
            for date, count in sorted(date_counts.items()):
                self.tree.insert("", "end", values=(date.strftime("%Y-%m-%d"), count))

        self.progress.stop()

    def plot_chart(self):
        """Vẽ biểu đồ dựa trên loại báo cáo được chọn"""
        self.progress.start()
        report_type = self.report_type_combobox.get()
        sns.set_style("whitegrid")
        plt.figure(figsize=(8, 6))

        if report_type == "Biểu đồ Tròn - Trạng thái thiết bị":
            # Đọc dữ liệu thiết bị
            data = self.load_data(DATA_FILE)
            if not data:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu thiết bị")
                self.progress.stop()
                return

            # Đếm số lượng thiết bị theo trạng thái
            status_counts = {}
            selected_status = self.status_combobox.get()
            for item in data:
                trang_thai = item.get("trang_thai", "Không xác định") if isinstance(item, dict) else item[2] if len(item) > 2 else "Không xác định"
                if selected_status == "Tất cả" or trang_thai == selected_status:
                    status_counts[trang_thai] = status_counts.get(trang_thai, 0) + 1

            if not status_counts:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu phù hợp với bộ lọc")
                self.progress.stop()
                return

            # Vẽ biểu đồ tròn
            labels = list(status_counts.keys())
            sizes = list(status_counts.values())
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("pastel"))
            plt.title("Phân bố trạng thái thiết bị", fontsize=14)

        elif report_type == "Biểu đồ Cột - Số lượng theo loại thiết bị":
            # Đọc dữ liệu thiết bị
            data = self.load_data(DATA_FILE)
            categories = self.load_data(CATEGORY_FILE)
            if not data:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu thiết bị")
                self.progress.stop()
                return

            # Đếm số lượng thiết bị theo loại
            type_counts = {cat: 0 for cat in categories}
            type_counts["Không xác định"] = 0
            selected_category = self.category_combobox.get()
            for item in data:
                loai = item.get("loai", "Không xác định") if isinstance(item, dict) else item[5] if len(item) > 5 else "Không xác định"
                if selected_category == "Tất cả" or loai == selected_category:
                    type_counts[loai] = type_counts.get(loai, 0) + 1

            # Loại bỏ các loại không có thiết bị
            type_counts = {k: v for k, v in type_counts.items() if v > 0}

            if not type_counts:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu phù hợp với bộ lọc")
                self.progress.stop()
                return

            # Vẽ biểu đồ cột
            plt.bar(type_counts.keys(), type_counts.values(), color=sns.color_palette("muted"))
            plt.title("Số lượng thiết bị theo loại", fontsize=14)
            plt.xlabel("Loại thiết bị", fontsize=12)
            plt.ylabel("Số lượng", fontsize=12)
            plt.xticks(rotation=45, ha="right")

        elif report_type == "Biểu đồ Đường - Tần suất quét mã":
            # Đọc dữ liệu lịch sử quét
            history = self.load_data(HISTORY_FILE)
            if not history:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu lịch sử quét")
                self.progress.stop()
                return

            # Lọc theo khoảng thời gian
            start_date = self.start_date.get_date()
            end_date = self.end_date.get_date()
            date_counts = {}
            for record in history:
                record_date = datetime.strptime(record["thoi_gian"], "%Y-%m-%d %H:%M:%S").date()
                if start_date <= record_date <= end_date:
                    date_counts[record_date] = date_counts.get(record_date, 0) + 1

            if not date_counts:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu phù hợp với bộ lọc")
                self.progress.stop()
                return

            # Vẽ biểu đồ đường
            sorted_dates = sorted(date_counts.keys())
            counts = [date_counts[date] for date in sorted_dates]
            plt.plot([date.strftime("%Y-%m-%d") for date in sorted_dates], counts, marker='o', color=sns.color_palette("deep")[0])
            plt.title("Tần suất quét mã QR theo ngày", fontsize=14)
            plt.xlabel("Ngày", fontsize=12)
            plt.ylabel("Số lần quét", fontsize=12)
            plt.xticks(rotation=45)

        # Lưu biểu đồ vào file
        plt.tight_layout()
        plt.savefig(OUTPUT_CHART, dpi=300, bbox_inches="tight")
        plt.show()
        self.progress.stop()

        # Tạo PDF báo cáo
        self.create_pdf_report()

    def create_pdf_report(self):
        """Tạo file PDF chứa biểu đồ và bảng số liệu"""
        report_type = self.report_type_combobox.get()
        doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Tiêu đề
        elements.append(Paragraph("Báo Cáo Quản Lý Phòng Lab", styles['Title']))
        elements.append(Spacer(1, 12))

        # Thông tin báo cáo
        elements.append(Paragraph(f"Loại báo cáo: {report_type}", styles['Normal']))
        elements.append(Paragraph(f"Ngày tạo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Thêm biểu đồ
        if os.path.exists(OUTPUT_CHART):
            img = Image(OUTPUT_CHART, width=400, height=300)
            elements.append(img)
            elements.append(Spacer(1, 12))

        # Thêm bảng số liệu
        if report_type == "Biểu đồ Tròn - Trạng thái thiết bị":
            data = [["Trạng thái", "Số lượng"]]
            for item in self.tree.get_children():
                data.append(self.tree.item(item)["values"])
        elif report_type == "Biểu đồ Cột - Số lượng theo loại thiết bị":
            data = [["Loại thiết bị", "Số lượng"]]
            for item in self.tree.get_children():
                data.append(self.tree.item(item)["values"])
        else:
            data = [["Ngày", "Số lần quét"]]
            for item in self.tree.get_children():
                data.append(self.tree.item(item)["values"])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        # Lưu PDF
        doc.build(elements)
        messagebox.showinfo("Thành công", f"Báo cáo PDF đã được lưu tại {OUTPUT_PDF}")

    async def send_telegram(self):
        """Gửi báo cáo qua Telegram (giả lập hoặc thực tế nếu có API key)"""
        # Thay thế bằng API key và chat ID thực tế
        TELEGRAM_BOT_TOKEN = "8166847649:AAHkwscQjJr0emqQ61CUeU_6RobCMN0df_s"
        TELEGRAM_CHAT_ID = "6553772266"

        if TELEGRAM_BOT_TOKEN == "8166847649:AAHkwscQjJr0emqQ61CUeU_6RobCMN0df_s":
            messagebox.showinfo("Giả lập", "Gửi báo cáo qua Telegram (giả lập)!")
            return

        try:
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            async with bot:
                # Gửi biểu đồ
                with open(OUTPUT_CHART, 'rb') as chart_file:
                    await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=chart_file, caption="Báo cáo quản lý phòng lab")
                # Gửi PDF
                with open(OUTPUT_PDF, 'rb') as pdf_file:
                    await bot.send_document(chat_id=TELEGRAM_CHAT_ID, document=pdf_file, caption="Báo cáo chi tiết")
            messagebox.showinfo("Thành công", "Đã gửi báo cáo qua Telegram!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể gửi báo cáo qua Telegram: {str(e)}")

    def send_report(self):
        """Gửi báo cáo qua Telegram và hiển thị thông báo"""
        if not os.path.exists(OUTPUT_CHART) or not os.path.exists(OUTPUT_PDF):
            messagebox.showwarning("Cảnh báo", "Vui lòng tạo biểu đồ và báo cáo trước khi gửi!")
            return

        # Chạy hàm gửi Telegram bất đồng bộ
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_telegram())

if __name__ == "__main__":
    root = tk.Tk()
    app = ReportGeneratorApp(root)
    root.mainloop()