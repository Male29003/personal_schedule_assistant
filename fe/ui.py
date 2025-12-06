import sys, os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import winsound
from datetime import datetime, timedelta

from db.db_manager import DBManager
from modules.nlp import NLPProcessor

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Trợ Lý Lịch Trình Thông Minh")
        self.root.geometry('900x600')

        self.db = DBManager()
        self.nlp = NLPProcessor()

        self.running = True
        self.setup_ui()
        self.load_data()

        self.thread = threading.Thread(target=self.check_reminders, daemon=True)

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#f0f0f0", pady=15, padx=15)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="Nhập câu lệnh (VD: Họp team lúc 9h sáng mai)", 
                 bg="#f0f0f0", font=("Arial", 11)).pack(anchor="w")
        
        self.txt_input = tk.Entry(header_frame, font=("Arial", 12))
        self.txt_input.pack(fill="x", pady=5, ipady=5)
        self.txt_input.bind("<Return>", self.on_add_event) # Enter để thêm
        
        btn_add = tk.Button(header_frame, text="➕ Thêm Sự Kiện", bg="#007bff", fg="white", 
                            font=("Arial", 10, "bold"), command=self.on_add_event)
        btn_add.pack(side="right", pady=5)

        # --- 2. BODY (Danh sách) ---
        body_frame = tk.Frame(self.root, padx=15, pady=5)
        body_frame.pack(fill="both", expand=True)
        
        # Bảng hiển thị
        columns = ("ID", "Nội dung", "Thời gian", "Địa điểm", "Nhắc trước")
        self.tree = ttk.Treeview(body_frame, columns=columns, show="headings", height=20)
        
        # Định nghĩa cột
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=30)
        self.tree.heading("Nội dung", text="Nội dung sự kiện")
        self.tree.column("Nội dung", width=250)
        self.tree.heading("Thời gian", text="Thời gian diễn ra")
        self.tree.column("Thời gian", width=120)
        self.tree.heading("Địa điểm", text="Địa điểm")
        self.tree.column("Địa điểm", width=150)
        self.tree.heading("Nhắc trước", text="Nhắc nhở")
        self.tree.column("Nhắc trước", width=80)
        
        self.tree.pack(fill="both", expand=True)
        
        # --- 3. FOOTER (Chức năng phụ) ---
        footer_frame = tk.Frame(self.root, pady=10)
        footer_frame.pack(fill="x")
        tk.Button(footer_frame, text="🔄 Làm mới", command=self.load_data).pack(side="left", padx=10)
        tk.Button(footer_frame, text="❌ Xóa sự kiện", command=self.delete_event, bg="#dc3545", fg="white").pack(side="right", padx=10)

    def on_add_event(self, event=None):
        raw_text = self.txt_input.get().strip()
        if not raw_text: return
        
        # Gọi NLP xử lý
        try:
            data = self.nlp.analyze(raw_text)
            
            # Hiển thị confirm
            msg = f"Xác nhận thêm sự kiện?\n\n- Sự kiện: {data['event']}\n- Thời gian: {data['start_time']}\n- Địa điểm: {data['location']}\n- Nhắc trước: {data['reminder_minutes']} phút"
            if messagebox.askyesno("Xác nhận NLP", msg):
                # Map dữ liệu sang đúng tên trường của DB
                db_data = {
                    "event": data['event'],
                    "start_time": data['start_time'],
                    "location": data['location'],
                    "reminder_minutes": data['reminder_minutes']
                }
                if self.db.add_event(**db_data):
                    self.txt_input.delete(0, 'end')
                    self.load_data()
                    messagebox.showinfo("Thành công", "Đã lưu sự kiện!")
                else:
                    messagebox.showwarning("Trùng lặp", "Sự kiện này đã tồn tại!")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def load_data(self):
        # Xóa cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Load mới
        events = self.db.get_upcoming_events()
        for evt in events:
            # evt: (id, ev, start_time, location, reminder)
            self.tree.insert("", "end", values=(evt[0], evt[1], evt[2], evt[3], f"{evt[4]}p"))

    def delete_event(self):
        selected = self.tree.selection()
        if selected:
            # Logic xóa demo (cần thêm hàm delete trong db_manager để xóa thật)
            for item in selected:
                self.tree.delete(item)
            messagebox.showinfo("Thông báo", "Đã xóa hiển thị (Cần cập nhật DB delete function)")

    def check_reminders(self):
        """Luồng chạy ngầm kiểm tra nhắc nhở mỗi 60s"""
        while self.running:
            try:
                # Lấy tất cả sự kiện sắp tới
                events = self.db.get_upcoming_events()
                now = datetime.now()
                
                for evt in events:
                    # evt[2] là chuỗi ISO time 'YYYY-MM-DD HH:MM:SS'
                    start_time = datetime.strptime(evt[2], "%Y-%m-%d %H:%M:%S")
                    reminder_min = evt[4]
                    
                    # Tính thời gian cần báo thức
                    trigger_time = start_time - timedelta(minutes=reminder_min)
                    
                    # Kiểm tra: Nếu trigger_time trùng với hiện tại (tính theo phút)
                    # (Chấp nhận sai số trong vòng 60 giây)
                    diff = (trigger_time - now).total_seconds()
                    
                    if -30 <= diff <= 30: 
                        # Phát âm thanh (Windows)
                        winsound.Beep(1000, 500) # Tần số 1000Hz, 0.5s
                        
                        # Hiện Popup (Cần dùng main thread để update GUI)
                        self.root.after(0, lambda e=evt: messagebox.showwarning(
                            "🔔 NHẮC NHỞ", 
                            f"Sắp đến giờ: {e[1]}\nLúc: {e[2]}\nTại: {e[3]}"
                        ))
                        
                        # Đánh dấu đã nhắc (để tránh nhắc lại) - Cần update DB status=1
                        # self.db.mark_as_notified(evt[0]) (Bạn tự thêm hàm này nếu kịp)
                        time.sleep(60) # Ngủ 1 chút để không spam popup cho cùng 1 sự kiện
                        
            except Exception as e:
                print(f"Lỗi Reminder: {e}")
            
            # Ngủ 60 giây trước khi check lần tiếp theo
            time.sleep(60)