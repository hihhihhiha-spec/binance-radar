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

# --- 1. خادم منع التوقف ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar is Active")
    def log_message(self, format, *args): return

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_port_server, daemon=True).start()

# --- 2. إعدادات باينانس ---
exchange = ccxt.binance({'options': {'defaultType': 'future'}, 'enableRateLimit': True})

# --- 3. القائمة ---
MY_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'LTC/USDT',
    'NEAR/USDT', 'MATIC/USDT', 'OP/USDT', 'ARB/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'TIA/USDT', 'SEI/USDT', 'SUI/USDT', 'APT/USDT', 'HBAR/USDT', 'ALGO/USDT', 'FIL/USDT', 'ICP/USDT', 'GRT/USDT', 'STX/USDT',
    'INJ/USDT', 'RNDR/USDT', 'FET/USDT', 'AGIX/USDT', 'OCEAN/USDT', 'TAO/USDT', 'THETA/USDT', 'EGLD/USDT', 'AAVE/USDT', 'UNI/USDT'
]

TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']

def check_logic(symbol, tf):
    try:
        # جلب آخر 10 شمعات لضمان وفرة البيانات
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=10)
        if len(bars) < 3: return False
        
        # التركيز على آخر شمعتين مكتملتين (تجاهل الشمعة الحالية غير المكتملة bars[-1])
        c1, c2 = bars[-3], bars[-2]
        
        o1, h1, l1, cl1 = c1[1], c1[2], c1[3], c1[4]
        o2, h2, l2, cl2 = c2[1], c2[2], c2[3], c2[4]

        # 1. شمعتان حمراوان
        is_red1 = cl1 < o1
        is_red2 = cl2 < o2

        if not (is_red1 and is_red2):
            return False

        # 2. قياس الأجسام والذيول
        b1, b2 = abs(o1 - cl1), abs(o2 - cl2)
        total_range1 = h1 - l1
        total_range2 = h2 - l2

        # 3. شرط قوة الجسم: أن يشكل جسم الشمعة 50% على الأقل من طول الشمعة الكامل
        strong_body1 = (b1 / total_range1) >= 0.5 if total_range1 > 0 else False
        strong_body2 = (b2 / total_range2) >= 0.5 if total_range2 > 0 else False

        # 4. كسر قاع الشمعة الأولى بواستط الشمعة الثانية
        broken_low = l2 < l1

        if is_red1 and is_red2 and strong_body1 and strong_body2 and broken_low:
            return True

        return False
    except:
        return False

print(f"🚀 Radar Started: {len(MY_SYMBOLS)} symbols.", flush=True)

while True:
    try:
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ({index}/{len(MY_SYMBOLS)}) Scanning: {symbol}", flush=True)
            for tf in TIMEFRAMES:
                if check_logic(symbol, tf):
                    print(f"🎯 ALERT: {symbol} | TF: {tf}", flush=True)
                    play_radar_sound()
            time.sleep(0.05)
            
        print("--- Cycle Finished. Restarting Now ---", flush=True)
        time.sleep(5)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(10)
