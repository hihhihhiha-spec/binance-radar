import sys
import os
import time
from binance.client import Client

def trigger_radar_sound():
    """دالة تشغيل الصوت التلقائية المتوافقة مع جميع الأنظمة"""
    # 1. نظام ويندوز
    if sys.platform == "win32":
        import winsound
        for _ in range(3):
            winsound.Beep(2000, 300)
            time.sleep(0.1)
    # 2. نظام ماك (Mac)
    elif sys.platform == "darwin":
        os.system('say "Pattern Detected"')
    # 3. نظام لينكس (Linux)
    else:
        print('\a')  # إرسال نظام التنبيه الصوتي القياسي Terminal Bell

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
