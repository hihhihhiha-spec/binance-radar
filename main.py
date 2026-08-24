import sys
import os
import time
from binance.client import Client

# 1. إعداد الاتصال بـ Binance (لا يحتاج مفاتيح API للبيانات العامة)
client = Client()

def play_radar_sound():
    """تشغيل صوت التنبيه حسب نظام التشغيل المستعمل"""
    try:
        if sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(2500, 250)
                time.sleep(0.05)
        elif sys.platform == "darwin":
            os.system('say "Alert"')
        else:
            print('\a')  # تنبيه نظام Linux/Terminal
    except Exception:
        print("\a")  # جرس مجلد الأوامر الاحتياطي

def check_pattern(symbol, interval=Client.KLINE_INTERVAL_1HOUR):
    try:
        # جلب آخر 5 شمعات
        klines = client.get_klines(symbol=symbol, interval=interval, limit=5)
        if len(klines) < 4:
            return False

        # استخدام الشمعات المكتملة السابقة (تجنب الشمعة الحالية غير المكتملة)
        c1, c2, c3 = klines[-4], klines[-3], klines[-2]

        open1, high1, low1, close1 = float(c1[1]), float(c1[2]), float(c1[3]), float(c1[4])
        open2, high2, low2, close2 = float(c2[1]), float(c2[2]), float(c2[3]), float(c2[4])
        open3, high3, low3, close3 = float(c3[1]), float(c3[2]), float(c3[3]), float(c3[4])

        # الشمعة 1 و 2 حمراوان
        is_red1 = close1 < open1
        is_red2 = close2 < open2

        # كسر ذيل الشمعة الأولى
        broken_tail = low2 < low1

        # جسم الشمعة 2 أكبر من الذيول
        body2 = open2 - close2
        upper_wick2 = high2 - open2
        lower_wick2 = close2 - low2
        strong_body2 = body2 > (upper_wick2 + lower_wick2)

        # الشمعة 3: خضراء + داخل نطاق الشمعة 2 + إغلاق أعلى من منتصف جسم الشمعة 2
        is_green3 = close3 > open3
        is_inside = (high3 <= high2) and (low3 >= low2)
        mid_body2 = close2 + (body2 / 2.0)
        closes_above_mid = close3 >= mid_body2

        if is_red1 and is_red2 and broken_tail and strong_body2 and is_green3 and is_inside and closes_above_mid:
            return True

    except Exception as e:
        print(f"خطأ في جلب بيانات {symbol}: {e}")

    return False

# تجربة الرادار على زوج معين
symbol_to_check = "BTCUSDT"
print(f"جاري فحص الزوج {symbol_to_check}...")

if check_pattern(symbol_to_check):
    print("🎯 تم صيد النموذج!")
    play_radar_sound()
else:
    print("لم يتم العثور على النمط في الوقت الحالي.")
