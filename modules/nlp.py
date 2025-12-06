import sys
import os
import re
from underthesea import ner

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.datetime_parser import DateTimeParser

class NLPProcessor:
    def __init__(self):
        self.datetime_parser = DateTimeParser()
        # Lấy danh sách các từ khóa thời gian bên DateTimeParser
        self.time_keywords = self.datetime_parser.get_keywords()

    def analyze(self, raw_text):
        result = {
            "event": "",
            "start_time": "",
            "location": None,
            "reminder_minutes": 0
        }
#B1: Chuẩn hóa thành ký tự thường
        processing_text = raw_text.strip().lower()
        processing_text = re.sub(r"[,\.\-\?]", " ", processing_text)
        original_text = raw_text.strip()

#B2.1: Bóc thời gian nhắc nhở ra dòng text đã xử lý bên trên 
        kw_remind = r"nhắc|nhac|thông báo|thong báo|thong bao|tbao|thông bao"
        kw_me = r"tôi|toi|mình|minh|tớ|to"
        kw_pre = r"trước|truoc|trc|sớm hơn|som hơn|sớm hon|trước đó|truoc do|trc do|trc đó|sau"
        # Có 2 patterns để bóc dựa trên 2 TH:
        #   - 1: "...nhắc tôi trước 15 phút...", "...báo trước 1 tiếng..."
        #   - 2: "...15 phút sau...", "...1 tiếng trước khi ..."
        remind_pattern1 = rf"(?:^|\s)({kw_remind})\s*({kw_me})?\s*({kw_pre})*\s*(\d+)\s*(phút|phut|p|h|giờ|gio|ngay|ngày)?"
        remind_pattern2 = r"(\d+)\s*(phút|phut|p|giờ|h|giờ|gio)?\s*(trước|truoc|trc|sớm|som)\s*(khi|lúc|luc)?"
        
        val = 0
        unit = ""
        redundant_text = None

        remind_match1 = re.search(remind_pattern1, processing_text)
        if  remind_match1:
            val = int(remind_match1.group(4))
            unit = remind_match1.group(5)
            redundant_text = remind_match1.group(0)
        else:
            remind_match2 = re.search(remind_pattern2, processing_text)
            if remind_match2:
                val = int(remind_match2.group(1))
                unit = remind_match2.group(2)
                redundant_text = remind_match2.group(0)
        # Nếu tìm thấy thì gán giá trị reminder_minutes và loại bỏ phần text thừa
        if val > 0:
            if unit in ['giờ', 'gio', 'h']:
                val *= 60
            elif unit in ['ngày', 'ngay']:
                val *= 1440
            result["reminder_minutes"] = val
            # Loại bỏ phần nhắc nhở khỏi chuỗi xử lý
            processing_text = processing_text.replace(redundant_text, ' ')
        
#B2.2: Bóc thời gian bắt đầu - Trong TH thời gian tương đối VD "trong vòng 30p", "sau 1 tiếng"
        # Kiểm tra xem có tgian tương đối ko
        relative_time = self.datetime_parser.parse_relative_time(processing_text)
        final_time = None
        if relative_time:
            final_time = relative_time
            # Loại bỏ phần thời gian tương đối khỏi chuỗi xử lý
            processing_text = re.sub(r"(sau|trong|trong vòng|tầm|khoảng|khoang)?\s*\d+\s*(phút|phut|p|giờ|h|tiếng|tieng)\s*(nữa|nua|tới|toi|sau|sau)?", ' ', processing_text)

        # Nếu ko có thời gian tương đối thì lọc thời gian cụ thể
        if not final_time:
            temp_times = []
            # Dò giờ và ngày theo số trước
            num_pattern = [r"\d{1,2}[:h]\d{0,2}", r"\d{1,2}[/-]\d{1,2}"]
            for pattern in num_pattern:
                for t in re.findall(pattern, processing_text):
                    temp_times.append(t)
                    processing_text = processing_text.replace(t, " ")
            # Tiếp theo là dò theo từ khóa
            for tkw in self.time_keywords:
                if tkw in processing_text:
                    temp_times.append(tkw)
                    processing_text = re.sub(re.escape(tkw), " ", processing_text, 1)
            
            final_time = self.datetime_parser.parse(' '.join(temp_times))
        
        result["start_time"] = final_time.strftime("%Y-%m-%d %H:%M:%S")


#B3: Bóc địa điểm
        # Lọc các từ nối để bóc địa điểm chính xác hơn
        linking_words_location = "tại|ở|phòng|quán|nhà hàng|tiệm|sân|hồ|công viên|bến|trường|bệnh viện|siêu thị|o|phong|quan|nha hang|tiem|san|ho|cong vien|truong|benh vien|sieu thi"
        #location_pattern = rf"(tại|tai|ở|o|ỏ|ở̉|tại chỗ|tai cho|o cho|ở cho|trong|tren|phòng|phong|quán|quan|tiệm|tiem)\s+([\w\s,]+?)(?=\s+({linking_words_location})|$)"
        location_pattern = rf"(?:^|\s)({linking_words_location})\s+(.*?)(?=\s+(lúc|vào|nhắc|báo|trước|luc|vao|vao luc|vào lúc|nhac|trc|truoc)|$|[.,])"
        location_match = re.search(location_pattern, processing_text)
        # Dùng rule-based thử trước
        if location_match:
            location_string = location_match.group(1) + " " + location_match.group(2)
            result["location"] = location_string
            processing_text = processing_text.replace(location_match.group(0), ' ')
        else:
            # Nếu dùng rule-based ko được thì dùng NER của Underthesea để bóc địa điểm
            try:
                tokens = ner(processing_text)
                locations = [word for word, pos, tag in tokens if 'LOC' in tag]
                if locations:
                    result["location"] = ', '.join(locations)
                    for loc in locations:
                        processing_text = processing_text.replace(loc, ' ')
            except: pass

#B4: Lấy tên sự kiện
        # Lọc các từ nối để bóc tên sk chính xác hơn
        linking_words_title = ["lúc", "luc", "vào", "vao", "tại", "tai", "ở", "o", "với", "voi", "vs", "và", "va",
                "đến", "den", "của", "cua", "là", "la", "nhắc", "nhac", "tôi", "toi", "mình", "minh", "bạn", "ban",
                "nữa", "nua", "trong", "vòng", "vong", "tới", "toi", "chiều", "chieu", "sáng", "sang", "tối"]
        # Loại bỏ các dấu câu và khoảng trống thừa
        clean_title = re.sub(r"[,\.\-\?]", " ", processing_text).strip()

        # Lọc tiêu đề sự kiện bằng cách bỏ các từ nối
        title = [w for w in clean_title.split() if w not in linking_words_title]
        if title:
            result['event'] = " ".join(title).strip().capitalize()
        else:
            # Trong trường hợp đã tách hết các thông tin mà ko còn gì để làm tiêu đề
            # ==> kiểm tra các từ khóa phổ biến để gán tiêu đề mặc định
            title_expected = ["nhắc", "nhac", "nhắc nhở", "nhac nho", "nhắc tôi", "nhac toi", "báo", "bao", "báo thức", "bao thuc"]
            if any(kw in raw_text.lower() for kw in title_expected):
                result['event'] = "Nhắc nhở/ Báo thức"
            # ==> Nếu vẫn ko có thì lấy từ đầu câu làm tiêu đề
            else:
                if raw_text.strip():    
                    result['event'] = raw_text.split()[0]
                else:  
                    result['event'] = "Sự kiện mới"
        
        # Nếu ko có remider_minutes thì đặt mặc định là 15 phút
        if result["reminder_minutes"] == 0:
            result["reminder_minutes"] = 15
        return result

if __name__ == "__main__":
    nlp = NLPProcessor()
    
    # Test thử vài câu
    sentences = [
        "Họp team lúc 9h sáng mai",
        "di nhau quan oc dem nay",
        "Nộp báo cáo chiều t2",
        "Nhac nop bai sau 30p",
        "Đi bơi ở hồ Lam Sơn 5h chiều nay",
        "Nhắc tôi uống thuốc sau 1h nua",
        "Hẹn khách lúc 10:30 ngày kia",
        "Da bong san Chao Lua toi t7",
        "8h toi mai xem phim, nhac truoc 15p",
        "Bao thuc luc 6h sang mai",
        "Đi siêu thị trong vòng 20p tới",
        "Nhắc mình đi ngủ lúc 23h",
        "Hop phu huynh ngay 20/11",
        "Cafe vs Tung o Highland 9h",
        "Gui email cho sep sau 10 phut",
        "Nhắc tôi trước 30 phút",
        "Tam 2 tieng nua di don con",
        "Sinh nhat Lan toi cn",
        "Kiem tra tien do du an chieu mai",
        "15p nua goi cho me",
        "Di lay do o tiem giat ui sang mot",
        "Ăn trưa tại nhà hàng Biển Đông",
        "Chay bo cong vien Tao Dan 5h sang",
        "Nhắc nộp thuế trước 1 ngày",
        "Di Vung Tau cuoi tuan nay",
        "Xem chung ket C1 luc 2h dem",
        "Mua qua 8/3",
        "Hop khan sau 5p",
        "Bao cao tai chinh luc 14h",
        "Di chua don giao thua"
    ]
    
    print("-" * 50)
    for s in sentences:
        print(f"Input: {s}")
        print(f"Output: {nlp.analyze(s)}")