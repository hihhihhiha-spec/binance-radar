import ccxt
import time
import os
import sys
import threading
import urllib.request
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

# --- 2. نظام جلب وتغيير البروكسي (IP Rotator) ---
def fetch_free_proxies():
    """جلب قائمة بروكسيات مجانية نشطة"""
    print("🔄 جاري جلب قائمة بروكسيات جديدة لتغيير الـ IP...", flush=True)
    url = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            proxies = response.read().decode('utf-8').strip().split('\n')
            clean_proxies = [f"http://{p.strip()}" for p in proxies if p.strip()]
            print(f"✅ تم جلب {len(clean_proxies)} بروكسي محتمل.", flush=True)
            return clean_proxies
    except Exception as e:
        print(f"⚠️ فشل جلب البروكسيات: {e}", flush=True)
        return []

proxies_list = fetch_free_proxies()
proxy_index = 0

def create_exchange_instance(proxy_url=None):
    """إنشاء اتصال باينانس مع بروكسي جديد"""
    config = {
        'options': {'defaultType': 'future'},
        'enableRateLimit': True,
        'timeout': 10000
    }
    if proxy_url:
        config['proxies'] = {
            'http': proxy_url,
            'https': proxy_url
        }
    return ccxt.binance(config)

exchange = create_exchange_instance()

def rotate_proxy():
    """تغيير الـ IP عبر الانتقال للبروكسي التالي"""
    global exchange, proxy_index, proxies_list
    if not proxies_list:
        proxies_list = fetch_free_proxies()
        proxy_index = 0

    if proxies_list:
        current_proxy = proxies_list[proxy_index % len(proxies_list)]
        proxy_index += 1
        print(f"🔀 تغيير الـ IP إلى البروكسي الجديد: {current_proxy}", flush=True)
        exchange = create_exchange_instance(current_proxy)
    else:
        print("⚠️ استخدام الاتصال المباشر (بدون بروكسي)...", flush=True)
        exchange = create_exchange_instance()

# --- 3. جلب الأزواج والعملات ---
def get_active_symbols():
    global exchange
    for attempt in range(5):
        try:
            markets = exchange.load_markets()
            symbols = [symbol for symbol, data in markets.items() if symbol.endswith('/USDT') and data.get('active', True)]
            if symbols:
                print(f"✅ تم تحميل {len(symbols)} عملة نشطة بنجاح!", flush=True)
                return symbols
        except Exception as e:
            print(f"⚠️ فشل تحميل العملات (المحاولة {attempt+1}): {e}", flush=True)
            rotate_proxy()
            time.sleep(2)
    return []

TIMEFRAMES = ['1m', '5m', '15m']
detected_signals = set()

# --- 4. خوارزمية النمط الثلاثي ---
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

# --- 5. دالة الفحص الرئيسية ---
def scan_market(symbols):
    global exchange
    total = len(symbols)
    for index, symbol in enumerate(symbols, 1):
        if index % 25 == 0 or index == total:
            print(f"🔍 تقدم الفحص: [{index}/{total}] عملة...", flush=True)

        for tf in TIMEFRAMES:
            success = False
            for retries in range(2):
                try:
                    bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=4)
                    if not bars or len(bars) < 4:
                        break

                    c1, c2, c3 = bars[-4], bars[-3], bars[-2]
                    candle_time = c3[0]

                    if is_pattern_valid(c1, c2, c3):
                        signal_key = f"{symbol}_{tf}_{candle_time}"
                        if signal_key not in detected_signals:
                            detected_signals.add(signal_key)
                            print(f"\n🎯🎯🎯 [تم صيد نمط 3 شمعات] {symbol} | الفريم: {tf} 🎯🎯🎯\n", flush=True)
                            play_radar_sound()
                    success = True
                    break
                except ccxt.RateLimitExceeded:
                    print("⚠️ تجاوز حد الطلبات! جاري تغيير الـ IP...", flush=True)
                    rotate_proxy()
                    time.sleep(1)
                except Exception:
                    rotate_proxy()
                    time.sleep(0.5)

            time.sleep(0.05)

print("🚀 بدء تشغيل الرادار المحمي بنظام تغيير الـ IP الآلي...", flush=True)

symbols_list = []
while True:
    try:
        if not symbols_list:
            symbols_list = get_active_symbols()
            if not symbols_list:
                print("⏳ تعذر جلب القائمة، إعادة المحاولة بعد 10 ثوانٍ...", flush=True)
                time.sleep(10)
                continue

        start_time = time.time()
        scan_market(symbols_list)
        elapsed = round(time.time() - start_time, 1)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] اكتمل الفحص في {elapsed} ثانية. إراحة 5 ثوانٍ...", flush=True)
        time.sleep(5)

    except Exception as e:
        print(f"خطأ رئيسي: {e}", flush=True)
        rotate_proxy()
        time.sleep(5)
