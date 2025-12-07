# Personal Schedule Assistant
Personal Schedule Assistant là một công cụ hỗ trợ trích xuất thông tin lịch trình (sự kiện, thời gian, địa điểm) từ câu lệnh ngôn ngữ tự nhiên tiếng Việt. Dự án khởi đầu là một bài tập môn học và đang được phát triển để trở thành một trợ lý ảo hoàn chỉnh.

## Hướng dẫn cài đặt và chạy (Getting Started)

Vui lòng làm theo các bước dưới đây để thiết lập môi trường và chạy chương trình.

### Bước 1: Clone repository
Mở terminal (CMD hoặc PowerShell) và chạy lệnh sau để tải source code về máy:
```
bash
git clone [https://github.com/username/personal_schedule_assistant.git](https://github.com/username/personal_schedule_assistant.git)
cd personal_schedule_assistant
```

### Bước 2: Cài đặt môi trường ảo (Virtual Environment)
Tạo và kích hoạt môi trường ảo để đảm bảo không xung đột thư viện:
#### Đối với Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```
#### Đối với macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện
Cài đặt các thư viện cần thiết cho dự án:
```bash
pip install -r requirements.txt
```

### Bước 4: Chạy chương trình
Khởi chạy ứng dụng:
```bash
python main.py
```
