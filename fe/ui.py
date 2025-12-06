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
        self.thread.start()
# Tạo giao diện
    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10, padx=20) 
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="Nhập câu lệnh (VD: Họp team lúc 9h sáng mai)", 
                 bg="#f0f0f0", font=("Arial", 12)).pack(anchor="w")
        
        self.txt_input = tk.Entry(header_frame, font=("Arial", 14)) 
        self.txt_input.pack(fill="x", pady=5, ipady=8) # Giảm pady xuống 5
        self.txt_input.bind("<Return>", self.on_add_event)
        
        # Nút Thêm (Vẫn giữ to đẹp)
        btn_add = tk.Button(header_frame, text="➕ THÊM SỰ KIỆN", bg="#007bff", fg="white", 
                            font=("Arial", 11, "bold"), # Giảm font xuống 1 xíu
                            padx=20, pady=8, # Giảm độ cao nút 1 xíu
                            command=self.on_add_event, cursor="hand2")
        btn_add.pack(side="right", pady=5)

        # --- 2. BODY (Danh sách) ---
        body_frame = tk.Frame(self.root, padx=20, pady=5)
        body_frame.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", font=("Arial", 11), rowheight=30)
        
        columns = ("ID", "Nội dung", "Thời gian", "Địa điểm", "Nhắc trước")
        # --- QUAN TRỌNG: Giảm height xuống 10 dòng để chừa chỗ cho footer ---
        self.tree = ttk.Treeview(body_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=40, anchor="center")
        self.tree.heading("Nội dung", text="Nội dung sự kiện")
        self.tree.column("Nội dung", width=300)
        self.tree.heading("Thời gian", text="Thời gian diễn ra")
        self.tree.column("Thời gian", width=160, anchor="center")
        self.tree.heading("Địa điểm", text="Địa điểm")
        self.tree.column("Địa điểm", width=150)
        self.tree.heading("Nhắc trước", text="Nhắc nhở")
        self.tree.column("Nhắc trước", width=100, anchor="center")
        
        # Thêm thanh cuộn (Scrollbar) phòng trường hợp danh sách dài
        scrollbar = ttk.Scrollbar(body_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # --- 3. FOOTER (Nút chức năng) ---
        footer_frame = tk.Frame(self.root, pady=10, bg="#e9ecef") # Giảm pady
        footer_frame.pack(fill="x", side="bottom") # Neo chặt xuống đáy
        
        btn_style = {"font": ("Arial", 11, "bold"), "padx": 15, "pady": 8, "cursor": "hand2"}

        tk.Button(footer_frame, text="🔄 Làm mới", command=self.load_data, 
                  **btn_style).pack(side="left", padx=20)
        
        tk.Button(footer_frame, text="✏️ Sửa sự kiện", command=self.edit_event, bg="#ffc107", fg="black",
                  **btn_style).pack(side="left", padx=10)
        
        tk.Button(footer_frame, text="❌ Xóa sự kiện", command=self.delete_event, bg="#dc3545", fg="white",
                  **btn_style).pack(side="right", padx=20)
# Thêm ghi chú mới
    def on_add_event(self, event=None):
        raw_text = self.txt_input.get().strip()
        if not raw_text: return
        
        # Gọi NLP xử lý
        try:
            data = self.nlp.analyze(raw_text)
            
            start_dt = datetime.strptime(data['start_time'], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            diff_minutes = (start_dt - now).total_seconds() / 60

            if 0 < diff_minutes < data["reminder_minutes"]:
                data["reminder_minutes"] = 0
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
# Tải danh sách ghi chú
    def load_data(self):
        # Xóa cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Load mới
        events = self.db.get_upcoming_events()
        for evt in events:
            # evt: (id, ev, start_time, location, reminder)
            self.tree.insert("", "end", values=(evt[0], evt[1], evt[2], evt[3], f"{evt[4]}p"))
# Xóa ghi chú
    def delete_event(self):
        selected_items = self.tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Chú ý", "Vui lòng chọn sự kiện cần xóa!")
            return
        # Hỏi cho chắc ăn
        if not messagebox.askyesno("Xác nhận xóa", "Bác có chắc muốn xóa vĩnh viễn sự kiện này không?"):
            return
        
        is_deleted = False

        for item in selected_items:
            # Lấy data của ghi chú đang chọn
            values = self.tree.item(item, 'values')
            event_id = values[0] # Cột đầu tiên là ID
            
            # Gọi DB -> xóa
            if self.db.delete_event(event_id):
                is_deleted = True
                # Nếu DB xóa thành công thì mới xóa trên UI
                self.tree.delete(item)
            else:
                messagebox.showerror("Lỗi", f"Không xóa được sự kiện ID {event_id} trong Database!")
        if is_deleted:
            # --- QUAN TRỌNG: Gọi hàm load_data để tải lại danh sách từ DB ---
            self.load_data() 
            messagebox.showinfo("Thành công xóa được ghi chú")
# Hàm sửa ghi chú
    def edit_event(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Chú ý", "Vui lòng chọn sự kiện cần sửa!")
            return

        item_id = selection[0]
        item_data = self.tree.item(item_id) 
        values = item_data['values'] # Danh sách giá trị các cột: [id, event, time, loc, remind]

        # Kiểm tra xem values có đủ dữ liệu không để tránh lỗi index tiếp
        if len(values) < 5: 
             messagebox.showerror("Lỗi", "Dữ liệu dòng này bị thiếu!")
             return

        # 4. Gán dữ liệu vào biến (Lưu ý: values trả về danh sách theo thứ tự cột)
        old_id = values[0]       # Cột 1: ID
        old_event = values[1]    # Cột 2: Tên sự kiện
        old_time = values[2]     # Cột 3: Thời gian
        old_loc = values[3]      # Cột 4: Địa điểm
        old_remind = str(values[4]).replace("p", "")

        # Mở modal sửa
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Chỉnh sửa sự kiện")
        edit_window.geometry("400x350")

        # Tên cũ
        tk.Label(edit_window, text="Event:").pack(anchor="w", padx=20, pady=5)
        entry_content = tk.Entry(edit_window, width=40)
        entry_content.insert(0, old_event)
        entry_content.pack(padx=20)
        #Thời gian cũ
        tk.Label(edit_window, text="Thời gian (YYYY-MM-DD HH:MM:SS):").pack(anchor="w", padx=20, pady=5)
        entry_time = tk.Entry(edit_window, width=40)
        entry_time.insert(0, old_time)
        entry_time.pack(padx=20)
        #Địa điểm cũ
        tk.Label(edit_window, text="Địa điểm:").pack(anchor="w", padx=20, pady=5)
        entry_loc = tk.Entry(edit_window, width=40)
        entry_loc.insert(0, old_loc if old_loc != "None" else "")
        entry_loc.pack(padx=20)
        # reminder_minutes cũ
        tk.Label(edit_window, text="Nhắc trước (phút):").pack(anchor="w", padx=20, pady=5)
        entry_remind = tk.Entry(edit_window, width=40)
        entry_remind.insert(0, old_remind)
        entry_remind.pack(padx=20)
        
        def save_changes():
            new_content = entry_content.get()
            new_time = entry_time.get()
            new_loc = entry_loc.get()
            new_remind = entry_remind.get()

            # Validate sơ bộ
            if not new_content or not new_time:
                messagebox.showerror("Lỗi", "Nội dung và Thời gian không được để trống!", parent=edit_window)
                return

            # --- SỬA Ở ĐÂY ---
            # Dùng 'old_id' thay vì 'event_id'
            if self.db.update_event(old_id, new_content, new_time, new_loc, new_remind):
                messagebox.showinfo("Thành công", "Cập nhật thành công!", parent=edit_window)
                edit_window.destroy()  # Đóng popup
                self.load_data()       # Load lại danh sách bên ngoài
            else:
                messagebox.showerror("Lỗi", "Cập nhật thất bại!", parent=edit_window)

        tk.Button(edit_window, text="💾 Lưu thay đổi", command=save_changes, bg="#28a745", fg="white").pack(pady=20)


# Hàm kiểm tra thông báo - Chạy mỗi 10s
    def check_reminders(self):
        print("--- Thread Reminder đang chạy ---")
        while self.running:
            try:
                events = self.db.get_upcoming_events()
                now = datetime.now()
                
                for evt in events:
                    try:
                        # evt[2] là string time, parse ra object
                        start_time = datetime.strptime(evt[2], "%Y-%m-%d %H:%M:%S")
                        
                        # Xử lý reminder_minutes (chống lỗi None/Text)
                        r_raw = evt[4]
                        if r_raw is None or str(r_raw).strip() == "":
                            reminder_min = 0
                        else:
                            # Xóa chữ 'p' nếu có và ép kiểu int
                            reminder_min = int(float(str(r_raw).replace("p", "").strip()))
                        
                        # Tính thời gian báo thức
                        trigger_time = start_time - timedelta(minutes=reminder_min)
                        diff = (trigger_time - now).total_seconds()
                        
                        # LOGIC MỚI: Chỉ cần bé hơn hoặc bằng 0 là BÁO (Bắt hết các trường hợp lỡ giờ)
                        if diff <= 0: 
                            print(f"!!! BÁO ĐỘNG: {evt[1]} !!!")
                            
                            # 1. Phát tiếng kêu (Thử cả 2 kiểu)
                            try:
                                winsound.Beep(1000, 1000) # Kêu dài 1 giây
                            except:
                                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

                            # 2. Hiện Popup (Dùng after để thread an toàn)
                            self.root.after(0, lambda e=evt: messagebox.showwarning(
                                "🔔 NHẮC NHỞ", 
                                f"Đến giờ rồi: {e[1]}\nThời gian: {e[2]}"
                            ))
                            
                            # 3. Update DB ngay lập tức để không lặp lại
                            self.db.mark_as_notified(evt[0])
                            self.load_data()
                            
                    except ValueError as ve:
                        print(f"Lỗi dữ liệu dòng {evt[0]}: {ve}")
                        continue

            except Exception as e:
                print(f"Lỗi Thread: {e}")
            
            # Quét mỗi 5 giây
            time.sleep(5)