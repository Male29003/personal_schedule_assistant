# personal_schedule_assistant

Đây là dự án bài tập môn học nhằm xây dựng trợ lý ảo hỗ trợ trích xuất thông tin lịch trình từ ngôn ngữ tự nhiên (Tiếng Việt). Dự án hiện đang được tiếp tục phát triển và mở rộng tính năng để trở thành một phiên bản hoàn thiện hơn.

## Hướng dẫn cài đặt và chạy (Getting Started)

Vui lòng làm theo các bước dưới đây để thiết lập môi trường và chạy chương trình.

### Bước 1: Clone repository
Mở terminal (CMD hoặc PowerShell) và chạy lệnh sau để tải source code về máy:

bash
git clone [https://github.com/username/personal_schedule_assistant.git](https://github.com/username/personal_schedule_assistant.git)
cd personal_schedule_assistant

###Bước 2: Cài đặt môi trường ảo (Virtual Environment)
Tạo và kích hoạt môi trường ảo để đảm bảo không xung đột thư viện:

Đối với Windows:
Bash
python -m venv venv
.\venv\Scripts\activate

Đối với macOS / Linux:
Bash
python3 -m venv venv
source venv/bin/activate

###Bước 3: Cài đặt thư viện
Cài đặt các thư viện cần thiết cho dự án:
Bước 3: Cài đặt thư viện
Cài đặt các thư viện cần thiết cho dự án:
Bash
pip install -r requirements.txt

###Bước 4: Chạy chương trình
Khởi chạy ứng dụng:
Bash
python main.py
