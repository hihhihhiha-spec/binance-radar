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

# --- 2. إعدادات باينانس وشبك العقود الآجلة ---
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
    'timeout': 10000
})

print("🔄 جاري تحميل قائمة جميع أزواج العقود الآجلة المتاحة على باينانس...", flush=True)
try:
    markets = exchange.load_markets()
    # جلب جميع الأزواج الشغالة المقترنة بـ USDT
    MY_SYMBOLS = [symbol for symbol, data in markets.items() if symbol.endswith('/USDT') and data.get('active', True)]
    print(f"✅ تم تحميل {len(MY_SYMBOLS)} عملة شغالين ونشطين بنجاح!", flush=True)
except Exception as e:
    print(f"⚠️ فشل الجلب الآلي، استخدام القائمة الاحتياطية: {e}", flush=True)
    MY_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'PEPE/USDT', 'WIF/USDT']

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

def scan_market():
    total = len(MY_SYMBOLS)
    for index, symbol in enumerate(MY_SYMBOLS, 1):
        # طباعة حالة الفحص المستمرة لتأكيد العمل
        if index % 20 == 0 or index == total:
            print(f"🔍 جاري فحص: [{index}/{total}] عملة...", flush=True)

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

                time.sleep(0.02)
            except Exception:
                continue

print("🚀 بدأ الرادار الفحص المباشر والسريع...", flush=True)

while True:
    try:
        start_time = time.time()
        scan_market()
        elapsed = round(time.time() - start_time, 1)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] اكتمل فحص {len(MY_SYMBOLS)} عملة في {elapsed} ثانية. إعادة...", flush=True)
        time.sleep(2)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(5)
