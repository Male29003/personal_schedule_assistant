import sqlite3
import datetime

DB_NAME = 'db/schedule.db'

class DBManager:
    def __init__(self, db_name=DB_NAME):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS note(
                id INTEGER primary key AUTOINCREMENT,
                event TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                reminder_minutes TEXT DEFAULT 15,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                status INTEGER DEFAULT 0
                )
        ''')
        self.connection.commit()
        print("Database initialized successfully!!!")

    def add_event(self, event, start_time, end_time=None, location=None, reminder_minutes=15, status=0):
        # Check if event already exists
        check_query = '''
            SELECT id FROM note 
            WHERE event = ? AND start_time = ? AND status != 1
        '''
        self.cursor.execute(check_query, (event, start_time))
        if self.cursor.fetchone():
            print(f"⚠️ Bỏ qua: Sự kiện '{event}' lúc {start_time} đã tồn tại!")
            return False
        try:
            self.cursor.execute('''
            INSERT INTO note (event, start_time, end_time, location, reminder_minutes, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (event, start_time, end_time, location, reminder_minutes, status))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding event: {e}")
            return False

    def get_upcoming_events(self):
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Select đúng thứ tự UI cần: ID, Event, StartTime, Location, Reminder
            query = """
                SELECT id, event, start_time, location, reminder_minutes 
                FROM note 
                WHERE status=0 AND start_time >= ? 
                ORDER BY start_time ASC
            """
            self.cursor.execute(query, (now, ))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching upcoming events: {e}")
            return []

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    db_manager = DBManager()
    sample_events = [
        {
            "event": "Họp đầu tuần",
            "start_time": "2025-12-01 09:00:00", # Đã qua
            "location": "Phòng 302",
            "reminder_minutes": 15,
            "status": 1 # Đã thông báo/xong
        },
        {
            "event": "Nộp báo cáo tiến độ",
            "start_time": "2025-12-04 14:00:00", # Đã qua
            "location": "Online Teams",
            "reminder_minutes": 30,
            "status": 1
        },

        # --- 8 SỰ KIỆN SẮP TỚI (Upcoming) ---
        {
            "event": "Đi xem phim với Crush",
            "start_time": "2025-12-05 20:00:00", # Tối nay
            "location": "CGV Vincom",
            "reminder_minutes": 60,
            "status": 0
        },
        {
            "event": "Chạy bộ sáng sớm",
            "start_time": "2025-12-06 05:30:00", # Sáng mai
            "location": "Công viên Tao Đàn",
            "status": 0
        },
        {
            "event": "Ăn tối gia đình",
            "start_time": "2025-12-06 19:00:00", # Tối mai
            "location": "Nhà hàng Biển Đông",
            "reminder_minutes": 30,
            "status": 0
        },
        {
            "event": "Review code dự án",
            "start_time": "2025-12-08 10:00:00", # Thứ 2 tuần sau
            "location": "Phòng Lab",
            "reminder_minutes": 15,
            "status": 0
        },
        {
            "event": "Hội thảo công nghệ AI",
            "start_time": "2025-12-10 08:00:00",
            "location": "Hội trường A",
            "reminder_minutes": 45,
            "status": 0
        },
        {
            "event": "Thi cuối kỳ môn Deep Learning",
            "start_time": "2025-12-15 09:00:00",
            "location": "Phòng thi 101",
            "reminder_minutes": 60,
            "status": 0
        },
        {
            "event": "Deadline nộp đồ án tốt nghiệp",
            "start_time": "2025-12-20 23:59:00",
            "location": "Cổng LMS",
            "reminder_minutes": 120,
            "status": 0
        },
        {
            "event": "Đi chơi Noel",
            "start_time": "2025-12-24 19:30:00",
            "location": "Nhà thờ Đức Bà",
            "reminder_minutes": 30,
            "status": 0
        }
    ]
    for e in  sample_events:
        db_manager.add_event(**e)

    test = db_manager.get_upcoming_events()
    for event in test:
        print(event)
