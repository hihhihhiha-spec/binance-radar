import time
import winsound  # يعمل على أنظمة Windows
from binance.client import Client

# Client = Client(api_key, api_secret)

def check_pattern(klines):
    if len(klines) < 4:
        return False

    c1, c2, c3 = klines[-4], klines[-3], klines[-2]

    open1, high1, low1, close1 = float(c1[1]), float(c1[2]), float(c1[3]), float(c1[4])
    open2, high2, low2, close2 = float(c2[1]), float(c2[2]), float(c2[3]), float(c2[4])
    open3, high3, low3, close3 = float(c3[1]), float(c3[2]), float(c3[3]), float(c3[4])

    # 1. شمعتان حمراوان
    is_red1 = close1 < open1
    is_red2 = close2 < open2
    
    # 2. كسر الذيل السفلي للشمعة الثانية
    broken_tail = low2 < low1
    
    # 3. جسم الشمعة الثانية أكبر من الذيول
    body2 = open2 - close2
    upper_wick2 = high2 - open2
    lower_wick2 = close2 - low2
    strong_body2 = body2 > (upper_wick2 + lower_wick2)

    # 4. الشمعة الثالثة: خضراء + داخل نطاق الثانية + تغلق عند/أعلى من منتصف جسم الثانية
    is_green3 = close3 > open3
    is_inside = (high3 <= high2) and (low3 >= low2)
    mid_body2 = close2 + (body2 / 2.0)
    closes_above_mid = close3 >= mid_body2

    return (is_red1 and is_red2 and broken_tail and strong_body2 and 
            is_green3 and is_inside and closes_above_mid)

def trigger_radar_sound():
    """تشغيل صوت صافرة التنبيه (3 نغمات متتالية)"""
    for _ in range(3):
        winsound.Beep(2000, 300)  # تردد 2000 هرتز لمدة 300 ميلي ثانية
        time.sleep(0.1)

# عند اكتشاف الفرصة في الحلقة التكرارية:
# if check_pattern(klines):
#     print(f"🎯 [صيد] تم إيجاد النموذج على الزوج: {symbol}")
#     trigger_radar_sound()
