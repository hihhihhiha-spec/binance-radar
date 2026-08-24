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
            print('\a', flush=True)  # صوت جرس الترمينال
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

# --- 2. إعدادات باينانس ---
exchange = ccxt.binance({'options': {'defaultType': 'future'}, 'enableRateLimit': True})

# --- 3. قائمة الأزواج ---
MY_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'LTC/USDT',
    'NEAR/USDT', 'MATIC/USDT', 'OP/USDT', 'ARB/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'TIA/USDT', 'SEI/USDT', 'SUI/USDT', 'APT/USDT', 'HBAR/USDT', 'ALGO/USDT', 'FIL/USDT', 'ICP/USDT', 'GRT/USDT', 'STX/USDT'
]

TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']

# ذاكرة لمنع تكرار التنبيه لنفس الشمعة
detected_signals = set()

def check_logic(symbol, tf):
    try:
        # جلب آخر 5 شمعات
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
        if len(bars) < 3: 
            return False
        
        # c1: الشمعة قبل الأخيرة المكتملة
        # c2: الشمعة الأخيرة المكتملة
        c1, c2 = bars[-3], bars[-2]
        
        o1, h1, l1, cl1, t1 = c1[1], c1[2], c1[3], c1[4], c1[0]
        o2, h2, l2, cl2, t2 = c2[1], c2[2], c2[3], c2[4], c2[0]

        # 1. الشمعتان حمراوان (إغلاق أقل من الافتتاح)
        is_red1 = cl1 < o1
        is_red2 = cl2 < o2

        if not (is_red1 and is_red2):
            return False

        # 2. كسر قاع الشمعة الأولى بواسطة قاع الشمعة الثانية
        broken_low = l2 < l1

        # 3. جسم الشمعة الثانية أكبر من الذيول العلوي والسفلي
        body2 = o2 - cl2
        upper_wick2 = h2 - o2
        lower_wick2 = cl2 - l2
        strong_body2 = body2 > (upper_wick2 + lower_wick2)

        # تحقق جميع الشروط
        if is_red1 and is_red2 and broken_low and strong_body2:
            signal_id = f"{symbol}_{tf}_{t2}"
            if signal_id not in detected_signals:
                detected_signals.add(signal_id)
                return True

        return False
    except Exception:
        return False

print(f"🚀 Radar Started: {len(MY_SYMBOLS)} symbols scanning...", flush=True)

while True:
    try:
        for index, symbol in enumerate(MY_SYMBOLS, 1):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ({index}/{len(MY_SYMBOLS)}) Scanning: {symbol}", flush=True)
            for tf in TIMEFRAMES:
                if check_logic(symbol, tf):
                    print(f"\n🎯 ALERT FOUND: {symbol} | Timeframe: {tf}\n", flush=True)
                    play_radar_sound()
            time.sleep(0.05)
            
        print("--- Cycle Finished. Restarting Now ---", flush=True)
        time.sleep(3)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(10)
