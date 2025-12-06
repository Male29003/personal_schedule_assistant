import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class DateTimeParser:
    def __init__(self):
        self.date_keywords = {
            "hôm nay": 0, "nay": 0, "đêm nay": 0, "tối nay": 0, "bữa nay":0,
            "hom nay": 0, "dem nay": 0, "toi nay": 0,"bua nay":0,
            "chiều nay": 0, "trưa nay": 0, "sáng nay": 0,
            "chieu nay": 0, "trua nay": 0, "sang nay": 0,
            
            "ngày mai": 1, "mai": 1, "tối mai": 1,
            "chiều mai": 1, "trưa mai": 1, "sáng mai": 1,
            "ngay mai": 1, "mai": 1, "toi mai": 1,
            "chieu mai": 1, "trua mai": 1, "sang mai": 1,
            
            "ngày kia": 2, "mốt": 2, "tối mốt": 2,
            "chiều mốt": 2, "trưa mốt": 2, "sáng mốt": 2,
            "ngay kia": 2, "mot": 2, "toi mot": 2,
            "chieu mốt": 2, "trua mot": 2, "sang mot": 2,

            "tuần sau": 7, "tuần tới": 7, "tuan sau": 7, "tuan toi": 7,
            "tháng sau": 30, "tháng tới": 30, "thang sau": 30, "thang toi": 30,

            "cuối tuần": 0, "cuoi tuan": 0
        }
        self.weekday_keywords = {
            "thứ hai": 0, "thứ 2": 0, "t2": 0, "thu 2": 0,
            "thứ ba": 1, "thứ 3": 1, "t3": 1, "thu 3": 0,
            "thứ tư": 2, "thứ 4": 2, "t4": 2, "thu 4": 0,
            "thứ năm": 3, "thứ 5": 3, "t5": 3, "thu 5": 0,
            "thứ sáu": 4, "thứ 6": 4, "t6": 4, "thu 6": 0,
            "thứ bảy": 5, "thứ 7": 5, "t7": 5, "thu 7": 0,
            "chủ nhật": 6, "cn": 6
        }
        # Danh sách các giờ để lấy nếu thời gian nhập vào là tương đối
        self.hour_keywords = {
            "sáng": 8, "sang" :8,
            "chiều": 14, "chieu": 14,
            "trưa": 12, "trua": 12,
            "tối": 21, "toi": 21,
            "đêm": 22, "dem": 22,
            "khuya": 24, "nửa đêm": 24, "nua dem": 24
        }

    def get_keywords(self):
        keywords = list(self.date_keywords.keys()) + \
            list(self.weekday_keywords.keys()) + \
            list(self.hour_keywords.keys()) +\
                ["lúc", "luc", "vào", "vao", "hồi", "hoi", "sau", "nữa", "nua", "khoảng", "khoang", "tầm", "tam", "trong vòng", "trong vong", "tới", "toi"]
        return sorted(list(set(keywords)), key=len, reverse = True)

    def parse_relative_time(self, text):
        pattern = r"(sau|trong|tầm|tam|khoảng|khoang|trong vòng)?\s*(\d+)\s*(phút|p|phut|giờ|h|tiếng|tieng)\s*(nữa|nua|tới|sau|sau)?"
        match = re.search(pattern, text)
        
        if match:
            # Tách phần đầu và cuối
            prefix = match.group(1)
            suffix = match.group(4)

            val = int(match.group(2))
            unit = match.group(3)
            # Nếu cả hai phần đều không có nghĩa là ko phải thời gian tương đối
            if not prefix and not suffix:
                return None
            # Trả về thời gian tương đối
            delta_minutes = val
            if unit in ['giờ', 'gio', 'h', 'tieng', 'tiếng']:
                delta_minutes *= 60
            return datetime.now() + timedelta(minutes=delta_minutes)
        return None

    def parse(self, text):
        text = text.lower()
        today = datetime.now()
        target_date = today
        minute = 0
        hour = 0
        # Kiểm tra nếu ko có giờ cụ thể
        has_time = False
        # Kiểm tra nếu buổi chiều / tối
        is_pm = False 

        # Kiểm tra ngày tháng cụ thể với định dạng dd/mm
        found_date = False
        date_pattern = r"(\d{1,2})[/-](\d{1,2})"
        date_match = re.search(date_pattern, text)
        if date_match:
            try:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = today.year
                # Nếu tháng đã qua thì chuyển sang năm sau
                if month < today.month or (month == today.month and day < today.day):
                    year += 1
                target_date = datetime(year, month, day)
                found_date = True
            except: pass

        # Kiểm tra xem là buổi nào : am hay pm
        for kw, hr in self.hour_keywords.items():
            if kw in text:
                if not has_time:
                    hour = hr
                if hr >= 12: is_pm = True 

        # Kiểm tra giờ cụ thể
        time_pattern = r"(\d{1,2})[:h](\d{0,2})"
        time_match = re.search(time_pattern, text)
        if time_match:
            has_time = True
            # Tách giờ và phút ra
            temp_hour = int(time_match.group(1))
            if time_match.group(2):
                minute = int(time_match.group(2))
            if any(x in text for x in ["đêm", "dem", "khuya", "sáng", "sang"]):
                hour = temp_hour
            elif is_pm and temp_hour < 12:
                hour = temp_hour + 12   # Định dạng 24h
            else:
                hour = temp_hour       
        
        # Nếu ko có ngày cụ thể trong prompt thì kiểm tra có phải là thứ trong tuần
        found_date = False
        if not date_match:
            for key, days in self.date_keywords.items():
                if key in text:
                    if key in ["cuối tuần", "cuoi tuan"]:
                        days_ahead = (5 - today.weekday() + 7) % 7
                        target_date = today + timedelta(days=days_ahead)
                        found_date = True
                    else:
                        target_date = today + timedelta(days=days)
                        found_date = True
                    break
            if not found_date:
                for key, weekday_index in self.weekday_keywords.items():
                    if key in text:
                        days_ahead = (weekday_index - today.weekday() + 7) % 7
                        if days_ahead == 0:
                            # Nếu bị trùng thứ thì dời tgian qua tuần sau
                            check_time = today.replace(hour=hour, minute=minute)
                            if has_time and check_time < today:
                                    days_ahead = 7
                            elif not has_time: days_ahead = 7
                        target_date = today + timedelta(days=days_ahead)
                        found_date = True
                        break
        
        # Kết hợp các thông tin thời gian
        result = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # Nếu tgian đã qua mà ko có ngày cụ thể thì đẩy sang ngày hôm sau
        if(result < today) and not found_date and not date_match:
            result += timedelta(days=1)

        return result