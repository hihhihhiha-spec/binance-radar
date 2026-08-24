import ccxt
import time
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 0. دالة الصوت التنبيهي ---
def play_radar_sound():
    try:
        if sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(2000, 300)
                time.sleep(0.05)
        elif sys.platform == "darwin":
            os.system('say "Alert"')
        else:
            print('\a', flush=True)
    except Exception:
        print('\a', flush=True)

# --- 1. خادم منع التوقف السحابي ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar Active")
    def log_message(self, format, *args): return

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# --- 2. إعدادات باينانس المنهجية ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True, # تفعيل الحماية الداخلية
    'timeout': 20000
})

def get_active_symbols():
    """جلب الأزواج النشطة بطريقة آمنة"""
    try:
        markets = exchange.load_markets()
        symbols = [symbol for symbol, data in markets.items() if symbol.endswith('/USDT') and data.get('active', True)]
        print(f"✅ تم تحميل {len(symbols)} عملة نشطة من باينانس.", flush=True)
        return symbols
    except Exception as e:
        print(f"⚠️ يتعذر جلب القائمة الآلية الآن (قد يكون الـ IP محظوراً مؤقتاً). الانتظار قليلاً...", flush=True)
        return []

TIMEFRAMES = ['1m', '5m', '15m']
detected_signals = set()

def is_pattern_valid(c1, c2, c3):
    o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
    o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]
    o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]

    # 1. شمعتان حمراوان
    if not (cl1 < o1 and cl2 < o2):
        return False

    # 2. كسر القاع
    if not (l2 < l1):
        return False

    # 3. جسم الشمعة الثانية أكبر من الذيول
    body2 = o2 - cl2
    upper_wick2 = h2 - o2
    lower_wick2 = cl2 - l2
    if not (body2 > (upper_wick2 + lower_wick2)):
        return False

    # 4. الشمعة الثالثة خضراء + داخل نطاق الثانية + تغلق في/أعلى النصف
    is_green3 = cl3 > o3
    is_inside3 = (h3 <= h2) and (l3 >= l2)
    mid_body2 = cl2 + (body2 / 2.0)
    closes_above_mid3 = cl3 >= mid_body2

    return is_green3 and is_inside3 and closes_above_mid3

def scan_market(symbols):
    total = len(symbols)
    for index, symbol in enumerate(symbols, 1):
        if index % 25 == 0 or index == total:
            print(f"🔍 تقدم الفحص: [{index}/{total}] عملة...", flush=True)

        for tf in TIMEFRAMES:
            try:
                bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=4)
                if not bars or len(bars) < 4:
                    continue

                c1, c2, c3 = bars[-4], bars[-3], bars[-2]
                candle_time = c3[0]

                if is_pattern_valid(c1, c2, c3):
                    signal_key = f"{symbol}_{tf}_{candle_time}"
                    if signal_key not in detected_signals:
                        detected_signals.add(signal_key)
                        print(f"\n🎯🎯🎯 [تم صيد نمط 3 شمعات] {symbol} | الفريم: {tf} 🎯🎯🎯\n", flush=True)
                        play_radar_sound()

                # تأخير 0.1 ثانية لحماية حقيقية للـ IP
                time.sleep(0.1)

            except ccxt.RateLimitExceeded:
                print("⚠️ تحذير: اقتراب من حد الطلبات! إيقاف مؤقت لمدة 30 ثانية لتفادي Ban...", flush=True)
                time.sleep(30)
            except Exception:
                continue

print("🚀 بدء تشغيل الرادار الآمن...", flush=True)

symbols_list = []
while True:
    try:
        # إعادة جلب الأزواج إذا كانت القائمة فارغة
        if not symbols_list:
            symbols_list = get_active_symbols()
            if not symbols_list:
                time.sleep(60) # انتظر دقيقة إذا كان الـ IP محظوراً حالياً ليرفع الحظر
                continue

        start_time = time.time()
        scan_market(symbols_list)
        elapsed = round(time.time() - start_time, 1)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] اكتمل الفحص في {elapsed} ثانية. إراحة 10 ثوانٍ...", flush=True)
        time.sleep(10)

    except Exception as e:
        print(f"خطأ رئيسي: {e}", flush=True)
        time.sleep(15)
